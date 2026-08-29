# AgentEscrow Submission Summary

AgentEscrow is a standalone GenLayer Intelligent Contract for native-GEN escrow and AI-validator dispute resolution over ambiguous digital deliverables. It intentionally contains no application frontend, backend, marketplace, or registry.

## Included

- Standalone 16-method Intelligent Contract.
- Deterministic funding, deadlines, cooperative settlement, and payout conservation.
- Natural-language rubric adjudication through independent leader/validator evaluation.
- Prompt-injection isolation and strict structured-output validation.
- Public URL restrictions, SHA-256 byte verification, evidence-to-criterion mapping, and response-size bounds.
- Permissionless dispute-timeout liveness using a deployment-fixed fallback.
- Four public JSON schemas and a complete deployment-argument example.
- Contribution narrative, threat model, reviewer guide, implementation plan, and reconciled design specification.

## Verification result

- 93 direct and artifact tests collected and passed.
- GenVM lint passed all three checks.
- GenVM contract validation passed: 16 methods (6 view, 10 write).
- One localnet integration test collected successfully.
- All public JSON artifacts parsed successfully.

## Bradbury proof

- Reviewer-corrected contract: `0x32e2Fbf6474fA397589B3e51cdCfd0a3C113B444`
- Corrected deployment transaction: `0x78dc8e084ea77f9f8a1b8feb22255c6e7a10a39d1beeda367ba6351e5ddac5d6`
- Corrections: positive criteria require mapped trusted citations; retrieved
  URL bodies are explicitly untrusted in both consensus prompts.

- Contract: `0x91F9ce165F7ab737D3920732679C24bBa9322EDd`
- Deployment transaction: `0x0e6836c0f96238e522f0f64ca89b123a03ab2abe5bd57b0a4acb6b970b4a9148`
- Provider delivery transaction: `0x797a999f8e0712cc0f71856b07b17dac1cc938b985604c5a4770883fcd1aecef`
- Client acceptance transaction: `0x8127e3342e3b5e69c70fec8ae20606c9e972a74936f70dc1097830750001eef6`
- Final state: `ACCEPTED`; settlement records 0.02 GEN and 10,000 provider basis points.

The corrected disputed-flow deployment and its still-pending AI-jury
transaction are documented in `docs/BRADBURY_DISPUTE_PROOF.md`; this package
does not claim that pending adjudication as complete.

Full localnet execution requires a current Studio/localnet image containing the contract's pinned runner and `gl.evm.contract_interface`. This compatibility constraint is documented without downgrading finalized payout behavior.
