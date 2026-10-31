# Management-host proposal

## Implemented

The plugin runs on the host that owns the Herdr server.
It uses AWS IAM credentials and saved connection records to manage remote terminal sessions.
The same connector can run on a development laptop or an EC2 management host.

## Target topology

```text
Laptop viewer -> persistent Herdr management host -> AgentCore workers
```

The management host owns Herdr state, local profiles, and connector processes.
Workers own application processes and use runtime-configured storage.
The runtime implementation is maintained in `agentcore-coding-runtimes`.

## Recovery boundaries

Reopening a Herdr client can resume viewing its server-owned panes.
Reattaching a cloud connection reuses its recorded live PTY.
Neither operation recreates a terminated worker conversation.
Conversation persistence and reconstruction are application concerns and are not implemented by this plugin.

## Future work

Qualify unattended management-host operation, identity renewal, host restart, and viewer disconnects.
Keep worker stop separate from management-host stop.
Do not add a user registry, Cognito deployment, or assistant-specific connector branches as part of that work.

See [the design](DESIGN.md) and [connection guide](CONNECT_EXISTING_RUNTIME.md).
