"""Check plugin documentation and distributions without a runtime checkout."""

import argparse
import re
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
COMPONENT = Path("src/herdr_plugin")
PACKAGE = "herdr_agentcore"


def anchors(path):
    result, counts = set(), {}
    fenced = False
    for line in path.read_text().splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if fenced or not line.startswith("#"):
            continue
        heading = re.sub(r"^#+\s+", "", line).lower()
        slug = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug if not count else f"{slug}-{count}")
    return result


def check_documents(root):
    documents = sorted(
        path
        for path in [
            *root.glob("*.md"),
            *root.glob("docs/*.md"),
            *root.glob("contracts/**/*.md"),
            *root.glob("src/herdr_plugin/**/*.md"),
        ]
        if not {"node_modules", "cdk.out"}.intersection(path.parts)
    )
    links = 0
    for document in documents:
        text = document.read_text()
        assert text.count("```") % 2 == 0, document
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (document.parent / unquote(parsed.path)).resolve() if parsed.path else document
            assert target.exists(), f"Missing target: {document.name}: {link}"
            if parsed.fragment and target.suffix == ".md":
                assert unquote(parsed.fragment) in anchors(target), f"Missing anchor: {link}"
            links += 1
    requirements = (root / "docs/REQUIREMENTS.md").read_text()
    identifiers = re.findall(r"^\| ([A-Z][0-9]{2}) \|", requirements, re.MULTILINE)
    assert identifiers and len(identifiers) == len(set(identifiers))
    for name in ("LICENSE", "NOTICE"):
        assert (root / name).is_file()
        nested = [
            path
            for path in (root / "src/herdr_plugin").rglob(name)
            if not {"node_modules", "cdk.out"}.intersection(path.parts)
        ]
        assert not nested, f"Project legal files must be kept at the repository root: {nested}"
    print(
        f"Verified {len(documents)} documents, {links} local links, "
        f"and {len(identifiers)} requirement IDs."
    )


def check_packages(root, directory):
    wheel_path = next(directory.glob(f"{PACKAGE}-*.whl"))
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()
        metadata_path = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata_directory = metadata_path.removesuffix("METADATA")
        assert all(name.startswith((PACKAGE + "/", metadata_directory)) for name in names)
        for legal in ("LICENSE", "NOTICE"):
            assert (
                wheel.read(metadata_directory + "extra_metadata/" + legal)
                == (root / legal).read_bytes()
            )
        assert not any("__pycache__" in name or "/tests/" in name for name in names)
        source_root = root / COMPONENT / PACKAGE
        for source in source_root.rglob("*"):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            name = (Path(PACKAGE) / source.relative_to(source_root)).as_posix()
            assert wheel.read(name) == source.read_bytes(), f"Wheel mismatch: {name}"
        metadata = Parser().parsestr(wheel.read(metadata_path).decode())
        dependencies = {
            re.split(r"[<>=!~\[ ;]", item)[0].replace("_", "-").lower()
            for item in metadata.get_all("Requires-Dist", [])
        }
        assert dependencies == {"bedrock-agentcore", "websockets"}
        assert f"{PACKAGE}/contract.py" in names
    with tarfile.open(next(directory.glob(f"{PACKAGE}-*.tar.gz"))) as archive:
        files = {"/".join(item.name.split("/")[1:]): item for item in archive if item.isfile()}
        for name in ("README.md", "pyproject.toml"):
            assert archive.extractfile(files[name]).read() == (root / COMPONENT / name).read_bytes()
        for legal in ("LICENSE", "NOTICE"):
            assert archive.extractfile(files[legal]).read() == (root / legal).read_bytes()
        assert not any("__pycache__" in name or "/.venv/" in name for name in files)
    print("Verified the standalone plugin wheel/source distribution and dependency metadata.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    args = parser.parse_args()
    check_documents(ROOT)
    check_packages(ROOT, args.dist)
