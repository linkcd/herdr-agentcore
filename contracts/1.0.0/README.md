# AgentCore Shell connection contract

## Ownership and scope

The [Herdr AgentCore plugin](https://github.com/linkcd/herdr-agentcore) owns this specification, schema, and fixtures.
Runtime publishers implement the data format. They do not import plugin code.
The Python validator is an internal plugin module, `herdr_agentcore.contract`.
It is not a separately published package.

## Connection descriptor

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

The identifiers above are fictional. `/app/run.sh` is an example, not a plugin default.

| Field | Rule |
| --- | --- |
| `version` | Required stable SemVer string in major version 1. The producer emits `1.0.0`. |
| `transport` | Required constant `agentcore-shell-v1`. |
| `connection.runtime_arn` | Required runtime ARN. Endpoint ARNs and URLs are invalid. |
| `connection.command` | Required argument array. Supply the command implemented by the runtime image. |
| `connection.endpoint` | Optional qualifier. Defaults to `DEFAULT`. |

Derive the AWS region from the runtime ARN. Reject unknown fields at both object levels.
Command arguments must be nonempty strings of at most 4096 Unicode characters, without control characters.
Commands contain 1–64 arguments. The first argument must not start with `-`.
The sum of each argument's UTF-8 byte length plus one must not exceed 8192 bytes.
The JSON Schema cannot express that aggregate byte limit; implementations must check it separately.
Endpoint strings follow the same text limits as command arguments.

## Local plugin settings

The plugin selects host AWS credentials, a local profile name, and an optional Herdr recognition hint.
These values are not runtime export fields. The hint is an open string identifier, not an assistant enum.
New assistants require a valid runtime and command, not connector source changes.
The plugin creates runtime-session and shell IDs and stores them in local connection records.
Those IDs are not part of this deployment descriptor.

## Publishing and consuming

Publish this object directly or as the JSON string in a CDK output named `ConnectionDescriptor`.
The consumer validates the resolved ARN and launch command before registration.
An import does not execute the command. A new connection executes it once.

```python
from herdr_agentcore.contract import decode_descriptor

connection = decode_descriptor(document)
region = connection.region
```

The plugin also accepts CDK output documents through `decode_cdk_outputs(document, stack)`.
If the document contains multiple stacks, the caller must select a stack explicitly.

## SemVer compatibility

The contract uses SemVer independently of the Herdr plugin's manifest version.
Consumers accept stable `1.x.y` versions with the documented payload shape. Build metadata is permitted and does not affect compatibility.
Prereleases, other major versions, numeric versions, and incomplete version strings are rejected.
The `contracts/1.0.0/` directory identifies this exact contract release.
Keep each published release in its own `contracts/MAJOR.MINOR.PATCH/` directory.
The `agentcore-shell-v1` transport identifies the Shell protocol independently of descriptor SemVer.

- **Major:** incompatible fields, validation rules, or transport behavior. Because unknown fields are rejected, adding a wire field requires a major version unless consumers can already accept it.
- **Minor:** backward-compatible capabilities that preserve the accepted payload shape and behavior.
- **Patch:** compatible fixes and documentation corrections.

Local profile and connection-record format markers are internal storage versions, not contract SemVer values.

## Releases and conformance

[connection.schema.json](connection.schema.json) defines structure and field constraints.
[fixtures.json](fixtures.json) contains shared valid and invalid cases.
Publish both files with a tagged plugin release. Consumers pin the release and file checksums.
The release artifact is named `connection-contract-1.0.0.zip` and contains a `1.0.0/` directory.
Its `1.0.0/checksums.json` manifest declares `descriptor_version: "1.0.0"` and hashes every artifact file.
Normal builds use the checked-in pinned copies and do not fetch a moving branch.
Both implementations must pass the fixtures and aggregate command-size checks.

Plugin profiles and connection records use a separate local format.
Keep published descriptor versions stable. Use a new descriptor version for incompatible changes.
Unknown fields are rejected, so an added field can be incompatible even when it is optional.
Plugin package, runtime image, and descriptor versions are independent.
