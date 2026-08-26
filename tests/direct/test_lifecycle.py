import json
import pytest

from test_configuration import valid_terms


def manifest():
    return json.dumps(
        [
            {"id": 1, "kind": "TEXT", "content": "Summary and findings", "content_hash": "", "criterion_ids": [2], "description": "Report excerpt"},
            {"id": 2, "kind": "URL", "content": "https://example.com/source", "content_hash": "", "criterion_ids": [1], "description": "Primary source"},
        ]
    )


def funded(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = direct_deploy("contracts/agent_escrow.py", *valid_terms(direct_bob))
    direct_vm.sender = direct_owner
    direct_vm.value = 100
    escrow.fund()
    direct_vm.value = 0
    return escrow


def test_only_provider_can_submit_once(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = funded(direct_vm, direct_deploy, direct_owner, direct_bob)
    with direct_vm.expect_revert("only provider"):
        escrow.submit_delivery("Done", manifest())
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", manifest())
    assert escrow.get_state() == "SUBMITTED"
    delivery = json.loads(escrow.get_delivery())
    assert delivery["summary"] == "Done"
    assert len(delivery["evidence"]) == 2
    with direct_vm.expect_revert("state must be FUNDED"):
        escrow.submit_delivery("Again", manifest())


def test_rejects_non_http_url(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = funded(direct_vm, direct_deploy, direct_owner, direct_bob)
    bad = json.loads(manifest())
    bad[1]["content"] = "file:///etc/passwd"
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("URL evidence must use http or https"):
        escrow.submit_delivery("Done", json.dumps(bad))


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/admin",
        "http://127.0.0.1/secrets",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/admin",
    ],
)
def test_rejects_non_public_url_targets(
    direct_vm, direct_deploy, direct_owner, direct_bob, url
):
    escrow = funded(direct_vm, direct_deploy, direct_owner, direct_bob)
    bad = json.loads(manifest())
    bad[1]["content"] = url
    direct_vm.sender = direct_bob

    with direct_vm.expect_revert("URL evidence must target a public host"):
        escrow.submit_delivery("Done", json.dumps(bad))


def test_url_hash_is_required_when_policy_enables_it(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    args = valid_terms(direct_bob)
    policy = json.loads(args[3])
    policy["require_url_hashes"] = True
    args[3] = json.dumps(policy)
    escrow = direct_deploy("contracts/agent_escrow.py", *args)
    direct_vm.sender = direct_owner
    direct_vm.value = 100
    escrow.fund()
    direct_vm.value = 0
    direct_vm.sender = direct_bob

    with direct_vm.expect_revert("URL evidence requires a SHA-256 hash"):
        escrow.submit_delivery("Done", manifest())


def test_either_party_can_open_dispute(direct_vm, direct_deploy, direct_owner, direct_bob):
    escrow = funded(direct_vm, direct_deploy, direct_owner, direct_bob)
    direct_vm.sender = direct_bob
    escrow.submit_delivery("Done", manifest())
    direct_vm.sender = direct_owner
    escrow.open_dispute()
    assert escrow.get_state() == "DISPUTED"
