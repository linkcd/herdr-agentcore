"""Build a standalone, checksum-described contract artifact without publishing it."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from herdr_agentcore.contract import CONTRACT_VERSION

ROOT = Path(__file__).resolve().parents[1]


def package_contract(output: Path) -> None:
    source = ROOT / "contracts" / CONTRACT_VERSION
    files = {
        name: (source / name).read_bytes()
        for name in ("connection.schema.json", "fixtures.json", "README.md")
    }
    files.update({name: (ROOT / name).read_bytes() for name in ("LICENSE", "NOTICE")})
    manifest = {
        "descriptor_version": CONTRACT_VERSION,
        "sha256": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(f"{CONTRACT_VERSION}/{name}", content)
        archive.writestr(
            f"{CONTRACT_VERSION}/checksums.json", json.dumps(manifest, indent=2) + "\n"
        )
    print(f"Built contract artifact: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("dist") / f"connection-contract-{CONTRACT_VERSION}.zip"
    )
    package_contract(parser.parse_args().output)
