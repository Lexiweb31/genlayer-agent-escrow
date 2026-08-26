import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = [
    "rubric.schema.json",
    "evidence-policy.schema.json",
    "evidence-manifest.schema.json",
    "resolution.schema.json",
]


def test_all_public_schemas_are_valid_json_schema_documents():
    for filename in SCHEMAS:
        path = ROOT / "schemas" / filename
        schema = json.loads(path.read_text())
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"].endswith(filename)
        assert schema["title"]


def test_deployment_example_matches_constructor_and_contract_invariants():
    example = json.loads((ROOT / "examples" / "deploy_args.json").read_text())
    assert example["contract"] == "AgentEscrow"
    assert example["argument_names"] == [
        "provider",
        "specification",
        "rubric_json",
        "evidence_policy_json",
        "delivery_deadline",
        "review_period",
        "undetermined_fallback",
        "adjudication_period",
    ]
    assert len(example["args"]) == 8
    rubric = json.loads(example["args"][2])
    policy = json.loads(example["args"][3])
    assert sum(item["weight_bps"] for item in rubric) == 10_000
    assert len({item["id"] for item in rubric}) == len(rubric)
    assert policy["allowed_kinds"] == ["TEXT", "URL"]
    assert policy["require_url_hashes"] is True
    assert example["args"][6] in {"REFUND_CLIENT", "PAY_PROVIDER", "SPLIT_50_50"}
    assert 0 < example["args"][5] <= 2_592_000
    assert 0 < example["args"][7] <= 2_592_000
