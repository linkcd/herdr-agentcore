"""Verify that release archives use the exact contract version and file checksums."""

import hashlib
import json
import zipfile

from herdr_agentcore.contract import CONTRACT_VERSION
from package_contract import package_contract


def test_contract_archive_layout_and_checksums(tmp_path):
    archive_path = tmp_path / f"connection-contract-{CONTRACT_VERSION}.zip"
    package_contract(archive_path)
    prefix = f"{CONTRACT_VERSION}/"
    with zipfile.ZipFile(archive_path) as archive:
        assert all(name.startswith(prefix) for name in archive.namelist())
        manifest = json.loads(archive.read(prefix + "checksums.json"))
        assert manifest["descriptor_version"] == CONTRACT_VERSION
        assert set(manifest["sha256"]) == {
            "connection.schema.json",
            "fixtures.json",
            "README.md",
            "LICENSE",
            "NOTICE",
        }
        for name, expected in manifest["sha256"].items():
            assert hashlib.sha256(archive.read(prefix + name)).hexdigest() == expected
        schema = json.loads(archive.read(prefix + "connection.schema.json"))
        assert schema["properties"]["version"]["default"] == CONTRACT_VERSION
