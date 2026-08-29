# Agent Escrow Intelligent Contract

A standalone GenLayer Intelligent Contract for native-GEN escrow when a digital deliverable must be judged against natural-language requirements. This repository intentionally contains no frontend, backend, marketplace, or application flow.

## Why it exists

Deterministic contracts can enforce payments and deadlines, but cannot reliably determine whether an ambiguous report, design, dataset, or agent-produced artifact satisfies a written brief. `AgentEscrow` freezes the agreement and evidence, then uses GenLayer validators to independently evaluate the same rubric before releasing funds.

## Lifecycle

```text
CREATED -> FUNDED -> SUBMITTED -> ACCEPTED
                      |    |-> SETTLED
                      |    -> DISPUTED -> RESOLVED
                      -> REFUNDED
FUNDED ----------------------------> REFUNDED
```

One deployment represents one client/provider agreement. The deployer is the client. Terms are immutable after deployment; `fund()` activates the escrow once with native GEN.

Constructor arguments are ordered as follows:

```text
provider, specification, rubric_json, evidence_policy_json,
delivery_deadline, review_period, undetermined_fallback, adjudication_period
```

See [`examples/deploy_args.json`](examples/deploy_args.json) for a complete deployment payload.

The GenLayer CLI automatically decodes arguments beginning with `[` or `{`. For CLI deployment, pass the rubric and evidence policy as native JSON array/object arguments; the constructor normalizes both those values and serialized JSON strings used by SDK integrations.

## Contract interface

- `fund()` — client-only payable activation.
- `submit_delivery(summary, evidence_json)` — provider-only, one-time evidence freeze.
- `accept_delivery()` — client releases 100% to the provider.
- `propose_settlement(provider_bps)` / `confirm_settlement(provider_bps)` — matching two-party split.
- `open_dispute()` — either party opens adjudication during review.
- `resolve_dispute()` — runs independent leader/validator evaluation and settles the agreed result.
- `claim_delivery_timeout()` — client refund after missed delivery.
- `claim_review_timeout()` — provider payment after unanswered review.
- `claim_dispute_timeout()` — permissionless fallback settlement after the immutable adjudication period expires.
- `get_agreement()`, `get_delivery()`, `get_resolution()`, `get_settlement()`, `get_state()`, `get_audit_log()` — read-only inspection.

## Rubric input

Rubric weights must be positive and total exactly 10,000 basis points.

```json
[
  {"id":1,"requirement":"Return a sourced report","weight_bps":6000,"evidence_guidance":"Cite URLs"},
  {"id":2,"requirement":"Include an executive summary","weight_bps":4000,"evidence_guidance":"Use submitted text"}
]
```

Evidence is a bounded JSON manifest of `TEXT` and public HTTP(S) `URL` items. Loopback, link-local, private literal-IP, localhost, and credential-bearing targets are rejected. IDs are unique and each item names the rubric criteria it supports. A policy may require canonical SHA-256 hashes for URL content. Submitted evidence is explicitly delimited as untrusted data; embedded commands cannot modify the trusted specification, rubric, output schema, or payout rules.

## Public JSON schemas

- [`schemas/rubric.schema.json`](schemas/rubric.schema.json)
- [`schemas/evidence-policy.schema.json`](schemas/evidence-policy.schema.json)
- [`schemas/evidence-manifest.schema.json`](schemas/evidence-manifest.schema.json)
- [`schemas/resolution.schema.json`](schemas/resolution.schema.json)

The schemas describe structural constraints. Rubric-weight totals, unique criterion IDs, criterion/evidence references, status-dependent awards, and payout arithmetic are additionally enforced by contract code because they depend on other submitted or deployed values.

## Consensus design

`resolve_dispute()` copies frozen storage into memory before entering `gl.vm.run_nondet_unsafe`.

1. The leader retrieves URL evidence, computes its SHA-256 digest, and produces a criterion-level JSON decision.
2. Every validator independently retrieves, hashes, and evaluates the same evidence.
3. Both outputs must pass deterministic schema, evidence-mapping, integrity, and arithmetic checks. Unavailable or hash-mismatched URLs cannot be cited for an award.
4. Validators require exact agreement on outcome, evidence sufficiency, every criterion status and award, and total provider basis points.
5. Explanatory summaries may differ.
6. Only an accepted result changes state and emits finalized GEN transfers.

