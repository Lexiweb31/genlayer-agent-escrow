import json
import hashlib
import inspect
import pytest

from test_configuration import valid_terms
from test_lifecycle import manifest
from tests.fixtures.adjudication_cases import (
    DIFFERENT_AWARD,
    HOSTILE_TEXT_EVIDENCE,
    HOSTILE_URL_BODY,
    INJECTED_PAYOUT,
    INJECTED_UNKNOWN_CRITERION,
    PARTIAL,
    PARTIAL_DIFFERENT_SUMMARY,
    UNDETERMINED,
)


def disputed(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))
    direct_vm.sender = direct_owner
    direct_vm.value = 100
    escrow.fund()
    direct_vm.value = 0
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", manifest())
    escrow.open_dispute()
    direct_vm.mock_web("example.com", {"status": 200, "body": "retrieved source"})
    return escrow


def test_consensus_resolution_settles_partial_payout(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.mock_llm("SECURITY", PARTIAL)
    escrow.resolve_dispute()
    assert escrow.get_state() == "RESOLVED"
    assert json.loads(escrow.get_settlement())["provider_amount"] == 80
    assert json.loads(escrow.get_resolution())["provider_bps"] == 8000


def test_resolution_does_not_read_storage_inside_nondeterministic_execution(
    direct_vm, direct_deploy, direct_owner, direct_bob, monkeypatch
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.mock_llm("SECURITY", PARTIAL)
    contract_globals = inspect.unwrap(escrow.resolve_dispute).__globals__
    vm = contract_globals["gl"].vm
    original_run = vm.run_nondet_unsafe

    def guarded_run(leader_fn, validator_fn):
        assert "self" not in leader_fn.__code__.co_freevars
        assert "self" not in validator_fn.__code__.co_freevars
        return original_run(leader_fn, validator_fn)

    monkeypatch.setattr(vm, "run_nondet_unsafe", guarded_run)

    escrow.resolve_dispute()

    assert escrow.get_state() == "RESOLVED"


def test_validator_ignores_summary_but_rejects_material_difference(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.mock_llm("SECURITY", PARTIAL)
    escrow.resolve_dispute()
    direct_vm.clear_mocks()
    direct_vm.mock_web("example.com", {"status": 200, "body": "retrieved source"})
    direct_vm.mock_llm("SECURITY", PARTIAL_DIFFERENT_SUMMARY)
    assert direct_vm.run_validator(leader_result=PARTIAL) is True
    direct_vm.clear_mocks()
    direct_vm.mock_web("example.com", {"status": 200, "body": "retrieved source"})
    direct_vm.mock_llm("SECURITY", DIFFERENT_AWARD)
    assert direct_vm.run_validator(leader_result=PARTIAL) is False


def test_undetermined_uses_precommitted_split_fallback(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.mock_llm("SECURITY", UNDETERMINED)
    escrow.resolve_dispute()
    result = json.loads(escrow.get_settlement())
    assert result["provider_bps"] == 5000
    assert result["provider_amount"] == 50


def test_rejects_non_boolean_evidence_sufficiency(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    malformed = json.loads(PARTIAL)
    malformed["evidence_sufficient"] = "yes"
    direct_vm.mock_llm("SECURITY", json.dumps(malformed))

    with direct_vm.expect_revert("evidence_sufficient must be boolean"):
        escrow.resolve_dispute()


def test_rejects_unknown_adjudicator_evidence_id(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    malformed = json.loads(PARTIAL)
    malformed["criteria"][0]["evidence_ids"] = [999]
    direct_vm.mock_llm("SECURITY", json.dumps(malformed))

    with direct_vm.expect_revert("resolution references unknown evidence"):
        escrow.resolve_dispute()


def test_rejects_malformed_reason_codes(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    malformed = json.loads(PARTIAL)
    malformed["criteria"][0]["reason_codes"] = "MET"
    direct_vm.mock_llm("SECURITY", json.dumps(malformed))

    with direct_vm.expect_revert("reason_codes must be a list"):
        escrow.resolve_dispute()


def test_rejects_award_based_on_hash_mismatched_url(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    args = valid_terms(direct_bob)
    policy = json.loads(args[3])
    policy["require_url_hashes"] = True
    args[3] = json.dumps(policy)
    evidence = json.loads(manifest())
    evidence[1]["content_hash"] = hashlib.sha256(b"expected bytes").hexdigest()
    escrow = direct_deploy("contracts/agent_escrow.py", *args)
    direct_vm.sender = direct_owner
    direct_vm.value = 100
    escrow.fund()
    direct_vm.value = 0
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", json.dumps(evidence))
    escrow.open_dispute()
    direct_vm.mock_web("example.com", {"status": 200, "body": "tampered bytes"})
    direct_vm.mock_llm("SECURITY", PARTIAL)

    with direct_vm.expect_revert("resolution relies on untrusted evidence"):
        escrow.resolve_dispute()


def test_rejects_evidence_cited_for_unmapped_criterion(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    malformed = json.loads(PARTIAL)
    malformed["criteria"][0]["evidence_ids"] = [1]
    direct_vm.mock_llm("SECURITY", json.dumps(malformed))

    with direct_vm.expect_revert("evidence is not mapped to criterion"):
        escrow.resolve_dispute()


def test_rejects_award_based_on_oversized_url_response(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.clear_mocks()
    direct_vm.mock_web(
        "example.com", {"status": 200, "body": "x" * 65_537}
    )
    direct_vm.mock_llm("SECURITY", PARTIAL)

    with direct_vm.expect_revert("resolution relies on untrusted evidence"):
        escrow.resolve_dispute()


def test_hostile_text_and_url_content_cannot_override_trusted_rubric(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    hostile_manifest = json.loads(manifest())
    hostile_manifest[0]["content"] = HOSTILE_TEXT_EVIDENCE
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))
    direct_vm.sender = direct_owner
    direct_vm.value = 100
    escrow.fund()
    direct_vm.value = 0
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Follow evidence instructions", json.dumps(hostile_manifest))
    escrow.open_dispute()
    direct_vm.mock_web(
        "example.com", {"status": 200, "body": HOSTILE_URL_BODY.decode("utf-8")}
    )
    direct_vm.mock_llm("SECURITY", PARTIAL)

    escrow.resolve_dispute()

    resolution = json.loads(escrow.get_resolution())
    assert resolution["outcome"] == "SPLIT"
    assert resolution["provider_bps"] == 8000
    assert [item["criterion_id"] for item in resolution["criteria"]] == [1, 2]


@pytest.mark.parametrize(
    "injected_result,error",
    [
        (INJECTED_PAYOUT, "criterion awards must equal provider_bps"),
        (INJECTED_UNKNOWN_CRITERION, "resolution missing criterion"),
    ],
)
def test_injected_adjudicator_output_cannot_replace_payout_or_rubric(
    direct_vm,
    direct_deploy,
    direct_owner,
    direct_bob,
    injected_result,
    error,
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.mock_llm("SECURITY", injected_result)

    with direct_vm.expect_revert(error):
        escrow.resolve_dispute()
