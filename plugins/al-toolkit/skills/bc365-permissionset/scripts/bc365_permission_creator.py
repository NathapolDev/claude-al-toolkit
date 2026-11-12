import argparse
import json
import xml.etree.ElementTree as ET
import sys
import os

# Standard App IDs for Business Central
SYSTEM_APP_ID = "{63ca2fa4-4f03-4f2b-a480-172fef340d3f}"
BASE_APP_ID = "{437dbf0e-84ff-417a-965d-ed2bb9650972}"

def indent_xml(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_xml(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def analyze_xml(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error: Failed to parse XML file. {str(e)}", file=sys.stderr)
        sys.exit(1)

    summary = {
        "file_name": os.path.basename(input_path),
        "version": root.get("Version", "2.0"),
        "permission_sets": []
    }

    # Handle both System and Tenant permission sets
    for ps in root.findall(".//PermissionSet") + root.findall(".//TenantPermissionSet"):
        role_id = ps.get("RoleID")
        role_name = ps.get("RoleName")
        assignable = ps.get("Assignable", "Yes")

        ps_info = {
            "role_id": role_id,
            "role_name": role_name,
            "assignable": assignable,
            "relations": [],
            "permissions": []
        }

        for rel in ps.findall("PermissionSetRel") + ps.findall("TenantPermissionSetRel"):
            obj_type = rel.findtext("ObjectType") or rel.findtext("Type") or "Include"
            related_role = rel.findtext("ObjectRelatedRoleId") or rel.findtext("RelatedRoleID")
            related_app = rel.findtext("ObjectRelatedAppId") or rel.findtext("RelatedAppID")
            related_scope = rel.findtext("ObjectRelatedScope") or rel.findtext("RelatedScope") or "System"

            ps_info["relations"].append({
                "type": obj_type,
                "related_role_id": related_role,
                "related_app_id": related_app,
                "related_scope": related_scope
            })

        for perm in ps.findall("Permission") + ps.findall("TenantPermission"):
            obj_type = perm.findtext("ObjectType")
            obj_id = perm.findtext("ObjectID")

            obj_type_map = {
                "0": "Table Data", "1": "Table", "3": "Report",
                "5": "Codeunit", "6": "XMLPort", "8": "Page", "9": "Query"
            }
            if obj_type in obj_type_map:
                obj_type = obj_type_map[obj_type]

            ps_info["permissions"].append({
                "object_type": obj_type,
                "object_id": obj_id,
                "read": perm.findtext("ReadPermission") or "No",
                "insert": perm.findtext("InsertPermission") or "No",
                "modify": perm.findtext("ModifyPermission") or "No",
                "delete": perm.findtext("DeletePermission") or "No",
                "execute": perm.findtext("ExecutePermission") or "No"
            })

        summary["permission_sets"].append(ps_info)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Success! Analysis written to: {output_path}")
    except Exception as e:
        print(f"Error: Failed to write output file. {str(e)}", file=sys.stderr)
        sys.exit(1)

def parse_permissions_json(permissions_str):
    if not permissions_str:
        return []
    try:
        if os.path.exists(permissions_str):
            with open(permissions_str, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return json.loads(permissions_str)
    except Exception as e:
        print(f"Error: Failed to parse object permissions JSON. {str(e)}", file=sys.stderr)
        sys.exit(1)

def create_xml(role_id, role_name, include_system_roles, object_permissions, output_path):
    root = ET.Element("PermissionSets", Version="2.0")
    tps = ET.SubElement(root, "TenantPermissionSet", RoleID=role_id, RoleName=role_name, Assignable="Yes")

    if include_system_roles:
        roles = [r.strip() for r in include_system_roles.split(",") if r.strip()]
        for role in roles:
            app_id = SYSTEM_APP_ID if role == "LOGIN" else BASE_APP_ID
            rel = ET.SubElement(tps, "TenantPermissionSetRel")
            ET.SubElement(rel, "ObjectType").text = "Include"
            ET.SubElement(rel, "ObjectRelatedScope").text = "System"
            ET.SubElement(rel, "ObjectRelatedRoleId").text = role
            ET.SubElement(rel, "ObjectRelatedAppId").text = app_id

    perms = parse_permissions_json(object_permissions)
    for perm in perms:
        tp = ET.SubElement(tps, "TenantPermission")
        ET.SubElement(tp, "ObjectType").text = perm.get("ObjectType", "Table Data")
        ET.SubElement(tp, "ObjectID").text = str(perm.get("ObjectID", 0))

        obj_type = perm.get("ObjectType", "Table Data")
        if obj_type == "Table Data":
            for field, default in [("ReadPermission", "Yes"), ("InsertPermission", "No"), ("ModifyPermission", "No"), ("DeletePermission", "No")]:
                val = perm.get(field, default)
                if val in ["Yes", "Indirect"]:
                    ET.SubElement(tp, field).text = val
        else:
            exec_val = perm.get("ExecutePermission", "Yes")
            if exec_val == "Yes":
                ET.SubElement(tp, "ExecutePermission").text = exec_val

        ET.SubElement(tp, "PermissionType").text = "Include"

    indent_xml(root)
    tree = ET.ElementTree(root)

    try:
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"Success! Tenant Permission Set XML written to: {output_path}")
    except Exception as e:
        print(f"Error: Failed to write XML file. {str(e)}", file=sys.stderr)
        sys.exit(1)

def create_al(role_id, role_name, include_system_roles, object_permissions, output_path, object_id=50100):
    al_content = []
    safe_role_id = role_id.replace(" ", "")

    al_content.append(f'permissionset {object_id} "{safe_role_id}"')
    al_content.append('{')
    al_content.append('  Assignable = true;')
    al_content.append(f'  Caption = \'{role_name}\';')

    if include_system_roles:
        roles = [f'"{r.strip()}"' if " " in r.strip() else r.strip() for r in include_system_roles.split(",") if r.strip()]
        al_content.append(f'  IncludedPermissionSets = {", ".join(roles)};')

    perms = parse_permissions_json(object_permissions)
    if perms:
        al_content.append('  Permissions =')
        perm_lines = []
        for perm in perms:
            obj_type = perm.get("ObjectType", "Table Data").lower().replace(" ", "")
            obj_id = perm.get("ObjectID")

            if obj_type == "tabledata":
                rimd = ""
                if perm.get("ReadPermission", "Yes") == "Yes": rimd += "R"
                if perm.get("InsertPermission", "No") == "Yes": rimd += "I"
                if perm.get("ModifyPermission", "No") == "Yes": rimd += "M"
                if perm.get("DeletePermission", "No") == "Yes": rimd += "D"
                if not rimd: rimd = "R"
                perm_lines.append(f'    {obj_type} {obj_id} = {rimd}')
            else:
                exec_val = "X" if perm.get("ExecutePermission", "Yes") == "Yes" else ""
                if exec_val:
                    perm_lines.append(f'    {obj_type} {obj_id} = {exec_val}')

        if perm_lines:
            al_content.append(",\n".join(perm_lines) + ";")

    al_content.append('}')

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(al_content))
        print(f"Success! AL Permission Set Object written to: {output_path}")
    except Exception as e:
        print(f"Error: Failed to write AL file. {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="BC365 Permission Sets CLI Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_analyze = subparsers.add_parser("analyze", help="Analyze BC XML permission sets")
    parser_analyze.add_argument("--input", required=True, help="Input XML file path")
    parser_analyze.add_argument("--output", required=True, help="Output JSON file path")

    parser_xml = subparsers.add_parser("create-xml", help="Create a Tenant XML permission set")
    parser_xml.add_argument("--role-id", required=True, help="Role ID (max 20 chars)")
    parser_xml.add_argument("--role-name", required=True, help="Role Name")
    parser_xml.add_argument("--include-system-roles", help="Comma-separated system roles to include")
    parser_xml.add_argument("--object-permissions", default="[]", help="JSON string or file path with object permissions")
    parser_xml.add_argument("--output", required=True, help="Output XML file path")

    parser_al = subparsers.add_parser("create-al", help="Create an AL permission set object")
    parser_al.add_argument("--role-id", required=True, help="Role ID")
    parser_al.add_argument("--role-name", required=True, help="Role Name")
    parser_al.add_argument("--include-system-roles", help="Comma-separated system roles to include")
    parser_al.add_argument("--object-permissions", default="[]", help="JSON string or file path with object permissions")
    parser_al.add_argument("--object-id", type=int, default=50100, help="Permission set object ID (get one with al_getnextobjectid)")
    parser_al.add_argument("--output", required=True, help="Output AL file path")

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_xml(args.input, args.output)
    elif args.command == "create-xml":
        create_xml(args.role_id, args.role_name, args.include_system_roles, args.object_permissions, args.output)
    elif args.command == "create-al":
        create_al(args.role_id, args.role_name, args.include_system_roles, args.object_permissions, args.output, args.object_id)

if __name__ == "__main__":
    main()
