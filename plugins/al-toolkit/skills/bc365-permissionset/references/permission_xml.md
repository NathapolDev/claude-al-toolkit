# Business Central Tenant Permission XML Reference

This reference is based on permission set XML exported from a Business Central 28 tenant.

## Import XML

Use tenant nodes for XML imported from the Business Central client:

- Root: `PermissionSets` with `Version="2.0"`.
- Permission set: `TenantPermissionSet`.
- Included permission set: `TenantPermissionSetRel`.
- Direct object permission: `TenantPermission`.

Example:

```xml
<?xml version="1.0" encoding="utf-8"?>
<PermissionSets Version="2.0">
  <TenantPermissionSet RoleID="SALES_DEPT" RoleName="Sales Department" Assignable="Yes">
    <TenantPermissionSetRel>
      <ObjectType>Include</ObjectType>
      <ObjectRelatedScope>System</ObjectRelatedScope>
      <ObjectRelatedRoleId>LOGIN</ObjectRelatedRoleId>
      <ObjectRelatedAppId>{63ca2fa4-4f03-4f2b-a480-172fef340d3f}</ObjectRelatedAppId>
    </TenantPermissionSetRel>
    <TenantPermission>
      <ObjectType>Table Data</ObjectType>
      <ObjectID>36</ObjectID>
      <ReadPermission>Yes</ReadPermission>
      <InsertPermission>Yes</InsertPermission>
      <ModifyPermission>Yes</ModifyPermission>
      <PermissionType>Include</PermissionType>
    </TenantPermission>
  </TenantPermissionSet>
</PermissionSets>
```

## Included Permission Sets

Use this shape:

```xml
<TenantPermissionSetRel>
  <ObjectType>Include</ObjectType>
  <ObjectRelatedScope>System</ObjectRelatedScope>
  <ObjectRelatedRoleId>D365 BASIC</ObjectRelatedRoleId>
  <ObjectRelatedAppId>{437dbf0e-84ff-417a-965d-ed2bb9650972}</ObjectRelatedAppId>
</TenantPermissionSetRel>
```

Known app IDs from the local exports:

- System Application: `{63ca2fa4-4f03-4f2b-a480-172fef340d3f}`
- Base Application: `{437dbf0e-84ff-417a-965d-ed2bb9650972}`

## Direct Object Permissions

Use these object type labels for tenant XML:

- `Table Data`
- `Table`
- `Page`
- `Report`
- `Codeunit`
- `Query`
- `XMLport`
- `System`

Permission fields:

- `ReadPermission`
- `InsertPermission`
- `ModifyPermission`
- `DeletePermission`
- `ExecutePermission`

Values seen in exports:

- `Yes`
- `Indirect`

For generated tenant XML, default to `Yes` unless the user asks for indirect access.

## Differences From System XML And AL

System exports use `PermissionSet`, `PermissionSetRel`, and `Permission`. Tenant/user-defined imports use `TenantPermissionSet`, `TenantPermissionSetRel`, and `TenantPermission`.

`.permissionset.al` files are not the default output for this skill. Only create AL permission set objects when the user explicitly asks for an extension source file.

## Validation Checklist

- XML parses successfully.
- Root is `PermissionSets`.
- Root has `Version="2.0"`.
- Every generated permission set is `TenantPermissionSet`.
- `RoleID` is present and no longer than 20 characters.
- `RoleName` is present.
- `Assignable` is `Yes` or `No`.
- Every `TenantPermissionSetRel` has `ObjectType`, `ObjectRelatedScope`, `ObjectRelatedRoleId`, and `ObjectRelatedAppId`.
- Every `TenantPermission` has `ObjectType`, `ObjectID`, at least one permission field, and `PermissionType`.
