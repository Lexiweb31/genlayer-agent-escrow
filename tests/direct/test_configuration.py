import json
import pytest


def address_text(raw_address):
    return "0x" + raw_address.hex()


def valid_terms(provider):
    rubric = json.dumps(
        [
            {
                "id": 1,
                "requirement": "Return a sourced report",
                "weight_bps": 6000,
                "evidence_guidance": "Cite URLs",
            },
            {
                "id": 2,
                "requirement": "Include an executive summary",
                "weight_bps": 4000,
                "evidence_guidance": "Use submitted text",
            },
        ],
        sort_keys=True,
    )
    policy = json.dumps(
        {
            "allowed_kinds": ["TEXT", "URL"],
            "require_url_hashes": False,
            "requirements": "Sources must be publicly retrievable.",
        },
        sort_keys=True,
    )
    return [
        address_text(provider),
        "Research the requested market.",
        rubric,
        policy,
        2_000_000_000,
        86_400,
        "SPLIT_50_50",
        172_800,
    ]


def test_deployment_stores_immutable_terms(direct_vm, direct_deploy, direct_bob):
    """Catches constructors that drop or alter agreement terms."""
    direct_vm.check_pickling = True
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))

    assert escrow.get_state() == "CREATED"
    agreement = json.loads(escrow.get_agreement())
    assert agreement["provider"].lower() == address_text(direct_bob)
    assert agreement["specification"] == "Research the requested market."
    assert agreement["rubric"] == [
        {
            "evidence_guidance": "Cite URLs",
            "id": 1,
            "requirement": "Return a sourced report",
            "weight_bps": 6000,
        },
        {
            "evidence_guidance": "Use submitted text",
            "id": 2,
            "requirement": "Include an executive summary",
            "weight_bps": 4000,
        },
    ]
    assert agreement["escrow_amount"] == 0


def test_deployment_records_client_and_empty_audit_log(
    direct_deploy, direct_owner, direct_bob
):
    """Catches assigning authority to the provider or fabricating transitions."""
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))

    agreement = json.loads(escrow.get_agreement())
    assert agreement["client"].lower() == address_text(direct_owner)
    assert list(escrow.get_audit_log()) == []


def test_deployment_accepts_cli_decoded_json_arguments(direct_deploy, direct_bob):
    args = valid_terms(direct_bob)
    args[2] = json.loads(args[2])
    args[3] = json.loads(args[3])

    escrow = direct_deploy("contracts/agent_escrow.py", *args)

    agreement = json.loads(escrow.get_agreement())
    assert len(agreement["rubric"]) == 2
    assert agreement["evidence_policy"]["allowed_kinds"] == ["TEXT", "URL"]


def test_rejects_rubric_whose_weights_do_not_total_10000(direct_deploy, direct_bob):
    """Catches underfunded or overfunded scoring rubrics."""
    args = valid_terms(direct_bob)
    rubric = json.loads(args[2])
    rubric[0]["weight_bps"] = 5000
    args[2] = json.dumps(rubric)

    with pytest.raises(Exception, match="rubric weights must total 10000"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_rejects_duplicate_criterion_ids(direct_deploy, direct_bob):
    """Catches ambiguous criterion-to-evidence mappings."""
    args = valid_terms(direct_bob)
    rubric = json.loads(args[2])
    rubric[1]["id"] = 1
    args[2] = json.dumps(rubric)

    with pytest.raises(Exception, match="criterion ids must be unique"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_rejects_oversized_specification(direct_deploy, direct_bob):
    args = valid_terms(direct_bob)
    args[1] = "x" * 8_193

    with pytest.raises(Exception, match="specification too large"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_rejects_unknown_undetermined_fallback(direct_deploy, direct_bob):
    args = valid_terms(direct_bob)
    args[6] = "ARBITRARY_PAYOUT"

    with pytest.raises(Exception, match="invalid undetermined fallback"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_rejects_unsupported_evidence_kind(direct_deploy, direct_bob):
    args = valid_terms(direct_bob)
    policy = json.loads(args[3])
    policy["allowed_kinds"] = ["TEXT", "EXECUTABLE"]
    args[3] = json.dumps(policy)

    with pytest.raises(Exception, match="unsupported evidence kind"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_rejects_elapsed_delivery_deadline(direct_deploy, direct_bob):
    args = valid_terms(direct_bob)
    args[4] = 1

    with pytest.raises(Exception, match="delivery deadline must be in the future"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_rejects_zero_review_period(direct_deploy, direct_bob):
    args = valid_terms(direct_bob)
    args[5] = 0

    with pytest.raises(Exception, match="review period out of range"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_rejects_zero_adjudication_period(direct_deploy, direct_bob):
    args = valid_terms(direct_bob)
    args[7] = 0

    with pytest.raises(Exception, match="adjudication period out of range"):
        direct_deploy("contracts/agent_escrow.py", *args)


def test_only_client_can_fund_once(
    direct_vm, direct_deploy, direct_owner, direct_bob, direct_charlie
):
    """Catches unauthorized, zero-value, and repeated escrow activation."""
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))

    direct_vm.sender = direct_charlie
    direct_vm.value = 100
    with direct_vm.expect_revert("only client"):
        escrow.fund()

    direct_vm.sender = direct_owner
    direct_vm.value = 0
    with direct_vm.expect_revert("funding value must be positive"):
        escrow.fund()

    direct_vm.value = 101
    escrow.fund()
    assert escrow.get_state() == "FUNDED"
    assert json.loads(escrow.get_agreement())["escrow_amount"] == 101
    assert json.loads(list(escrow.get_audit_log())[0])["transition"] == "FUNDED"

    with direct_vm.expect_revert("state must be CREATED"):
        escrow.fund()
