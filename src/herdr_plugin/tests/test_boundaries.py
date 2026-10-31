"""Keep the installed connector independent of runtime deployment code."""

import ast
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "src/herdr_plugin/herdr_agentcore"


def imports(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            yield from (alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            yield node.module.split(".")[0]


def test_plugin_is_the_only_workspace_package():
    assert {path.name for path in (ROOT / "src").iterdir() if path.is_dir()} == {"herdr_plugin"}
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert metadata["tool"]["uv"]["workspace"]["members"] == ["src/herdr_plugin"]
    package = tomllib.loads((ROOT / "src/herdr_plugin/pyproject.toml").read_text())
    dependencies = {
        re.split(r"[<>=!~\[]", value)[0] for value in package["project"]["dependencies"]
    }
    assert dependencies == {"bedrock-agentcore", "websockets"}
    assert (ROOT / "contracts/v1/connection.schema.json").is_file()


def test_plugin_imports_only_local_modules_and_supported_dependencies():
    allowed = sys.stdlib_module_names | {
        "herdr_agentcore",
        "boto3",
        "botocore",
        "bedrock_agentcore",
        "websockets",
    }
    for source in PACKAGE.glob("*.py"):
        assert set(imports(source)) <= allowed, source


def test_contract_validator_has_only_standard_library_dependencies():
    assert set(imports(PACKAGE / "contract.py")) <= sys.stdlib_module_names
