# GenLayer Intelligent Contract Contribution

## Submission

**AgentEscrow** is a standalone, reusable Intelligent Contract for agent-to-agent and agent-to-human commerce involving subjective digital deliverables. It locks native GEN against immutable natural-language terms, freezes bounded evidence, supports cooperative settlement, and uses GenLayer validator consensus when the parties disagree.

This contribution intentionally contains no frontend, backend, marketplace, agent registry, or product flow. The primitive is designed to be deployed once per commitment and composed by other protocols.

## Problem solved

Ordinary smart contracts can enforce amounts and timestamps but cannot reliably judge whether a report, dataset, design, research task, or other agent-produced artifact satisfies an ambiguous written specification. Happy-path payment protocols do not settle disputes about quality, evidence, SLA meaning, or partial completion.

AgentEscrow separates the problem into:

1. deterministic custody, authorization, deadlines, and payout arithmetic;
2. immutable specification, rubric, evidence policy, and fallback terms;
3. nondeterministic evidence retrieval and criterion-level evaluation; and
4. validator equivalence over payout-relevant structured fields.

## Why GenLayer consensus matters

The leader and validators independently retrieve permitted URL evidence and evaluate the same frozen agreement. Both outputs must satisfy deterministic schema, rubric arithmetic, evidence-reference, mapping, availability, and hash-integrity rules. Consensus compares outcome, evidence sufficiency, criterion status, criterion award, and total provider basis points. Explanatory prose is non-material.

This is not a thin “AI decides” wrapper: malformed model output cannot settle, evidence-borne instructions are untrusted, and a result changes state only after GenLayer accepts the nondeterministic operation.

## Reusable capabilities

- Native-GEN escrow with one-time funding.
- Natural-language specification and weighted 10,000-basis-point rubric.
- Bounded `TEXT` and public HTTP(S) evidence manifests.
- Optional mandatory SHA-256 verification of retrieved URL bytes.
- Direct acceptance and mutually confirmed splits.
- Independent AI-validator dispute resolution.
- Precommitted handling of agreed insufficient evidence.
- Permissionless liveness fallback after an immutable dispute deadline.
- Canonical agreement, delivery, settlement, resolution, and audit views.

## Repository contents

- `contracts/agent_escrow.py` — the standalone Intelligent Contract.
- `tests/direct/` — lifecycle, settlement, consensus, adversarial, and invariant tests.
- `tests/integration/` — localnet deployment/funding/submission/acceptance flow.
- `schemas/` — public JSON schemas for every JSON boundary.
- `examples/deploy_args.json` — complete ordered constructor arguments.
- `SECURITY.md` — threat model and explicit trust boundaries.
- `REVIEWER_NOTES.md` — compact review and verification guide.

## Verification

```bash
.venv/bin/python -m pytest tests/direct tests/test_artifacts.py -q
.venv/bin/genvm-lint check contracts/agent_escrow.py
.venv/bin/python -m pytest tests/integration --collect-only -q
```

Full integration execution requires a Studio/localnet image containing the contract’s pinned GenLayer runner and `gl.evm.contract_interface`. The direct suite validates contract behavior without weakening finalized transfer semantics for an older simulator.

## V1 boundary

V1 supports one client, one provider, one milestone, native GEN, and digital evidence. Stablecoins, identity/reputation, appeals above GenLayer finality, physical-task verification, registries, and application UI are deliberately left to composable higher layers.
