import json
import pytest

from test_configuration import valid_terms
from test_lifecycle import manifest


def submitted(direct_vm, direct_deploy, direct_owner, direct_bob, amount=101):
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))
    direct_vm.sender = direct_owner
    direct_vm.value = amount
    escrow.fund()
    direct_vm.value = 0
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", manifest())
    return escrow


def test_client_accepts_full_provider_payout(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = submitted(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.sender = direct_owner
    escrow.accept_delivery()
    assert escrow.get_state() == "ACCEPTED"
    settlement = json.loads(escrow.get_settlement())
    assert settlement == {
        "client_amount": 0,
        "provider_amount": 101,
        "provider_bps": 10000,
        "settled": True,
    }
    with direct_vm.expect_revert("state must be SUBMITTED"):
        escrow.accept_delivery()


def test_mutual_split_conserves_escrow(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = submitted(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.sender = direct_owner
    escrow.propose_settlement(3333)
    direct_vm.sender = direct_bob
    escrow.confirm_settlement(3333)
    result = json.loads(escrow.get_settlement())
    assert result["provider_amount"] == 33
    assert result["client_amount"] == 68
    assert result["provider_amount"] + result["client_amount"] == 101
    assert escrow.get_state() == "SETTLED"


def test_mismatched_mutual_split_does_not_settle(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = submitted(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.sender = direct_owner
    escrow.propose_settlement(3000)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("settlement proposal does not match"):
        escrow.confirm_settlement(4000)
    assert escrow.get_state() == "SUBMITTED"


def test_client_refunds_after_missed_delivery_deadline(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))
    direct_vm.sender = direct_owner
    direct_vm.value = 101
    escrow.fund()
    direct_vm.value = 0
    direct_vm.warp("2040-01-01T00:00:00+00:00")
    escrow.claim_delivery_timeout()
    result = json.loads(escrow.get_settlement())
    assert escrow.get_state() == "REFUNDED"
    assert result["client_amount"] == 101


def test_provider_claims_after_unanswered_review(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = submitted(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.warp("2040-01-01T00:00:00+00:00")
    direct_vm.sender = direct_bob
    escrow.claim_review_timeout()
    result = json.loads(escrow.get_settlement())
    assert escrow.get_state() == "ACCEPTED"
    assert result["provider_amount"] == 101


def disputed(direct_vm, direct_deploy, direct_owner, direct_bob, fallback):
    args = valid_terms(direct_bob)
    args[6] = fallback
    escrow = direct_deploy("contracts/agent_escrow.py", *args)
    direct_vm.sender = direct_owner
    direct_vm.value = 101
    escrow.fund()
    direct_vm.value = 0
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", manifest())
    escrow.open_dispute()
    return escrow


def test_dispute_timeout_cannot_be_claimed_early(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = disputed(
        direct_vm, direct_deploy, direct_owner, direct_bob, "SPLIT_50_50"
    )

    with direct_vm.expect_revert("dispute deadline not elapsed"):
        escrow.claim_dispute_timeout()
    assert escrow.get_state() == "DISPUTED"


@pytest.mark.parametrize(
    "fallback,provider_bps,provider_amount,client_amount",
    [
        ("REFUND_CLIENT", 0, 0, 101),
        ("PAY_PROVIDER", 10_000, 101, 0),
        ("SPLIT_50_50", 5_000, 50, 51),
    ],
)
def test_dispute_timeout_applies_precommitted_fallback(
    direct_vm,
    direct_deploy,
    direct_owner,
    direct_bob,
    direct_charlie,
    fallback,
    provider_bps,
    provider_amount,
    client_amount,
):
    escrow = disputed(direct_vm, direct_deploy, direct_owner, direct_bob, fallback)
    direct_vm.warp("2040-01-01T00:00:00+00:00")
    direct_vm.sender = direct_charlie
    escrow.claim_dispute_timeout()

    settlement = json.loads(escrow.get_settlement())
    resolution = json.loads(escrow.get_resolution())
    assert escrow.get_state() == "RESOLVED"
    assert settlement["provider_bps"] == provider_bps
    assert settlement["provider_amount"] == provider_amount
    assert settlement["client_amount"] == client_amount
    assert provider_amount + client_amount == 101
    assert resolution["resolution_source"] == "DISPUTE_TIMEOUT"
    assert resolution["outcome"] == "UNDETERMINED"
    assert [item["status"] for item in resolution["criteria"]] == [
        "INSUFFICIENT",
        "INSUFFICIENT",
    ]
    with direct_vm.expect_revert("state must be DISPUTED"):
        escrow.claim_dispute_timeout()
