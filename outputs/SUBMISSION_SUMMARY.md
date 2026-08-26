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

- 87 direct and artifact tests collected and passed.
- GenVM lint passed all three checks.
- GenVM contract validation passed: 16 methods (6 view, 10 write).
- One localnet integration test collected successfully.
- All public JSON artifacts parsed successfully.

Full localnet execution requires a current Studio/localnet image containing the contract's pinned runner and `gl.evm.contract_interface`. This compatibility constraint is documented without downgrading finalized payout behavior.
