# Coding agent instructions

## Read first

Read [README.md](README.md), [the connector README](src/herdr_plugin/README.md), [the connection contract](contracts/1.0.0/README.md), and [the design](docs/DESIGN.md).
Use [the connection guide](docs/CONNECT_EXISTING_RUNTIME.md) before changing launch or recovery behavior.

## Scope and repository boundaries

This repository contains the Herdr AgentCore plugin.
The source repository is [linkcd/herdr-agentcore](https://github.com/linkcd/herdr-agentcore).
Runtime images, CDK infrastructure, provision profiles, storage, and runtime verification belong to [linkcd/agentcore-coding-assistant](https://github.com/linkcd/agentcore-coding-assistant).

1. Keep the plugin package and tests under `src/herdr_plugin/`.
2. Keep the Herdr manifest, Python workspace, lockfile, LICENSE, and NOTICE at the root.
3. The plugin owns the specification and fixtures under `contracts/1.0.0/`. Use full SemVer names for contract directories and archive prefixes.
4. Keep the Python contract validator internal to `herdr_agentcore`. Do not add a shared implementation-package dependency.
5. The runtime publisher implements the JSON format independently. No build may require its checkout beside this repository.
6. Required runtime information is the ARN and explicit launch argv. The endpoint is optional and defaults to `DEFAULT`; derive the region from the ARN.
7. Recognition hints, host AWS profile selection, and local labels belong to plugin profiles, not runtime exports.
8. Keep assistant names out of connector branches. A new terminal assistant needs a runtime and command, not plugin source changes.
9. A local profile can include a descriptive source label. It is not part of the public descriptor or an assistant selector.

## Preserve connector behavior

- Use only public Herdr CLI, plugin, and socket APIs. Do not modify Herdr core.
- A launch command is explicit and has no inferred default. Only the interactive setup prompt shows `["/app/run.sh"]` as a visible default that the user confirms; the saved profile always holds the argv. The setup prompt also defaults the local recognition hint to `opencode` (`terminal` clears it). This is a prompt default only, not a connector branch. Record the launch attempt before sending it. Never replay uncertain commands or user input.
- Reattach only to the recorded runtime-session and shell IDs. Require the original PTY after a launch attempt.
- Detach closes the WebSocket without a shell-shutdown frame. Stop requires explicit confirmation and targets the whole runtime session.
- The saved `stopped` label means AWS accepted the request, not that a completion waiter verified termination.
- Use the AWS credential provider chain. Do not copy worker credentials or print signed URLs, tokens, raw environments, or service payloads.
- Clear inherited recognition hints when no kind is configured. Never infer a kind from ARN or command text.
- Keep input/output nonblocking. Backpressure must not block reconnect, resize, or detach.
- Honor explicit profile, then `HERDR_AGENTCORE_PROFILE`, then the saved default. Do not infer defaults from profile names or counts.
- Preserve local records and profile snapshots. Unknown recovery annotations remain intact.
- The connector sends WebSocket pings every 20 seconds. Herdr client detach is different from closing the cloud-agent pane.
- Do not stop user sessions, alter AWS resources, or change the user's Herdr setup as an incidental test.

## Validation

Run from the repository root:

```bash
uv sync --frozen
uv run --frozen ruff check src scripts
uv run --frozen ruff format --check src scripts
HERDR_TEST_BINARY="$(command -v herdr)" uv run --frozen pytest -q --tb=short
uv run --frozen python src/herdr_plugin/tests/repository_privacy.py
uv build --package herdr-agentcore
uv run --frozen python src/herdr_plugin/tests/check_distributions.py --dist dist
uv run --frozen python scripts/package_contract.py
uv run --frozen python scripts/check_publication.py
git diff --check
```

Default tests make no AWS calls. Source-build tests use the populated uv cache without network access.
Optional Herdr installation/update tests use an isolated registry and local Git transport.
Live probes require explicit authorization and disposable sessions. Stop only their own sessions.
Preserve `.venv/`; the linked plugin uses it. Regenerate the lockfile when dependencies change, then use frozen installs.

## Changes and releases

- Inspect Git status and diffs before changes. Preserve unrelated edits and untracked files.
- Commit, push, and publish only when requested. Do not create remote repositories without approval.
- Keep credentials, local configuration, records, transcripts, and generated artifacts out of Git.
- Preserve licenses and attribution. Package builds include root legal files.
- Keep published descriptor versions stable. Introduce a new version for incompatible changes.
- Validate canonical schema/fixtures before packaging a release. Runtime consumers pin artifact checksums and a release reference.

## Documentation style

Use ASD-STE100-style English: short sentences, active voice, and one main idea per sentence.
Keep terms consistent. Distinguish deployed compute, connections, agent work, and persistent data.
State limits with units. Label implemented, tested, and planned behavior separately.
Use fictional identifiers in examples and exact API names in instructions.
