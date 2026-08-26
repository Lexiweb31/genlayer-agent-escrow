# Agent Escrow Submission Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze AgentEscrow V1 and make its financial invariants, prompt-injection resistance, public input schemas, deployment flow, and contribution-review package complete and reproducible.

**Architecture:** Keep the standalone Intelligent Contract unchanged unless a failing invariant or adversarial test exposes a defect. Add deterministic direct-mode tests around the existing public interface, publish machine-readable JSON Schemas for every JSON boundary, and assemble reviewer documentation without introducing an app, frontend, backend, or registry.

**Tech Stack:** Python 3.12, GenLayer Intelligent Contracts, genlayer-test 0.29.2, pytest 8.4.2, JSON Schema Draft 2020-12 documentation.

**Spec:** `docs/superpowers/specs/2026-08-25-agent-escrow-design.md`

## Global Constraints

- Deliver only a standalone GenLayer Intelligent Contract and its tests/documentation.
- Preserve native-GEN settlement and the existing 16-method public interface.
- Preserve payout conservation: provider amount plus client amount equals escrow amount.
- Do not add runtime dependencies unless the existing parameterized-test approach cannot express an invariant.
- Run `.venv/bin/python -m pytest tests/direct -q` and `.venv/bin/genvm-lint check contracts/agent_escrow.py` before completion.

---

### Task 1: Financial and lifecycle invariant matrix

**Files:**
- Create: `tests/direct/test_invariants.py`
- Modify only if a regression fails: `contracts/agent_escrow.py`

**Interfaces:**
- Consumes: `valid_terms(provider)`, `submit_delivery(summary, manifest)`, settlement methods, and canonical state/settlement views.
- Produces: parameterized invariant tests over funding amounts, basis-point splits, terminal transitions, unauthorized callers, and timeout paths.

- [ ] **Step 1: Write parameterized conservation tests**

Cover amounts `[1, 2, 3, 10, 101, 10**6, 2**64 - 1]` and basis points `[0, 1, 3333, 5000, 9999, 10000]`. For every accepted mutual settlement, assert:
```python
assert settlement["provider_amount"] + settlement["client_amount"] == amount
assert settlement["provider_amount"] == amount * provider_bps // 10_000
```

- [ ] **Step 2: Write terminal-state and authorization matrix tests**

After each terminal method, call all write methods that could settle or reopen the escrow and assert they revert on state. Exercise client, provider, and unrelated caller against privileged methods.

- [ ] **Step 3: Run the new tests**

Run: `.venv/bin/python -m pytest tests/direct/test_invariants.py -q`
Expected: PASS, or a focused FAIL identifying a contract invariant defect.

- [ ] **Step 4: Fix only proven defects and rerun**

Use the smallest contract change that restores the stated invariant, then rerun the focused file.

### Task 2: Adversarial prompt-injection fixtures

**Files:**
- Modify: `tests/fixtures/adjudication_cases.py`
- Modify: `tests/direct/test_resolution.py`

**Interfaces:**
- Consumes: the frozen trusted agreement, untrusted evidence delimiter, deterministic resolution validator, and direct LLM/web mocks.
- Produces: regression cases showing evidence-borne instructions cannot change schema, rubric IDs, payout arithmetic, evidence mappings, or consensus material.

- [ ] **Step 1: Add hostile TEXT and URL-body fixtures**

Include role-change text, rubric replacement, forced full-payout JSON, markdown-fence output instructions, and duplicated/unknown criterion IDs.

- [ ] **Step 2: Add rejection and consensus tests**

Mock hostile evidence separately from the adjudicator response. Assert valid rubric-bound output settles normally, while injected malformed output reverts or fails validator equivalence.

- [ ] **Step 3: Run the adversarial tests**

Run: `.venv/bin/python -m pytest tests/direct/test_resolution.py -q`
Expected: PASS.

### Task 3: Public schemas and deployment example

**Files:**
- Create: `schemas/rubric.schema.json`
- Create: `schemas/evidence-policy.schema.json`
- Create: `schemas/evidence-manifest.schema.json`
- Create: `schemas/resolution.schema.json`
- Create: `examples/deploy_args.json`
- Create: `tests/test_artifacts.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: exact constructor fields and JSON rules enforced in `contracts/agent_escrow.py`.
- Produces: Draft 2020-12 schemas, one complete ordered constructor-argument example, and tests that load every artifact and validate internal totals/references.

- [ ] **Step 1: Write machine-readable schemas**

Encode exact limits, enums, required keys, uniqueness, URL scheme, SHA-256 pattern, criterion ranges, and resolution field shapes. Document cross-field arithmetic as schema descriptions where JSON Schema cannot enforce it.

- [ ] **Step 2: Write the deployment example**

Provide all eight ordered constructor arguments, including `adjudication_period`, with a rubric totaling 10,000 basis points and matching evidence policy.

- [ ] **Step 3: Add artifact integrity tests**

Load every JSON file, assert Draft 2020-12 metadata, verify the example argument count and rubric total, and verify referenced schema files exist.

- [ ] **Step 4: Document usage**

Add constructor order, schema links, and direct deployment/test commands to the README.

### Task 4: Contribution-review package

**Files:**
- Create: `CONTRIBUTION.md`
- Create: `SECURITY.md`
- Create: `REVIEWER_NOTES.md`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-08-25-agent-escrow-design.md`

**Interfaces:**
- Consumes: verified contract behavior, schemas, tests, known localnet SDK limitation, and contribution-category requirements.
- Produces: a concise submission narrative, threat model/security boundary, reviewer checklist, repository map, and reproducible verification instructions.

- [ ] **Step 1: Write contribution narrative**

Explain the primitive, why GenLayer consensus is necessary, consensus material, reusable interface, and why the repository is intentionally not an app.

- [ ] **Step 2: Write security boundary**

Cover prompt injection, evidence integrity, URL isolation limits, consensus disagreement, timeouts, payout conservation, EVM transfer assumptions, and explicitly excluded V1 capabilities.

- [ ] **Step 3: Write reviewer notes**

List exact files, 16 public methods, constructor order, test commands, expected counts, and the simulator/runner compatibility caveat.

- [ ] **Step 4: Reconcile the original design spec**

Update lifecycle, constructor, evidence integrity, and dispute-timeout sections to match the implemented contract.

- [ ] **Step 5: Verify the complete package**

Run:
```bash
.venv/bin/python -m pytest tests/direct tests/test_artifacts.py -q
.venv/bin/genvm-lint check contracts/agent_escrow.py
.venv/bin/python -m pytest tests/integration --collect-only -q
```
Expected: all direct/artifact tests pass, lint and contract validation pass, and one integration test collects.
