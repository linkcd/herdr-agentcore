# Publish the Herdr AgentCore plugin

## Requirements

Follow [Herdr's plugin contract](https://herdr.dev/tui/docs/plugins/) and [marketplace rules](https://herdr.dev/tui/docs/marketplace/).

The source repository must:

1. Be public, not a fork, and not archived.
2. Have the topic `herdr-plugin`.
3. Contain a parseable `herdr-plugin.toml` on its default branch. This plugin uses the repository root.
4. Include the files needed by the manifest build command.

The marketplace indexes repositories automatically every 30 minutes and rescans changed default-branch heads.
A listing is discovery, not a review or endorsement by Herdr. There is no separate registration API to call.

## Manifest and source installation

The stable plugin ID is `agentcore`. Its configuration and state directories are keyed by this ID.
Required metadata is `id`, `name`, `version`, and `min_herdr_version`.
The manifest declares Linux and macOS support and uses argv arrays for all commands.
The minimum supported Herdr version is `0.9.5`.

Herdr installs the source with Git and runs `uv sync --frozen --no-dev` in the managed checkout.
The build installs the connector into that checkout's `.venv`. It does not need AWS credentials or Herdr runtime context.
The manifest must remain unchanged during the build.
No wheel, PyPI release, GitHub release asset, or runtime repository is required for Herdr installation.

Documented prerequisites are Git, uv, Python 3.11+, and Herdr 0.9.5+.
Runtime commands use `HERDR_BIN_PATH` for Herdr calls and the injected config/state directories for user data.
Installed source directories contain program files, not credentials or durable connection records.

## Versioning

Use SemVer independently for the plugin and connection contract:

| Item | Current version | Location |
| --- | --- | --- |
| Plugin | `0.1.0` | `herdr-plugin.toml`, package metadata, and `herdr_agentcore.__version__` |
| Connection contract | `1.0.0` | Descriptor `version`, schema default, and producer/consumer version constants |
| Minimum Herdr | `0.9.5` | Manifest compatibility requirement |

Use plugin release tags such as `v0.1.0`. The marketplace displays the manifest version from the default branch.
The contract artifact is `connection-contract-1.0.0.zip`; its internal `v1/` directory identifies the protocol major version.
Changing the contract version does not require matching the plugin version number.
See [contract compatibility](../contracts/v1/README.md#semver-compatibility) before changing the interface.

## Validate source before publishing

Run from the repository root:

```bash
uv sync --frozen
uv run --frozen ruff check src scripts
uv run --frozen ruff format --check src scripts
HERDR_TEST_BINARY="$(command -v herdr)" uv run --frozen pytest -q --tb=short
uv run --frozen python scripts/check_publication.py
uv run --frozen python src/herdr_plugin/tests/repository_privacy.py
uv build --package herdr-agentcore
uv run --frozen python src/herdr_plugin/tests/check_distributions.py --dist dist
uv run --frozen python scripts/package_contract.py
```

Tests build a fresh source copy using the declared manifest command.
With `HERDR_TEST_BINARY`, they exercise Herdr's managed installer and updater against a local Git fixture in an isolated registry.
They do not contact a public fixture repository, alter the user's plugin installation, or create AWS sessions.

## Publish and discover

1. Choose the GitHub owner and repository name.
2. Review and commit the source, manifest, documentation, and lockfile.
3. Publish the repository's default branch. Verify that its root contains `herdr-plugin.toml`.
4. Add a repository description and the topic `herdr-plugin`.
5. Optionally create a SemVer release tag and attach the contract artifact.
6. Verify the published repository with:

   ```bash
   uv run --frozen python scripts/check_publication.py --github OWNER/REPO
   ```

The GitHub check is read-only. It checks visibility, fork/archive status, the topic, and default-branch manifest metadata.
It does not make a repository public, push code, create a release, or change topics.

An owner can add the topic with GitHub's repository settings or:

```bash
gh repo edit OWNER/REPO --add-topic herdr-plugin
```

Users install the published source with `herdr plugin install OWNER/REPO`.
Use `--ref TAG_OR_COMMIT` when validating a particular published revision.
Check the [marketplace](https://herdr.dev/plugins/) after its refresh cycle.
