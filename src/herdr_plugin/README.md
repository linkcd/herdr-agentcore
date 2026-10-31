# Herdr AgentCore connector

## Purpose

Connect Herdr to an already deployed AgentCore terminal runtime.
The package is `herdr-agentcore`; its module is `herdr_agentcore`.
It owns profiles, runtime-session and shell IDs, terminal transport, reconnect, detach, and stop.

Runtime images and infrastructure are maintained in the separate `agentcore-coding-runtimes` repository.
This package has no dependency on that repository or an external contract implementation package.
Its production dependencies are the AgentCore SDK and WebSocket client.

## Configure

Installed users run `herdr plugin action invoke agentcore.setup` from a Herdr workspace.
Herdr supplies the installed root and external config/state directories automatically.

For a local source checkout, run from the repository root:

```bash
uv sync --frozen --no-dev
herdr plugin link "$PWD"
.venv/bin/herdr-agentcore configure \
  --connection-file /path/to/connection.json \
  --profile my-agent \
  --agent-kind opencode \
  --config-dir "$(herdr plugin config-dir agentcore)"
```

The runtime descriptor supplies an ARN, explicit launch command, and optional endpoint.
The plugin derives the AWS region from the ARN.
`--agent-kind` selects only a local Herdr recognition hint. Omit it for an ordinary terminal.
Use `--aws-profile` only for a named host credential profile. Otherwise, use the normal AWS credential chain.

Use `--cdk-outputs PATH --stack NAME` to import a CDK output document.
Use `--runtime-arn ARN --command EXECUTABLE ARGUMENTS...` for direct registration.
Put `--command` last. Commands have no inferred default.
An explicit `--command` can override a valid imported descriptor's command.

## Connection operations

```bash
.venv/bin/herdr-agentcore action new --profile my-agent
herdr plugin action invoke agentcore.attach
herdr plugin action invoke agentcore.sessions
herdr plugin action invoke agentcore.stop
```

Selection order is explicit profile, `HERDR_AGENTCORE_PROFILE`, then saved default.
The first profile becomes default; later imports preserve that choice.
Detach with Ctrl+] followed by `d`.
Reattachment uses the original runtime-session and shell IDs and does not launch another assistant.
Stop requires confirmation and targets the whole runtime session.

Saved configuration and connection records stay in Herdr's external config/state directories.
When invoking the executable outside a plugin-managed pane, supply `--config-dir` and `--state-dir` for the intended Herdr installation.
Local statuses are records of previous observations, not a live inventory of AWS compute.

## Contract ownership

The [versioned JSON contract](../../contracts/v1/README.md) is the boundary with runtime publishers.
`herdr_agentcore.contract` validates imported descriptors using standard-library code.
`models.Profile` adds local recognition and host-credential settings.
Its optional `runtime_profile` source label describes the local connection and is not accepted in runtime exports.

The connector has no assistant-name enum. Recognition requires support in Herdr; it does not affect the generic Shell transport.
Publishers do not need to import this package to produce a descriptor.

## Checks

```bash
uv run --frozen pytest src/herdr_plugin/tests -q --tb=short
uv build --package herdr-agentcore
```

Default tests make no AWS calls. Set `HERDR_TEST_BINARY` to include isolated Herdr installation checks.
Live probes require an explicitly authorized target and stop only their own disposable sessions.
The root LICENSE and NOTICE are included in package distributions.

See the [connection guide](../../docs/CONNECT_EXISTING_RUNTIME.md), [design](../../docs/DESIGN.md), and [repository instructions](../../agent.md).
