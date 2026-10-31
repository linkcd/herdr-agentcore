# Connect an existing AgentCore runtime

## Required information

The runtime owner supplies:

1. The runtime ARN.
2. The explicit command to launch inside its Shell session.
3. A non-default endpoint qualifier, if applicable.

The region is derived from the ARN. The endpoint defaults to `DEFAULT`.
The target must support interactive AgentCore Shell connections and contain the declared command.
The plugin does not install an assistant or infer a launcher.

Host AWS credentials and the optional Herdr recognition hint are local choices.
Runtime model credentials, configuration, storage, and work-health reporting belong to the runtime owner.

## Install on the management host

Use macOS or Linux, Git, Python 3.11+, uv, and Herdr 0.9.5+.
For a remote Herdr server, install the plugin on that server's host.

For a published revision of [linkcd/herdr-agentcore](https://github.com/linkcd/herdr-agentcore), run:

```bash
herdr plugin install linkcd/herdr-agentcore
herdr plugin action invoke agentcore.setup
```

The setup action runs inside Herdr with the correct installed directory and config/state paths.
Supply the runtime ARN, launch argv as JSON, and optional local settings.

For local development, run from the source repository:

```bash
uv sync --frozen --no-dev
herdr plugin link "$PWD"
```

The host identity needs Shell invocation permission for the runtime.
Stop operations also need `bedrock-agentcore:StopRuntimeSession`.
Use an existing AWS credential chain or a named host AWS profile.

## Register a descriptor

The direct CLI examples below assume a source checkout. Managed-install users can use the setup action above.

```bash
.venv/bin/herdr-agentcore configure \
  --connection-file /path/to/connection.json \
  --profile my-agent \
  --agent-kind opencode \
  --config-dir "$(herdr plugin config-dir agentcore)"
```

For a CDK output file, replace `--connection-file PATH` with `--cdk-outputs PATH --stack NAME`.
The selected stack must contain a JSON string output named `ConnectionDescriptor`.
See [the descriptor specification](../contracts/1.0.0/README.md).

`--agent-kind` is a local recognition hint, not a runtime setting or model selector.
Omit it for an ordinary terminal, or use `--agent-kind terminal` to clear it explicitly.
The plugin accepts open string identifiers; supported detection rules are owned by Herdr.
Adding a different terminal assistant does not require connector changes.

## Register directly

```bash
.venv/bin/herdr-agentcore configure \
  --runtime-arn "$RUNTIME_ARN" \
  --profile my-agent \
  --agent-kind opencode \
  --config-dir "$(herdr plugin config-dir agentcore)" \
  --command /app/run.sh
```

Replace the ARN and command with the runtime owner's values. Put `--command` last.
Add `--endpoint NAME` only for a different qualifier.
Add `--aws-profile NAME` only to select a named host credential profile.
Use `--replace` to replace an existing local profile deliberately.

## Select and launch

```bash
.venv/bin/herdr-agentcore set-default my-agent \
  --config-dir "$(herdr plugin config-dir agentcore)"
herdr plugin action invoke agentcore.new
```

For an explicit launch selection, run `.venv/bin/herdr-agentcore action new --profile NAME`.
The connector records its launch attempt before sending the command.
It never replays an uncertain launch or uncertain terminal input.

## Detach and reattach

1. Press Ctrl+] followed by `d`, or close the cloud-agent pane.
2. Run `herdr plugin action invoke agentcore.attach`.
3. Select the saved connection.

Attachment reuses the recorded runtime-session and shell IDs.
It requires the original PTY after a previous launch.
If compute expired, attachment reports failure instead of silently starting another assistant.
Conversation recovery is outside this connector's scope.

Closing only the terminal client displaying Herdr can leave the Herdr server and connector running.
The connector sends WebSocket pings every 20 seconds while connected.
Runtime expiry depends on the deployment's lifecycle settings and platform activity accounting.

## Stop

Detach first, then run:

```bash
herdr plugin action invoke agentcore.stop
```

Select the connection and confirm its name.
Stop targets the entire runtime session and all its processes.
The saved `stopped` state means AWS accepted the request; no completion waiter exists.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Missing command | Obtain explicit launch argv from the runtime owner. |
| Access denied | Check the management host's IAM identity and runtime permissions. |
| Missing profile | Supply the intended Herdr config directory or select a saved profile. |
| Original PTY missing | The shell ended or compute expired. Start new work explicitly. |
| Ordinary terminal instead of an agent | Configure a local recognition hint supported by Herdr. |
| Model or tool failure after connection | Check the runtime's application configuration and execution role. |

See the [connector README](../src/herdr_plugin/README.md) for package commands.
