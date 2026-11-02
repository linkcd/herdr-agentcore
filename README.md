# Herdr AgentCore plugin

Connect Herdr terminals to interactive assistants hosted in Amazon Bedrock AgentCore Runtime.
The plugin manages terminal transport, saved connections, reconnect, detach, and stop.
It does not build images or deploy AWS resources.

Source repository: [linkcd/herdr-agentcore](https://github.com/linkcd/herdr-agentcore).
Runtime images and CDK infrastructure are maintained independently in [linkcd/agentcore-coding-assistant](https://github.com/linkcd/agentcore-coding-assistant).

## Quick start: connect from an EC2 host

Use this path when you have the host from [`ec2_herdr_host`](https://github.com/linkcd/agentcore-coding-assistant/tree/main/src/ec2_herdr_host) and a runtime from [`agentcore_runtime`](https://github.com/linkcd/agentcore-coding-assistant/tree/main/src/agentcore_runtime).
The host's first boot installs Herdr, uv, and this plugin. You only connect the plugin to your runtime.

### 1. Collect two values from the runtime

| Value | Where to find it |
| --- | --- |
| Runtime ARN | The `RuntimeArn` output of the runtime deployment. The same ARN is in the `ConnectionDescriptor` output. |
| Launch command | The `command` in the same `ConnectionDescriptor`. The sample OpenCode and Codex images use `["/app/run.sh"]`. |

### 2. Allow the host to open a terminal in the runtime

The plugin signs its requests with the host's AWS identity (the EC2 instance role).
That role needs these permissions on your runtime ARN:

- `bedrock-agentcore:InvokeAgentRuntimeCommandShell` to open a terminal.
- `bedrock-agentcore:StopRuntimeSession` to stop a session. It is optional if you never stop sessions from Herdr.

Grant them on the runtime ARN and on `RUNTIME_ARN/runtime-endpoint/DEFAULT` (use your endpoint name if it is not `DEFAULT`).
AgentCore checks both resources.

With the `ec2_herdr_host` stack, set `AGENTCORE_RUNTIME_ARN` in its `.env` to the `RuntimeArn` and redeploy. The stack then adds exactly this policy.
Without it, the role allows only the Claude model, and the connection fails with an HTTP 403 (`AccessDenied`).

### 3. Open the host and start Herdr

1. Run the `SessionCommand` output of the `ec2_herdr_host` stack on your laptop. It opens a Bash terminal on the host.
2. Check that the plugin is there: `herdr plugin list` must show `agentcore`.
   If it does not, run `herdr plugin install linkcd/herdr-agentcore --yes`.
3. Run `herdr`. Press Enter to close the welcome message. You now have a workspace with a terminal pane.

### 4. Save the connection (one time)

In that Herdr terminal pane, run:

```bash
herdr plugin action invoke agentcore.setup
```

An **AgentCore setup** pane opens and asks these questions:

| Question | What to enter |
| --- | --- |
| Profile name | Any short name, for example `my-agent`. Press Enter to use `default`. |
| Runtime ARN | The `RuntimeArn` from step 1. |
| AWS profile | Leave blank. The host uses its instance role. |
| Runtime endpoint | Leave blank to use `DEFAULT`. |
| Herdr agent kind | `opencode` or `codex`, to match the runtime image. Leave blank for a plain terminal. |
| Launch argv as JSON | The launch command from step 1, for example `["/app/run.sh"]`. |

The answers are saved as a profile in `config.json` in the folder printed by `herdr plugin config-dir agentcore`.
The region comes from the ARN. The first profile you save becomes the default.
The file holds no credentials. It survives plugin updates and uninstall, so you set up once per host.

### 5. Start the cloud agent

```bash
herdr plugin action invoke agentcore.new
```

A new pane opens a terminal inside your runtime and starts the assistant.
The first start can take a short while because AgentCore creates the session.
The saved default profile is used.

### 6. Detach, come back, and stop

| Goal | How |
| --- | --- |
| Leave the agent running | Press Ctrl+] then `d`, or close the pane. |
| Return to it | `herdr plugin action invoke agentcore.attach`, then pick the session. |
| See saved sessions | `herdr plugin action invoke agentcore.sessions` |
| End it and free the compute | Detach, then `herdr plugin action invoke agentcore.stop`, then type the session name to confirm. |

Closing your Session Manager terminal does not stop Herdr or the agent. Run `herdr` on the host again to return.
Reattaching works only while the original AgentCore session is alive. After it expires, start a new one with `agentcore.new`.

### If something goes wrong

| Message or symptom | Likely cause and fix |
| --- | --- |
| `server_not_running` | Herdr is not running. Run `herdr` first, then invoke the action from a Herdr pane. |
| HTTP 403 or `AccessDeniedException` | The host role lacks the permission from step 2, or it is scoped to a different runtime ARN or endpoint name. |
| `NoCredentialsError` | The host has no AWS credentials. Check that the instance has its role. If you typed an AWS profile in setup, make sure it exists on the host, or run setup again and leave it blank. |
| `ResourceNotFoundException` | The runtime ARN is wrong or belongs to another region or account. |
| Shell closes at once | The launch command does not exist in the image. Check it against the runtime's `ConnectionDescriptor`. |
| A plain terminal opens, not the agent | The agent kind is blank or unsupported. The terminal still works. |
| Wrong profile saved | Run `agentcore.setup` again with the same name and answer `y` to replace it. |

## Repository layout

```text
herdr-plugin.toml                 Herdr actions and pane entrypoints
src/herdr_plugin/                Python connector package and tests
contracts/1.0.0/                 Canonical JSON schema and conformance cases
scripts/package_contract.py      Contract release-artifact builder
docs/                            Connector design and operation guides
```

## Install from GitHub

Use macOS or Linux, Git, Python 3.11+, uv, and Herdr 0.9.5+.
The management host needs AWS permission to invoke the selected runtime's Shell API.
The runtime must contain a working interactive launch command.
Installation downloads locked Python dependencies. Herdr does not install system toolchains.

Once the plugin source is published on the repository's default branch, install it with:

```bash
herdr plugin install linkcd/herdr-agentcore
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
The plugin owns [the contract specification](contracts/1.0.0/README.md) and its internal validator.
Runtime publishers consume pinned schema/fixture artifacts, not plugin source code.
Contract releases use full SemVer directories and archive prefixes, such as `contracts/1.0.0/` and `1.0.0/`.

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