This is substantive validation, not a format-only check. A protocol-level validator disagreement initially leaves the contract disputed and funded so adjudication can be retried. If no result finalizes before the immutable dispute deadline, anyone may call `claim_dispute_timeout()` and apply the deployment-selected fallback. `UNDETERMINED` is an agreed finding that evidence is insufficient and applies the same fallback (`REFUND_CLIENT`, `PAY_PROVIDER`, or `SPLIT_50_50`).

## Settlement safety

Payout uses integer basis points:

```text
provider_amount = floor(escrow_amount * provider_bps / 10_000)
client_amount   = escrow_amount - provider_amount
```

State and settlement fields are written before external messages. Transfers are emitted at finality, zero-value legs are skipped, and terminal methods cannot execute twice.

## Limits and assumptions

- Specification: 8,192 UTF-8 bytes.
- Rubric: 1–8 criteria.
- Delivery summary: 2,048 UTF-8 bytes.
- Evidence: 1–12 items, at most 32,768 aggregate serialized bytes.
- Retrieved URL body: at most 65,536 bytes; larger responses cannot support an award and are not placed in the adjudication prompt.
- Review and adjudication periods: 1–2,592,000 seconds each.
- Live URLs may change, disappear, personalize content, or differ between validators.
- Host syntax checks reject direct private-network targets; the GenLayer web runtime remains responsible for redirect and DNS-level network isolation.
- When URL hashes are required, retrieved bytes must match the submitted SHA-256 digest before that evidence can support an award.
- Prompt isolation and consensus reduce model manipulation; they do not make subjective decisions objectively infallible.
- V1 supports one milestone, one provider, and native GEN only.

## Verification

Requires Python 3.12+.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests/direct/ -v
.venv/bin/python -m pytest tests/test_artifacts.py -v
.venv/bin/genvm-lint check contracts/agent_escrow.py
```

Studio integration requires a running GenLayer Studio/localnet and is intentionally reported separately from direct-mode verification.

The current contract uses the SDK runner that provides `gl.evm.contract_interface` for finalized EOA payouts. A localnet image must bundle that exact runner pin (or be able to retrieve it). Older simulator images that bundle only the v0.2 SDK cannot execute this payout interface; use a current Studio/localnet image rather than downgrading the contract's settlement guarantees.

## Bradbury testnet proof

The reviewer-corrected source is deployed on Bradbury at
`0x32e2Fbf6474fA397589B3e51cdCfd0a3C113B444` (deployment transaction
`0x78dc8e084ea77f9f8a1b8feb22255c6e7a10a39d1beeda367ba6351e5ddac5d6`).
This version requires mapped trusted citations for every `PASS` or `PARTIAL`
criterion and encloses retrieved URL bodies in explicit untrusted-data
boundaries in both leader and validator prompts.

A complete cooperative escrow lifecycle was exercised on Bradbury using contract
`0x91F9ce165F7ab737D3920732679C24bBa9322EDd`:

- Deployment: `0x0e6836c0f96238e522f0f64ca89b123a03ab2abe5bd57b0a4acb6b970b4a9148`
- Provider delivery: `0x797a999f8e0712cc0f71856b07b17dac1cc938b985604c5a4770883fcd1aecef`
- Client acceptance: `0x8127e3342e3b5e69c70fec8ae20606c9e972a74936f70dc1097830750001eef6`

The final contract state is `ACCEPTED`; `get_settlement()` records 10,000 provider
basis points, 0.02 GEN to the provider, zero to the client, and `settled: true`.

A separate disputed-flow exercise uncovered and fixed a GenVM storage-capture
regression. The corrected deployment, confirmed lifecycle transactions, pending
AI-jury transaction, and recovery details are recorded in
[`docs/BRADBURY_DISPUTE_PROOF.md`](docs/BRADBURY_DISPUTE_PROOF.md). Pending
consensus is explicitly not represented as a completed adjudication.

## Reuse

Another protocol can deploy one `AgentEscrow` per commitment, pass its own human- or agent-authored specification and rubric, and observe canonical views plus lifecycle records. No application-specific registry is required.

## Submission documents

- [`CONTRIBUTION.md`](CONTRIBUTION.md) — contribution narrative and category fit.
- [`SECURITY.md`](SECURITY.md) — threat model, controls, and known limitations.
- [`REVIEWER_NOTES.md`](REVIEWER_NOTES.md) — public surface and reproducible review checklist.
