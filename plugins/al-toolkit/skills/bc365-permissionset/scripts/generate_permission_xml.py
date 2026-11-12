#!/usr/bin/env python3
"""Generate import-ready Business Central tenant permission set XML."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


SYSTEM_APP_ID = "{63ca2fa4-4f03-4f2b-a480-172fef340d3f}"
BASE_APP_ID = "{437dbf0e-84ff-417a-965d-ed2bb9650972}"
ROLE_ID_MAX_LENGTH = 20

COMMON_SYSTEM_SET_APP_IDS = {
    "LOGIN": SYSTEM_APP_ID,
    "SYSTEM APP - BASIC": SYSTEM_APP_ID,
    "D365 BASIC": BASE_APP_ID,
    "D365 CUSTOMER, EDIT": BASE_APP_ID,
    "D365 CUSTOMER, VIEW": BASE_APP_ID,
    "D365 ITEM, EDIT": BASE_APP_ID,
    "D365 ITEM, VIEW": BASE_APP_ID,
    "D365 SALES DOC, EDIT": BASE_APP_ID,
    "D365 SALES DOC, POST": BASE_APP_ID,
    "D365 SALES DOC, VIEW": BASE_APP_ID,
    "D365 PURCH DOC, EDIT": BASE_APP_ID,
    "D365 PURCH DOC, POST": BASE_APP_ID,
    "D365 PURCH DOC, VIEW": BASE_APP_ID,
}

OBJECT_TYPES = {
    "Table Data",
    "Table",
    "Page",
    "Report",
    "Codeunit",
    "Query",
    "XMLport",
    "System",
}

PERMISSION_FIELDS = (
    "ReadPermission",
    "InsertPermission",
    "ModifyPermission",
    "DeletePermission",
    "ExecutePermission",
)

SECURITY_SENSITIVE_TABLES = {
    9000,
    9001,
    9002,
    9003,
    9004,
    2000000053,
    2000000054,
    2000000055,
}


class PermissionXmlError(ValueError):
    pass


def normalize_role_id(value: str) -> str:
    role_id = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").upper()
    role_id = re.sub(r"_+", "_", role_id)
    if not role_id:
        raise PermissionXmlError("RoleID cannot be blank.")
    if role_id == "SUPER":
        raise PermissionXmlError("Refusing to generate SUPER permission set.")
    if len(role_id) > ROLE_ID_MAX_LENGTH:
        role_id = role_id[:ROLE_ID_MAX_LENGTH].rstrip("_")
    return role_id


def child(parent: ET.Element, tag: str, text: str | int) -> ET.Element:
    node = ET.SubElement(parent, tag)
    node.text = str(text)
    return node


def load_spec(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        spec = json.load(handle)
    if not isinstance(spec, dict):
        raise PermissionXmlError("Input JSON must be an object.")
    return spec


def normalize_includes(spec: dict[str, Any]) -> list[dict[str, str]]:
    includes = spec.get("includes", [])
    if includes is None:
        includes = []
    if not isinstance(includes, list):
        raise PermissionXmlError("includes must be a list.")

    normalized: list[dict[str, str]] = []
    seen = set()

    def add_include(item: str | dict[str, Any]) -> None:
        if isinstance(item, str):
            role_id = item.strip().upper()
            app_id = COMMON_SYSTEM_SET_APP_IDS.get(role_id)
            if not app_id:
                raise PermissionXmlError(
                    f"Unknown app ID for included permission set '{item}'. "
                    "Pass an object with role_id and app_id."
                )
        elif isinstance(item, dict):
            role_id = str(item.get("role_id", item.get("RoleID", ""))).strip().upper()
            app_id = str(item.get("app_id", item.get("AppID", ""))).strip()
            if not role_id or not app_id:
                raise PermissionXmlError("include objects require role_id and app_id.")
        else:
            raise PermissionXmlError("includes entries must be strings or objects.")

        if role_id == "SUPER":
            raise PermissionXmlError("Refusing to include SUPER permission set.")
        key = (role_id, app_id.lower())
        if key not in seen:
            normalized.append({"role_id": role_id, "app_id": app_id})
            seen.add(key)

    add_include("LOGIN")
    for include in includes:
        add_include(include)

    return normalized


def permission_value(value: Any) -> str | None:
    if value in (None, "", False):
        return None
    if value is True:
        return "Yes"
    text = str(value).strip()
    if not text:
        return None
    lookup = {
        "yes": "Yes",
        "true": "Yes",
        "1": "Yes",
        "indirect": "Indirect",
    }
    normalized = lookup.get(text.lower())
    if not normalized:
        raise PermissionXmlError(f"Unsupported permission value '{value}'.")
    return normalized


def normalize_permissions(spec: dict[str, Any], allow_sensitive: bool) -> list[dict[str, Any]]:
    permissions = spec.get("permissions", [])
    if permissions is None:
        permissions = []
    if not isinstance(permissions, list):
        raise PermissionXmlError("permissions must be a list.")

    normalized = []
    for index, item in enumerate(permissions, start=1):
        if not isinstance(item, dict):
            raise PermissionXmlError(f"permissions[{index}] must be an object.")

        object_type = str(item.get("object_type", item.get("ObjectType", ""))).strip()
        if object_type not in OBJECT_TYPES:
            raise PermissionXmlError(f"Unsupported ObjectType '{object_type}' in permissions[{index}].")

        try:
            object_id = int(item.get("object_id", item.get("ObjectID")))
        except (TypeError, ValueError):
            raise PermissionXmlError(f"permissions[{index}] requires numeric object_id.") from None

        values = {
            field: permission_value(item.get(field, item.get(field[0].lower() + field[1:])))
            for field in PERMISSION_FIELDS
        }
        values = {field: value for field, value in values.items() if value}
        if not values:
            raise PermissionXmlError(f"permissions[{index}] requires at least one permission field.")

        if (
            object_type == "Table Data"
            and object_id in SECURITY_SENSITIVE_TABLES
            and not allow_sensitive
            and any(values.get(field) == "Yes" for field in ("InsertPermission", "ModifyPermission", "DeletePermission"))
        ):
            raise PermissionXmlError(
                f"Refusing write permissions on security-sensitive table {object_id}. "
                "Pass allow_sensitive_security_permissions=true only when explicitly approved."
            )

        normalized.append({"object_type": object_type, "object_id": object_id, "values": values})

    return normalized


def build_xml(spec: dict[str, Any]) -> str:
    role_name = str(spec.get("role_name", spec.get("RoleName", ""))).strip()
    if not role_name:
        raise PermissionXmlError("role_name is required.")

    role_id_input = str(spec.get("role_id", spec.get("RoleID", role_name))).strip()
    role_id = normalize_role_id(role_id_input)
    assignable = "Yes" if spec.get("assignable", True) not in (False, "No", "no", "false", "False", 0) else "No"
    # Strict opt-in: bool("false") is True, so only explicit true values unlock the guard.
    allow_sensitive = spec.get("allow_sensitive_security_permissions", False) in (True, "true", "True", "yes", "Yes")

    includes = normalize_includes(spec)
    permissions = normalize_permissions(spec, allow_sensitive)

    root = ET.Element("PermissionSets", {"Version": "2.0"})
    permission_set = ET.SubElement(
        root,
        "TenantPermissionSet",
        {"RoleID": role_id, "RoleName": role_name, "Assignable": assignable},
    )

    for include in includes:
        rel = ET.SubElement(permission_set, "TenantPermissionSetRel")
        child(rel, "ObjectType", "Include")
        child(rel, "ObjectRelatedScope", "System")
        child(rel, "ObjectRelatedRoleId", include["role_id"])
        child(rel, "ObjectRelatedAppId", include["app_id"])

    for permission in permissions:
        node = ET.SubElement(permission_set, "TenantPermission")
        child(node, "ObjectType", permission["object_type"])
        child(node, "ObjectID", permission["object_id"])
        for field in PERMISSION_FIELDS:
            if field in permission["values"]:
                child(node, field, permission["values"][field])
        child(node, "PermissionType", "Include")

    rough_xml = ET.tostring(root, encoding="utf-8")
    parsed = xml.dom.minidom.parseString(rough_xml)
    pretty = parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    return "\n".join(line for line in pretty.splitlines() if line.strip()) + "\n"


def validate_xml(xml_text: str) -> None:
    root = ET.fromstring(xml_text.encode("utf-8"))
    if root.tag != "PermissionSets":
        raise PermissionXmlError("Root element must be PermissionSets.")
    if root.attrib.get("Version") != "2.0":
        raise PermissionXmlError('Root PermissionSets Version must be "2.0".')
    for permission_set in root:
        if permission_set.tag != "TenantPermissionSet":
            raise PermissionXmlError("Generated import XML must use TenantPermissionSet.")
        role_id = permission_set.attrib.get("RoleID", "")
        if not role_id or len(role_id) > ROLE_ID_MAX_LENGTH:
            raise PermissionXmlError("TenantPermissionSet RoleID is missing or too long.")
        if not permission_set.attrib.get("RoleName"):
            raise PermissionXmlError("TenantPermissionSet RoleName is missing.")
        if permission_set.attrib.get("Assignable") not in {"Yes", "No"}:
            raise PermissionXmlError("TenantPermissionSet Assignable must be Yes or No.")
        for node in permission_set:
            if node.tag == "TenantPermissionSetRel":
                required = {"ObjectType", "ObjectRelatedScope", "ObjectRelatedRoleId", "ObjectRelatedAppId"}
            elif node.tag == "TenantPermission":
                required = {"ObjectType", "ObjectID", "PermissionType"}
                if not any(node.find(field) is not None for field in PERMISSION_FIELDS):
                    raise PermissionXmlError("TenantPermission requires at least one permission field.")
            else:
                raise PermissionXmlError(f"Unexpected child node {node.tag}.")
            missing = [tag for tag in required if node.find(tag) is None]
            if missing:
                raise PermissionXmlError(f"{node.tag} missing required fields: {', '.join(sorted(missing))}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON permission set specification.")
    parser.add_argument("--output", type=Path, help="XML output path. Defaults to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        spec = load_spec(args.input)
        xml_text = build_xml(spec)
        validate_xml(xml_text)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(xml_text, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(xml_text)
    except PermissionXmlError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
