"""Verify source builds and managed installation with isolated local Git transport."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def run(argv, *, cwd, env, timeout=120):
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def isolated_environment(tmp_path):
    excluded = {
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "UV_PROJECT",
        "UV_PROJECT_ENVIRONMENT",
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "GH_ENTERPRISE_TOKEN",
        "GITHUB_ENTERPRISE_TOKEN",
    }
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("HERDR_", "AWS_", "GIT_")) and key not in excluded
    }
    env["UV_CACHE_DIR"] = subprocess.check_output(["uv", "cache", "dir"], text=True).strip()
    env["UV_OFFLINE"] = "1"
    env["UV_PYTHON_DOWNLOADS"] = "never"
    env["UV_PYTHON"] = str(Path(sys.executable).resolve())
    env["HOME"] = str(tmp_path / "home")
    env["XDG_CONFIG_HOME"] = str(tmp_path / "config")
    env["XDG_STATE_HOME"] = str(tmp_path / "state")
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def copy_source(target):
    target.mkdir()
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    )
    for name in sorted(set(output.decode().split("\0")) - {""}):
        source = ROOT / name
        if not source.is_file():
            continue
        assert not source.is_symlink(), name
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    assert not (target / ".venv").exists()
    assert not (target / ".local").exists()
    assert not (target / ".mcp.json").exists()


def test_manifest_builds_fresh_source_without_plugin_runtime_context(tmp_path):
    if shutil.which("uv") is None:
        pytest.skip("uv is required for source installation checks")
    source = tmp_path / "source"
    copy_source(source)
    env = isolated_environment(tmp_path)
    manifest_file = source / "herdr-plugin.toml"
    before = manifest_file.read_bytes()
    manifest = tomllib.loads(before.decode())
    for build in manifest["build"]:
        run(build["command"], cwd=source, env=env)
    assert manifest_file.read_bytes() == before
    python = str(source / ".venv/bin/python")
    run([python, "-m", "herdr_agentcore", "--help"], cwd=source, env=env)
    run(
        [python, "-c", "from herdr_agentcore.contract import decode_descriptor"],
        cwd=source,
        env=env,
    )
    assert not (source / "config.json").exists()


def test_managed_install_and_update_preserve_external_user_data(tmp_path):
    binary = os.environ.get("HERDR_TEST_BINARY")
    if not binary:
        pytest.skip("Set HERDR_TEST_BINARY to verify the managed installer")
    seed = tmp_path / "source"
    copy_source(seed)
    env = isolated_environment(tmp_path)

    def git(*args):
        return run(
            [
                "git",
                "-c",
                "user.name=Installation Test",
                "-c",
                "user.email=test@example.invalid",
                *args,
            ],
            cwd=seed,
            env=env,
        )

    git("init", "--initial-branch=main")
    git("add", "--force", ".")
    git("commit", "-m", "Test source package")
    # Only subprocesses in this test map this GitHub URL to a local fixture.
    # No public repository is contacted, created, or modified.
    env["GIT_CONFIG_COUNT"] = "2"
    env["GIT_CONFIG_KEY_0"] = f"url.{seed.as_uri()}.insteadOf"
    env["GIT_CONFIG_VALUE_0"] = "https://github.com/example/agentcore-test.git"
    env["GIT_CONFIG_KEY_1"] = "protocol.file.allow"
    env["GIT_CONFIG_VALUE_1"] = "always"
    with tempfile.TemporaryDirectory(prefix="h-") as sockets:
        env["HERDR_SOCKET_PATH"] = str(Path(sockets) / "a.sock")
        env["HERDR_CLIENT_SOCKET_PATH"] = str(Path(sockets) / "c.sock")

        def herdr(*args):
            return run([binary, "plugin", *args], cwd=tmp_path, env=env)

        herdr("install", "example/agentcore-test", "--ref", "main", "--yes")
        info = json.loads(herdr("list", "--plugin", "agentcore", "--json"))["result"]["plugins"][0]
        assert info["source"]["kind"] == "github"
        first_root = Path(info["plugin_root"])
        assert first_root.is_relative_to(tmp_path)
        config = Path(herdr("config-dir", "agentcore").strip())
        marker = config / "user-note.txt"
        marker.write_text("keep user configuration")
        python = str(first_root / ".venv/bin/python")
        run([python, "-m", "herdr_agentcore", "new", "--help"], cwd=first_root, env=env)
        (seed / "README.md").write_text((seed / "README.md").read_text() + "\nFixture update.\n")
        git("add", "README.md")
        git("commit", "-m", "Update test source package")
        herdr("update", "agentcore", "--yes")
        listing = json.loads(herdr("list", "--plugin", "agentcore", "--json"))
        updated = listing["result"]["plugins"][0]
        assert Path(updated["plugin_root"]) != first_root
        assert marker.read_text() == "keep user configuration"
        assert Path(herdr("config-dir", "agentcore").strip()) == config
