"""Plugin-owned validation of the SemVer-versioned JSON connection contract."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

CONTRACT_VERSION = "1.0.0"
SUPPORTED_VERSION_PATTERN = (
    r"1\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)


def supports_version(value) -> bool:
    return isinstance(value, str) and re.fullmatch(SUPPORTED_VERSION_PATTERN, value) is not None


class UserError(Exception):
    """An actionable error that is safe to display without a traceback."""


def plain_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise UserError(f"{label} must be a non-empty string of at most 4096 characters.")
    if any(ord(c) < 32 or 127 <= ord(c) < 160 for c in value):
        raise UserError(f"{label} must not contain terminal control characters.")
    return value


def validate_command(command) -> list[str]:
    if not isinstance(command, list) or not 1 <= len(command) <= 64:
        raise UserError("command is required and must be an argv array with 1–64 elements.")
    for arg in command:
        plain_text(arg, "command argument")
    if sum(len(arg.encode()) + 1 for arg in command) > 8192:
        raise UserError("Launch command is too long (maximum 8 KiB).")
    if command[0].startswith("-"):
        raise UserError("The command executable must not start with '-'.")
    return list(command)


def runtime_region(arn: str) -> str:
    if not isinstance(arn, str):
        raise UserError("runtime_arn must be a string.")
    match = re.fullmatch(
        r"arn:(aws|aws-cn|aws-us-gov):bedrock-agentcore:([a-z0-9-]+):"
        r"([0-9]{12}):runtime/([a-zA-Z0-9_-]+)",
        arn,
    )
    if not match:
        raise UserError("Expected an AgentCore runtime ARN, not an endpoint ARN or URL.")
    return match[2]


@dataclass(frozen=True)
class ConnectionSpec:
    runtime_arn: str
    command: list[str]
    endpoint: str = "DEFAULT"

    @property
    def region(self) -> str:
        return runtime_region(self.runtime_arn)

    @classmethod
    def from_dict(cls, data: dict) -> ConnectionSpec:
        if not isinstance(data, dict):
            raise UserError("A runtime connection must be a JSON object.")
        allowed = {"runtime_arn", "command", "endpoint"}
        if set(data) - allowed:
            raise UserError("Unknown runtime connection fields.")
        arn = data.get("runtime_arn", "")
        runtime_region(arn)
        command = validate_command(data.get("command"))
        endpoint = plain_text(data.get("endpoint", "DEFAULT"), "endpoint")
        return cls(arn, list(command), endpoint)


def encode_descriptor(connection: ConnectionSpec) -> dict:
    fields = {"runtime_arn": connection.runtime_arn, "command": list(connection.command)}
    if connection.endpoint != "DEFAULT":
        fields["endpoint"] = connection.endpoint
    ConnectionSpec.from_dict(fields)
    return {"version": CONTRACT_VERSION, "transport": "agentcore-shell-v1", "connection": fields}


def decode_descriptor(data: dict) -> ConnectionSpec:
    if not isinstance(data, dict) or not supports_version(data.get("version")):
        raise UserError("Unsupported connection descriptor; expected stable 1.x.y SemVer.")
    if set(data) != {"version", "transport", "connection"}:
        raise UserError("A descriptor must contain only version, transport, and connection.")
    if data["transport"] != "agentcore-shell-v1":
        raise UserError("Unsupported connection transport; expected agentcore-shell-v1.")
    return ConnectionSpec.from_dict(data["connection"])


def decode_cdk_outputs(data: dict, stack: str | None = None) -> ConnectionSpec:
    """Read the resolved descriptor in a standard CDK --outputs-file document."""
    if not isinstance(data, dict) or not data:
        raise UserError("CDK outputs must contain at least one stack.")
    if stack is None:
        if len(data) != 1:
            raise UserError("CDK outputs contain multiple stacks. Supply --stack explicitly.")
        stack = next(iter(data))
    outputs = data.get(stack)
    if not isinstance(outputs, dict):
        raise UserError("The selected stack is not present in the CDK outputs.")
    descriptor = outputs.get("ConnectionDescriptor")
    if not isinstance(descriptor, str):
        raise UserError("The stack has no ConnectionDescriptor output.")
    try:
        return decode_descriptor(json.loads(descriptor))
    except json.JSONDecodeError as exc:
        raise UserError("ConnectionDescriptor must contain valid JSON.") from exc
