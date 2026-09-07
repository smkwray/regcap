from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


class ConfigError(ValueError):
    """Raised when project configuration is malformed."""


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a mapping: {path}")
    return data


def load_mechanisms(config_dir: Path = CONFIG_DIR) -> list[dict[str, Any]]:
    data = load_yaml(config_dir / "mechanisms.yml")
    mechanisms = data.get("mechanisms")
    if not isinstance(mechanisms, list) or not mechanisms:
        raise ConfigError("mechanisms.yml must define a nonempty mechanisms list")
    for item in mechanisms:
        if not isinstance(item, dict):
            raise ConfigError("Each mechanism must be a mapping")
    return mechanisms


def load_source_contracts(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    data = load_yaml(config_dir / "source_contracts.yml")
    contracts = data.get("contracts")
    if not isinstance(contracts, dict) or not contracts:
        raise ConfigError("source_contracts.yml must define a nonempty contracts mapping")
    return data


def load_variables(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    data = load_yaml(config_dir / "variables.yml")
    variables = data.get("variables")
    if not isinstance(variables, dict) or not variables:
        raise ConfigError("variables.yml must define a nonempty variables mapping")
    return data


def validate_config(config_dir: Path = CONFIG_DIR) -> list[str]:
    messages: list[str] = []
    mechanisms = load_mechanisms(config_dir)
    contracts_data = load_source_contracts(config_dir)
    variables = load_variables(config_dir)["variables"]

    mechanism_ids = [row.get("mechanism_id") for row in mechanisms]
    if len(mechanism_ids) != len(set(mechanism_ids)):
        raise ConfigError("mechanism_id values must be unique")

    required_columns = {
        "mechanism_id",
        "mechanism_label",
        "research_function",
        "primary_existing_project",
        "supporting_projects",
        "public_data_sources",
        "frequency",
        "cleanest_estimand",
        "identification_leverage",
        "tdc_connection",
        "claim_boundary_safe",
        "claim_boundary_unsafe",
        "go_no_go_recommendation",
        "implementation_priority",
    }
    contracts = contracts_data["contracts"]
    for row in mechanisms:
        missing = required_columns.difference(row)
        if missing:
            raise ConfigError(f"{row.get('mechanism_id', '<unknown>')} missing fields: {sorted(missing)}")
        if row["primary_existing_project"] not in contracts:
            raise ConfigError(f"{row['mechanism_id']} references unknown primary project {row['primary_existing_project']}")
        if not isinstance(row["supporting_projects"], list):
            raise ConfigError(f"{row['mechanism_id']} supporting_projects must be a list")
        if not isinstance(row["public_data_sources"], list):
            raise ConfigError(f"{row['mechanism_id']} public_data_sources must be a list")
        int(row["implementation_priority"])

    for project, contract in contracts.items():
        artifacts = contract.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ConfigError(f"source contract {project} must list artifacts")
        for artifact in artifacts:
            for key in ("path", "destination", "required", "notes"):
                if key not in artifact:
                    raise ConfigError(f"source contract {project} artifact missing {key}")
            schema = artifact.get("schema")
            if schema is not None:
                if not isinstance(schema, dict):
                    raise ConfigError(f"source contract {project} artifact schema must be a mapping")
                expected_hash = schema.get("sha256")
                if expected_hash is not None and (
                    not isinstance(expected_hash, str) or len(expected_hash) != 64
                    or any(char not in "0123456789abcdef" for char in expected_hash)
                ):
                    raise ConfigError(f"source contract {project} has invalid sha256")
                artifact_format = schema.get("format")
                if artifact_format not in {"csv", "json", "markdown"}:
                    raise ConfigError(f"source contract {project} artifact has unknown schema format {artifact_format}")
                if artifact_format == "csv" and not isinstance(schema.get("required_columns"), list):
                    raise ConfigError(f"source contract {project} csv artifact must list required_columns")
                if artifact_format == "json" and not isinstance(schema.get("required_keys"), list):
                    raise ConfigError(f"source contract {project} json artifact must list required_keys")
                if artifact_format == "markdown" and not isinstance(schema.get("required_heading"), str):
                    raise ConfigError(f"source contract {project} markdown artifact must set required_heading")

    for name, variable in variables.items():
        if "description" not in variable or "claim_boundary" not in variable:
            raise ConfigError(f"variable {name} must include description and claim_boundary")

    messages.append(f"Validated {len(mechanisms)} mechanisms")
    messages.append(f"Validated {len(contracts)} sibling source contracts")
    messages.append(f"Validated {len(variables)} variable definitions")
    return messages
