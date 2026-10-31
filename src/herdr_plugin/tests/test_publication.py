"""Publication metadata and read-only marketplace prerequisite checks."""

import base64
import copy
import tomllib
from pathlib import Path

import pytest
from check_publication import check_github, check_local, validate_manifest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def manifest():
    return tomllib.loads((ROOT / "herdr-plugin.toml").read_text())


def test_local_publication_requirements():
    assert check_local(ROOT)["id"] == "agentcore"


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", "1"),
        ("min_herdr_version", "latest"),
        ("platforms", []),
        ("platforms", {"linux": True}),
        ("platforms", ["unsupported"]),
        ("id", "bad id"),
        ("description", ""),
    ],
)
def test_invalid_manifest_metadata_is_rejected(manifest, field, value):
    with pytest.raises(ValueError):
        validate_manifest({**manifest, field: value})


def test_duplicate_local_ids_and_non_argv_commands_are_rejected(manifest):
    invalid = copy.deepcopy(manifest)
    invalid["actions"].append(invalid["actions"][0])
    with pytest.raises(ValueError):
        validate_manifest(invalid)
    invalid = copy.deepcopy(manifest)
    invalid["build"][0]["command"] = "uv sync"
    with pytest.raises(ValueError):
        validate_manifest(invalid)


def test_manifest_entrypoints_require_tables_and_titles(manifest):
    with pytest.raises(ValueError):
        validate_manifest({**manifest, "panes": {"id": "setup"}})
    invalid = copy.deepcopy(manifest)
    del invalid["panes"][0]["title"]
    with pytest.raises(ValueError):
        validate_manifest(invalid)


@pytest.mark.parametrize(
    "changes",
    [
        {"private": True},
        {"fork": True},
        {"archived": True},
        {"topics": []},
    ],
)
def test_marketplace_requires_public_active_nonfork_topic(monkeypatch, manifest, changes):
    metadata = {"private": False, "fork": False, "archived": False, "topics": ["herdr-plugin"]}
    monkeypatch.setattr("check_publication.github_json", lambda route: {**metadata, **changes})
    with pytest.raises(ValueError):
        check_github("example/plugin", manifest)


def test_marketplace_checks_the_default_branch_manifest_without_mutation(monkeypatch, manifest):
    routes = []

    def get(route):
        routes.append(route)
        if route == "repos/example/plugin":
            return {"private": False, "fork": False, "archived": False, "topics": ["herdr-plugin"]}
        assert route == "repos/example/plugin/contents/herdr-plugin.toml"
        return {
            "type": "file",
            "encoding": "base64",
            "content": base64.b64encode((ROOT / "herdr-plugin.toml").read_bytes()).decode(),
        }

    monkeypatch.setattr("check_publication.github_json", get)
    check_github("example/plugin", manifest)
    assert len(routes) == 2
