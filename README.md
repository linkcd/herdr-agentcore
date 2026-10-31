# Herdr AgentCore plugin

Connect Herdr terminals to interactive assistants hosted in Amazon Bedrock AgentCore Runtime.
The plugin manages terminal transport, saved connections, reconnect, detach, and stop.
It does not build images or deploy AWS resources.

Runtime images and CDK infrastructure are maintained independently in the `agentcore-coding-runtimes` repository.

## Repository layout

```text
herdr-plugin.toml                 Herdr actions and pane entrypoints
src/herdr_plugin/                Python connector package and tests
contracts/v1/                    Canonical JSON schema and conformance cases
scripts/package_contract.py      Contract release-artifact builder
docs/                            Connector design and operation guides
```

## Install from GitHub

Use macOS or Linux, Git, Python 3.11+, uv, and Herdr 0.9.5+.
The management host needs AWS permission to invoke the selected runtime's Shell API.
The runtime must contain a working interactive launch command.
Installation downloads locked Python dependencies. Herdr does not install system toolchains.

Replace `OWNER/REPO` with the public repository that hosts this plugin:

```bash
herdr plugin install OWNER/REPO
herdr plugin action invoke agentcore.setup
herdr plugin action invoke agentcore.new
```

Run the actions from a Herdr workspace. Setup asks for the runtime ARN, launch argv, and optional local settings.
Supply argv as JSON, for example `["/app/run.sh"]` when that is the runtime's declared launcher.
Herdr previews the manifest and build commands before an interactive install.
Use `--ref TAG_OR_COMMIT` to select a published revision and `--yes` for a trusted noninteractive install.
Plugins run with the host user's permissions and AWS credential access.

## Develop from source

Run these commands from the repository root:

```bash
uv sync --frozen --no-dev
herdr plugin link "$PWD"
```

For a source checkout, the CLI can also import a descriptor supplied by the runtime owner:

```bash
.venv/bin/herdr-agentcore configure \
  --connection-file /path/to/connection.json \
  --profile my-agent \
  --agent-kind opencode \
  --config-dir "$(herdr plugin config-dir agentcore)"
```

`--agent-kind` is optional local metadata. Omit it for an ordinary terminal.
It does not select a runtime image or install recognition support in Herdr.
The plugin accepts any valid recognition identifier without assistant-specific branches.

For CDK output documents, use `--cdk-outputs /path/to/outputs.json --stack RuntimeStack` instead of `--connection-file`.
For direct registration, supply the runtime ARN and explicit launch argv:

```bash
.venv/bin/herdr-agentcore configure \
  --runtime-arn "$RUNTIME_ARN" \
  --profile my-agent \
  --agent-kind opencode \
  --config-dir "$(herdr plugin config-dir agentcore)" \
  --command /app/run.sh
```

Set `RUNTIME_ARN` to the actual runtime ARN. `/app/run.sh` is an example command, not a plugin default.
Put `--command` last. Use `--aws-profile` only when selecting a named host credential profile.
The default AWS credential chain is used otherwise.
The AWS region is derived from the ARN. The endpoint defaults to `DEFAULT`.

## Launch and manage connections

The first saved profile becomes the default. Later imports do not replace the default.

```bash
.venv/bin/herdr-agentcore set-default my-agent \
  --config-dir "$(herdr plugin config-dir agentcore)"
herdr plugin action invoke agentcore.new
```

| Action | Purpose |
| --- | --- |
| `agentcore.new` | Create a new runtime-session and shell binding. |
| `agentcore.attach` | Reattach to the original live remote terminal. |
| `agentcore.sessions` | Display last-known saved connection records. |
| `agentcore.stop` | Confirm and request whole-session termination. |

Run actions with `herdr plugin action invoke ACTION`.
Use `.venv/bin/herdr-agentcore action new --profile NAME` for an explicit profile selection.
Selection order is explicit profile, `HERDR_AGENTCORE_PROFILE`, then the saved default.

