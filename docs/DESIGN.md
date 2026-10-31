# Connector design

## Architecture

```text
Herdr pane
  -> Python connector
  -> SigV4-authenticated AgentCore Shell WebSocket
  -> remote terminal process
```

Herdr owns workspaces, tabs, panes, and agent recognition.
The plugin owns connection profiles, runtime-session and shell bindings, terminal I/O, reconnect, detach, and stop.
The independent runtime repository owns application images, deployment, storage, and work-health reporting.

## Minimal deployment boundary

The runtime publishes a [versioned JSON descriptor](../contracts/1.0.0/README.md).
Required connection values are runtime ARN and explicit launch argv. The endpoint defaults to `DEFAULT`.
The consumer derives region from the ARN. Format markers are constants, not deployment choices.

The plugin owns the schema, fixtures, and internal Python validator.
Runtime builds use pinned schema/fixture copies and their own producer implementation.
No shared implementation package or sibling checkout is required.

Herdr recognition, host AWS credentials, profile names, and execution IDs remain local.
The optional saved `runtime_profile` label has no transport behavior and is not exported by a runtime.
An assistant-independent connector treats the command as argv and forwards terminal bytes.

## Implementation map

| Module | Responsibility |
| --- | --- |
| `contract.py` | Validate minimal JSON descriptors and CDK output envelopes. |
| `models.py` | Validate local profiles and connection records. |
| `storage.py` | Atomic writes, directory sync, and local locks. |
| `cli.py` | Registration, selection, menus, and stop confirmation. |
| `sessions.py` | Create, attach, and stop use cases. |
| `agentcore.py` | AWS credentials, signing, transport, and stop requests. |
| `connector.py` | At-most-once launch, shell frames, and bounded reconnect. |
| `terminal.py` | Raw terminal mode and cancellable nonblocking I/O. |
| `herdr.py` | Public plugin APIs and display metadata. |

## Launch and recovery

Before sending a launch command, persist the attempted state.
After an uncertain transmission, require inspection of the original shell; do not resend the command.
Attachment checks the Shell confirmation's `reconnected` field.
The original PTY must exist after any prior launch attempt.

Detach closes the WebSocket without requesting shell shutdown.
SIGTERM, SIGHUP, terminal EOF, and Ctrl+] d initiate detach.
Stop is a separate, confirmed operation targeting the complete runtime session.

Retry only classified transient failures inside the reconnect window.
An explicit retryable conflict can be retried. An unknown HTTP 409 cannot.
Pause input during reconnect and never replay buffered input from an outage.

## Identity and storage

Use the AWS SDK credential provider chain and refresh credentials for each new handshake.
Keep signed URLs and credentials out of records and logs.
Saved profiles retain their target, command, and local recognition choice for existing sessions.
Changing a default profile affects future sessions only.

Local records are not an authoritative AWS compute inventory.
Persisted runtime-session IDs cannot restore a terminated process or its conversation.
Runtime-owned durable files and application recovery are separate from connector state.

## Activity and lifecycle

Herdr's working/idle detection and AgentCore work-health reporting are separate.
The connector publishes transport metadata only and leaves agent-state detection to Herdr.
WebSocket keepalive pings run every 20 seconds without checking agent work state.
AWS documents that WebSocket ping/pong traffic affects idle accounting.
The deployment's maximum compute lifetime still applies.

## Validation

Default tests cover transport, framing, commands, records, selection, and descriptor conformance without AWS calls.
The optional Herdr installation test uses an isolated session and registry.
Live probes require explicit authorization, create disposable sessions, and stop only those sessions.
