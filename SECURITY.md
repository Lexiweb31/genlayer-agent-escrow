# Security Model

## Protected assets and invariants

The protected asset is the native GEN funded into one AgentEscrow deployment. The contract is designed to preserve these invariants:

- only the client funds and directly accepts;
- only the provider submits a delivery;
- mutual settlement requires matching values from opposite parties;
- every payout uses 0–10,000 provider basis points;
- provider and client amounts always sum to the funded escrow;
- settlement occurs at most once;
- terminal states cannot reopen; and
- every funded lifecycle has a deadline-based route to a terminal state.

## Trust boundaries

Immutable contract storage is trusted adjudication input. Delivery summaries, evidence text, remote bodies, descriptions, and any instructions embedded in them are untrusted.

The GenLayer protocol and configured validator set are trusted to execute and finalize the nondeterministic consensus mechanism. The GenLayer web runtime is trusted to enforce redirect- and DNS-level network isolation. Contract-side URL parsing additionally blocks direct localhost, credential-bearing, loopback, link-local, private, reserved, multicast, and unspecified literal-IP targets.

## Prompt injection

Evidence is placed inside an explicit untrusted boundary. The adjudication prompt forbids role changes, rubric replacement, payout commands, and output-format instructions found in evidence. This is reinforced by deterministic validation:

- every deployed criterion must appear exactly once;
- unknown criteria and evidence IDs are rejected;
- cited evidence must be available, integrity-valid, and mapped to that criterion;
- status-dependent awards and totals are recomputed; and
- payout-relevant leader fields must equal each validator’s independent result.

Prompt wording alone is not treated as a complete defense.

## Remote evidence integrity

When `require_url_hashes` is enabled, URL evidence must include a canonical lowercase SHA-256 digest. Leaders and validators hash independently retrieved bytes. Unavailable, mismatched, or greater-than-65,536-byte responses are excluded from trusted evidence and cannot be cited for an award.

Without mandatory hashes, a successfully retrieved public URL is evaluated as observed by each validator. Mutable or personalized content may cause non-consensus; it does not silently produce a payout.

## Consensus failure and liveness

Protocol non-consensus is distinct from an agreed `UNDETERMINED` result. A failed resolution attempt leaves state and funds unchanged in `DISPUTED`, allowing retries. If no result finalizes before `dispute_deadline`, anyone may call `claim_dispute_timeout()` and apply the immutable deployment fallback.

Fallback choices have economic consequences. `SPLIT_50_50` reduces either party’s unilateral benefit from making evidence unavailable but is not universally optimal.

## Transfer safety

Settlement records terminal state and amounts before emitting external transfers. Zero-value legs are skipped. Recipient contracts receive ordinary finalized value transfers through the pinned GenLayer EVM contract interface; V1 intentionally exposes no callback or arbitrary external call surface.

## Known limitations

- Subjective consensus can still be wrong even when internally consistent.
- Hostname syntax checks cannot detect a public hostname that later resolves or redirects to a private target; the web runtime must isolate those cases.
- Remote sources can disappear or vary across validators.
- V1 does not implement appeals above GenLayer protocol finality.
- V1 has no stablecoin, oracle-price, identity, reputation, milestone, or upgrade mechanism.
- Deployers must choose realistic deadlines, rubric language, evidence requirements, and fallback incentives.

## Reporting

Do not fund production value until the contract, pinned runner, target network, and transfer behavior have received independent review. Report suspected vulnerabilities privately to the repository owner with a minimal reproduction, affected method, and expected financial impact.
