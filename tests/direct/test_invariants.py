import json

import pytest

from test_configuration import valid_terms
from test_lifecycle import manifest


AMOUNTS = [1, 2, 3, 10, 101, 10**6, 2**64 - 1]
PROVIDER_BPS = [0, 1, 3333, 5000, 9999, 10_000]


def submitted(direct_vm, direct_deploy, direct_owner, direct_bob, amount):
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))
    direct_vm.sender = direct_owner
    direct_vm.value = amount
    escrow.fund()
    direct_vm.value = 0
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", manifest())
    return escrow


@pytest.mark.parametrize("amount", AMOUNTS)
@pytest.mark.parametrize("provider_bps", PROVIDER_BPS)
def test_every_mutual_split_conserves_the_funded_amount(
    direct_vm,
    direct_deploy,
    direct_owner,
    direct_bob,
    amount,
    provider_bps,
):
    escrow = submitted(
        direct_vm, direct_deploy, direct_owner, direct_bob, amount
    )
    direct_vm.sender = direct_owner
    escrow.propose_settlement(provider_bps)
    direct_vm.sender = direct_bob
    escrow.confirm_settlement(provider_bps)

    settlement = json.loads(escrow.get_settlement())
    assert settlement["provider_bps"] == provider_bps
    assert settlement["provider_amount"] == amount * provider_bps // 10_000
    assert settlement["client_amount"] == amount - settlement["provider_amount"]
    assert settlement["provider_amount"] + settlement["client_amount"] == amount


def test_terminal_state_rejects_every_state_changing_entrypoint(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    escrow = submitted(direct_vm, direct_deploy, direct_owner, direct_bob, 101)
    direct_vm.sender = direct_owner
    escrow.accept_delivery()

    calls = [
        (escrow.fund, ()),
        (escrow.submit_delivery, ("Again", manifest())),
        (escrow.accept_delivery, ()),
        (escrow.propose_settlement, (5000,)),
        (escrow.confirm_settlement, (5000,)),
        (escrow.claim_delivery_timeout, ()),
        (escrow.claim_review_timeout, ()),
        (escrow.open_dispute, ()),
        (escrow.resolve_dispute, ()),
        (escrow.claim_dispute_timeout, ()),
    ]
    for method, args in calls:
        with direct_vm.expect_revert("state must be"):
            method(*args)

    settlement = json.loads(escrow.get_settlement())
    assert settlement["provider_amount"] == 101
    assert settlement["client_amount"] == 0
    assert escrow.get_state() == "ACCEPTED"


def test_unrelated_caller_cannot_control_privileged_transitions(
    direct_vm,
    direct_deploy,
    direct_owner,
    direct_bob,
    direct_charlie,
):
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))
    direct_vm.sender = direct_owner
    direct_vm.value = 101
    escrow.fund()
    direct_vm.value = 0

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("only provider"):
        escrow.submit_delivery("Forged", manifest())

    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", manifest())
    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("only client"):
        escrow.accept_delivery()
    with direct_vm.expect_revert("only a party"):
        escrow.propose_settlement(5000)
    with direct_vm.expect_revert("only a party"):
        escrow.open_dispute()
    assert escrow.get_state() == "SUBMITTED"
