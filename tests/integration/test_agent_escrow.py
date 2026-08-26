import json

from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded


def test_deploy_fund_submit_and_accept_through_localnet(accounts):
    client, provider = accounts[0], accounts[1]
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
        ]
    )
    policy = json.dumps(
        {
            "allowed_kinds": ["TEXT"],
            "require_url_hashes": False,
            "requirements": "Use only the frozen submitted text.",
        }
    )
    evidence = json.dumps(
        [
            {
                "id": 1,
                "kind": "TEXT",
                "content": "Executive summary and sourced findings.",
                "content_hash": "",
                "criterion_ids": [1, 2],
                "description": "Delivered report",
            }
        ]
    )

    factory = get_contract_factory("AgentEscrow")
    escrow = factory.deploy(
        args=[
            provider.address,
            "Research the requested market.",
            rubric,
            policy,
            2_000_000_000,
            86_400,
            "SPLIT_50_50",
            172_800,
        ],
        account=client,
    )

    assert tx_execution_succeeded(escrow.fund().transact(value=101))
    assert tx_execution_succeeded(
        escrow.connect(provider).submit_delivery(args=["Done", evidence]).transact()
    )
    assert tx_execution_succeeded(escrow.accept_delivery().transact())

    assert escrow.get_state().call() == "ACCEPTED"
    settlement = json.loads(escrow.get_settlement().call())
    assert settlement["provider_amount"] == 101
    assert settlement["client_amount"] == 0
