# Plugin requirements

## Scope

Connect Herdr to already deployed AgentCore Shell runtimes.
Image builds, AWS deployment, storage administration, model selection, and application recovery belong to the runtime owner.

| ID | Requirement |
| --- | --- |
| F01 | Register an ARN and explicit launch argv directly or through a validated descriptor. |
| F02 | Derive region from the ARN and default the endpoint to `DEFAULT`. |
| F03 | Keep host AWS credential selection and recognition hints in local profiles. |
| F04 | Add compatible terminal assistants without connector branches or an assistant enum. |
| F05 | Record a launch attempt before sending it and never replay uncertain input. |
| F06 | Reattach only to the original runtime-session and shell binding. |
| F07 | Distinguish detach from confirmed whole-session stop. |
| F08 | Restore terminal settings and keep I/O, resize, and reconnect cancellable. |
| F09 | Persist records atomically, retain unknown recovery annotations, and enforce local locks. |
| F10 | Select an explicit profile before environment override before saved default. |
| F11 | Preserve existing profile snapshots and do not silently replace a missing default. |
| F12 | Use public Herdr APIs and keep display metadata separate from work-state detection. |
| C01 | Own a versioned JSON contract with shared conformance fixtures. |
| C02 | Export no runtime-specific application settings, credentials, or execution IDs. |
| C03 | Reject unknown descriptor fields, unsupported versions, and invalid argv. |
| C04 | Build the plugin without Node.js, CDK, or the runtime repository. |
| C05 | Package canonical schema and fixture files for independent runtime consumers. |
| P01 | Keep credentials, populated operational files, and transcripts out of Git. |
| P02 | Default tests make no AWS calls and do not affect the user's Herdr server. |
| P03 | Live probes use explicitly authorized targets and clean up only their own sessions. |

The descriptor and local saved-profile formats are separate.
See [the contract](../contracts/1.0.0/README.md) and [the design](DESIGN.md).
