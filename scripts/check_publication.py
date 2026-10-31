"""Check local plugin metadata and optional public GitHub marketplace prerequisites."""

import argparse
import base64
import json
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"


def validate_manifest(manifest):
    for field in ("id", "name", "version", "min_herdr_version", "description"):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            raise ValueError(f"Manifest requires nonempty {field}")
    if not re.fullmatch(r"[A-Za-z0-9.:_-]{1,120}", manifest["id"]):
        raise ValueError("Invalid plugin ID")
    for field in ("version", "min_herdr_version"):
        if not re.fullmatch(SEMVER, manifest[field]):
            raise ValueError(f"Use stable SemVer for {field}")
    platforms = manifest.get("platforms")
    if (
        not isinstance(platforms, list)
        or not platforms
        or any(value not in ("linux", "macos", "windows") for value in platforms)
    ):
        raise ValueError("Declare supported plugin platforms")
    for section in ("build", "startup", "actions", "events", "panes", "link_handlers"):
        entries = manifest.get(section, [])
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise ValueError(f"{section} must be an array of manifest tables")
    for section in ("actions", "panes", "link_handlers"):
        identifiers = [entry.get("id") for entry in manifest.get(section, [])]
        if any(
            not isinstance(identifier, str)
            or not re.fullmatch(r"[A-Za-z0-9:_-]{1,120}", identifier)
            for identifier in identifiers
        ) or len(identifiers) != len(set(identifiers)):
            raise ValueError(f"Invalid or duplicate {section} IDs")
        if any(
            not isinstance(entry.get("title"), str) or not entry["title"].strip()
            for entry in manifest.get(section, [])
        ):
            raise ValueError(f"{section} entries require titles")
    for section in ("build", "startup", "actions", "events", "panes"):
        for entry in manifest.get(section, []):
            command = entry.get("command")
            if (
                not isinstance(command, list)
                or not command
                or any(not isinstance(argument, str) or not argument for argument in command)
            ):
                raise ValueError(f"{section} command must be a nonempty argv array")
    actions = {entry["id"] for entry in manifest.get("actions", [])}
    if any(entry.get("action") not in actions for entry in manifest.get("link_handlers", [])):
        raise ValueError("Link handler references an unknown action")


def check_local(root=ROOT):
    manifest = tomllib.loads((root / "herdr-plugin.toml").read_text())
    validate_manifest(manifest)
    metadata = tomllib.loads((root / "src/herdr_plugin/pyproject.toml").read_text())
    if manifest["version"] != metadata["project"]["version"]:
        raise ValueError("Manifest and package versions must match")
    for name in ("README.md", "LICENSE", "NOTICE", "uv.lock", "docs/PUBLISHING.md"):
        if not (root / name).is_file():
            raise ValueError(f"Missing publication file: {name}")
    print(f"Local publication checks passed for {manifest['id']} {manifest['version']}.")
    return manifest


def github_json(route):
    return json.loads(
        subprocess.check_output(["gh", "api", "--hostname", "github.com", route], text=True)
    )


def check_github(repository, local):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or any(
        part in {".", ".."} for part in repository.split("/")
    ):
        raise ValueError("Use OWNER/REPO GitHub shorthand")
    metadata = github_json(f"repos/{repository}")
    if metadata["private"] or metadata["fork"] or metadata["archived"]:
        raise ValueError("Marketplace repositories must be public, non-fork, and not archived")
    if "herdr-plugin" not in metadata.get("topics", []):
        raise ValueError("Add the herdr-plugin GitHub topic")
    # The Contents API uses the default branch when no ref is supplied.
    entry = github_json(f"repos/{repository}/contents/herdr-plugin.toml")
    if entry.get("type") != "file" or entry.get("encoding") != "base64":
        raise ValueError("Default branch must contain a root manifest file")
    published = tomllib.loads(base64.b64decode(entry["content"]).decode())
    validate_manifest(published)
    if published != local:
        raise ValueError("Published manifest does not match the local manifest")
    print(f"GitHub marketplace prerequisites passed for {repository}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github", help="Also check OWNER/REPO using read-only GitHub API calls")
    args = parser.parse_args()
    try:
        manifest = check_local()
        if args.github:
            check_github(args.github, manifest)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Publication check failed: {error}") from None