Detach from a cloud connection with Ctrl+] followed by `d`, or close its cloud-agent pane.
Detach closes transport without terminating the remote process.
Closing only the Herdr client window can leave the background server and cloud connector running.
The connector sends WebSocket keepalive pings every 20 seconds while connected.
Runtime lifecycle limits are controlled by the deployment, not the plugin.

Reattachment preserves the process and conversation only while the original PTY survives.
The connector never silently recreates an expired process or replays uncertain input.
Persistent files and conversation recovery are runtime/application responsibilities.

## Minimal connection contract

Runtime publishers provide two connection values: runtime ARN and explicit launch argv.
They can also provide an endpoint qualifier. The descriptor envelope identifies the format.

```json
{
  "version": "1.0.0",
  "transport": "agentcore-shell-v1",
  "connection": {
    "runtime_arn": "arn:aws:bedrock-agentcore:eu-west-1:123456789012:runtime/example-Abc123",
    "command": ["/app/run.sh"]
  }
}
```

The example identifiers are fictional.
Recognition hints, local profile labels, host credentials, and execution IDs are not exported by runtimes.
The plugin owns [the contract specification](contracts/v1/README.md) and its internal validator.
Runtime publishers consume pinned schema/fixture artifacts, not plugin source code.

## Build and verify

```bash
uv sync --frozen
uv run --frozen ruff check src/herdr_plugin scripts
uv run --frozen ruff format --check src/herdr_plugin scripts
uv run --frozen pytest -q --tb=short
uv run --frozen python src/herdr_plugin/tests/repository_privacy.py
uv build --package herdr-agentcore
uv run --frozen python src/herdr_plugin/tests/check_distributions.py --dist dist
uv run --frozen python scripts/package_contract.py
uv run --frozen python scripts/check_publication.py
```

Set `HERDR_TEST_BINARY` to an installed Herdr executable to include isolated manifest and managed installation/update tests.
The managed installer test redirects its GitHub source to a local Git fixture; it does not publish a repository or contact AWS.
The default source-build test runs the manifest build in a fresh source directory without plugin runtime context.
Default tests make no AWS calls. Live tests require an explicit target and authorization.
No Node.js, CDK project, runtime checkout, or separate contract package is required to build this plugin.

Publish the contract archive with a tagged plugin release after conformance checks pass.
Keep descriptor versions separate from plugin package and runtime image versions.

## Update and remove

```bash
herdr plugin update agentcore
herdr plugin uninstall agentcore
```

Updates use the ref selected during installation. Locally linked plugins are updated by editing and building their source checkout.
To change a pinned revision, install the same GitHub source with the desired `--ref` value.
Configuration and connection records are stored outside the installed source and survive updates and uninstall.
Use `herdr plugin config-dir agentcore` to locate configuration. Runtime actions receive `HERDR_PLUGIN_CONFIG_DIR` and `HERDR_PLUGIN_STATE_DIR` automatically.
A managed install cannot replace a local link. Finish plugin work and use `herdr plugin unlink agentcore` before changing installation methods.

## Publish and list in the marketplace

Publish the source to a public, non-fork, non-archived GitHub repository with `herdr-plugin.toml` on its default branch.
Add the repository topic `herdr-plugin`. Herdr's marketplace discovers it automatically, normally within its 30-minute refresh cycle.
See [publishing](docs/PUBLISHING.md) for source validation, SemVer releases, and the read-only marketplace check.

## Documentation

- [Connection guide](docs/CONNECT_EXISTING_RUNTIME.md)
- [Design](docs/DESIGN.md)
- [Requirements](docs/REQUIREMENTS.md)
- [Herdr plugin review](docs/PLUGIN_GUIDELINES_REVIEW.md)
- [Publishing and marketplace](docs/PUBLISHING.md)
- [Management-host proposal](docs/SESSION_MANAGEMENT_PROPOSAL.md)
- [Contributor instructions](agent.md)

The repository root owns [LICENSE](LICENSE) and [NOTICE](NOTICE). Package builds include them.
