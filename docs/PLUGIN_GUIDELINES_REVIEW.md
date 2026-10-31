# Herdr plugin guideline review

## Scope

This review uses the [Herdr plugin documentation](https://herdr.dev/tui/docs/plugins/), [marketplace rules](https://herdr.dev/tui/docs/marketplace/), and the Herdr 0.9.5 CLI.
Herdr requires a root manifest and executable argv entrypoints. It does not prescribe a source layout.
The current repository contains only the plugin implementation and its versioned connection specification.

## Extension contract

| Convention | Implementation |
| --- | --- |
| Root manifest | [herdr-plugin.toml](../herdr-plugin.toml) declares metadata, actions, and pane entrypoints. |
| Argument arrays | Commands use argv arrays. Remote launch arguments are quoted explicitly. |
| Public APIs | [herdr.py](../src/herdr_plugin/herdr_agentcore/herdr.py) uses the public CLI and injected `HERDR_BIN_PATH`. |
| Invocation context | Pane creation uses explicit pane/workspace context. |
| External user state | Profiles and records use Herdr's config/state directories and local locks. |
| Owned schema | [models.py](../src/herdr_plugin/herdr_agentcore/models.py) validates local records; [the contract](../contracts/v1/README.md) defines runtime exports. |
| Build isolation | `uv sync --frozen --no-dev` installs only the connector and its dependencies. |
| Long-running work | Connectors run in panes and restore terminal state on exit. |
| Agent recognition | A local optional hint sets `HERDR_AGENT`. The connector does not contain an assistant enum. |
| Transport metadata | Connection status uses `pane report-metadata`, not artificial agent work events. |

## State and lifecycle

Plugins run with the management host user's permissions.
The connector uses that host's AWS credential chain and does not copy worker credentials.
Detach closes transport. Stop is a separate confirmed request for the whole runtime session.
Closing a Herdr viewer can leave its persistent server and connector processes running.

Herdr recognition and runtime work-health reporting are separate.
A connected wrapper does not prove the remote application's health or permission to answer an unfamiliar prompt.
See [the design](DESIGN.md) for transport and recovery boundaries.

## Build and publication

The connector builds one Python wheel and source distribution.
Root LICENSE and NOTICE files are included in both.
The contract schema and fixtures are packaged as a separate data artifact, not a shared code package.
Runtime deployment and image builds are maintained in `agentcore-coding-runtimes`.

```bash
HERDR_TEST_BINARY="$(command -v herdr)" uv run --frozen pytest \
  src/herdr_plugin/tests/test_plugin.py src/herdr_plugin/tests/test_herdr_manifest.py -q --tb=short
uv build --package herdr-agentcore
uv run --frozen python src/herdr_plugin/tests/check_distributions.py --dist dist
uv run --frozen python scripts/package_contract.py
uv run --frozen python scripts/check_publication.py
```

The optional manifest test uses an isolated, disabled plugin registry.
It does not modify the user's registry or start a remote agent.
Source-build tests validate the declared build command without runtime context.
The optional managed installer test exercises installation and update with local Git transport and an isolated registry.
Public repository discovery is checked separately with `scripts/check_publication.py --github OWNER/REPO`.
Remote publication and marketplace registration require an explicit request.
