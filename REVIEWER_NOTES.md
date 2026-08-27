# Reviewer Notes

## Review target

The submission target is `contracts/agent_escrow.py`. It is one standalone GenLayer Intelligent Contract, not an application.

## Constructor order

```text
provider: str
specification: str
rubric_json: str
evidence_policy_json: str
delivery_deadline: u64
review_period: u64
undetermined_fallback: str
adjudication_period: u64
```

A valid payload is in `examples/deploy_args.json`.

## Public surface

Six views:

- `get_state`
- `get_agreement`
- `get_audit_log`
- `get_delivery`
- `get_settlement`
- `get_resolution`

Ten writes:

- `fund`
- `submit_delivery`
- `open_dispute`
- `accept_delivery`
- `propose_settlement`
- `confirm_settlement`
- `claim_delivery_timeout`
- `claim_review_timeout`
- `claim_dispute_timeout`
- `resolve_dispute`

## Suggested review order

1. Constructor validation and immutable terms.
2. State guards and actor authorization.
3. `_settle` accounting and transfer order.
4. Evidence manifest validation and public URL restrictions.
5. `_validate_resolution` arithmetic and evidence-reference checks.
6. Leader/validator independent retrieval, hashing, and material equivalence.
7. `UNDETERMINED` and dispute-timeout fallback behavior.
8. Tests, schemas, and documented limits.

## Reproducible checks

```bash
.venv/bin/python -m pytest tests/direct tests/test_artifacts.py -q
.venv/bin/genvm-lint check contracts/agent_escrow.py
.venv/bin/python -m pytest tests/integration --collect-only -q
```

The direct suite covers configuration, lifecycle, settlement, dispute consensus, prompt injection, URL integrity, URL target restrictions, timeout liveness, terminal-state immutability, authorization, and payout conservation across boundary amounts and basis points.

Expected verified collection: 90 direct/artifact tests and one integration test.

## Integration caveat

The contract pins the GenLayer runner that exposes `gl.evm.contract_interface`, used for finalized EOA payouts. An older local simulator image that bundles only the v0.2 SDK cannot execute that interface. The integration test remains present and collectable; execute it on a current Studio/localnet image with the pinned runner rather than downgrading the contract’s settlement path.
