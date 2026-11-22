[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$userProfile = if ($env:USERPROFILE) { $env:USERPROFILE } else { [Environment]::GetFolderPath('UserProfile') }
$configRoot = [System.IO.Path]::GetFullPath((Join-Path $userProfile '.gemini\config'))

$sourceDir = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'plugins\al-toolkit'))
if (-not (Test-Path -LiteralPath $sourceDir -PathType Container)) {
    throw "Source plugin directory not found: $sourceDir"
}

$pluginsDir = Join-Path $configRoot 'plugins'
$destDir = Join-Path $pluginsDir 'bc365-al-toolkit'

New-Item -ItemType Directory -Path $pluginsDir -Force | Out-Null

New-Item -ItemType Directory -Path $destDir -Force | Out-Null
Get-ChildItem -LiteralPath $sourceDir -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $destDir -Recurse -Force
}

if (-not (Test-Path -LiteralPath (Join-Path $destDir 'plugin.json') -PathType Leaf)) {
    throw "Plugin copy failed; plugin.json not found in $destDir"
}

$destForward = ($destDir -replace '\\', '/').TrimEnd('/')
$alMcpCmd = "$destForward/scripts/al-mcp.cmd"
$alLspMcpCmd = "$destForward/scripts/al-lsp-mcp.cmd"

$mcpConfigPath = Join-Path $destDir 'mcp_config.json'
if (Test-Path -LiteralPath $mcpConfigPath -PathType Leaf) {
    $mcpConfig = Get-Content -LiteralPath $mcpConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
} else {
    $mcpConfig = [pscustomobject]@{
        mcpServers = [pscustomobject]@{}
    }
}

if (-not $mcpConfig.mcpServers) {
    $mcpConfig | Add-Member -NotePropertyName 'mcpServers' -NotePropertyValue ([pscustomobject]@{}) -Force
}

$mcpConfig.mcpServers | Add-Member -NotePropertyName 'al' -NotePropertyValue ([pscustomobject]@{
    command = $alMcpCmd
    args    = @()
}) -Force

$mcpConfig.mcpServers | Add-Member -NotePropertyName 'al-lsp' -NotePropertyValue ([pscustomobject]@{
    command = $alLspMcpCmd
    args    = @()
}) -Force

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$jsonText = ($mcpConfig | ConvertTo-Json -Depth 10) + "`r`n"
[System.IO.File]::WriteAllText($mcpConfigPath, $jsonText, $utf8NoBom)

$skillsDir = Join-Path $configRoot 'skills'
$archiveDir = Join-Path $configRoot 'skills_archived_by_bc365_al_toolkit'
$looseSkillNames = @('al-analyst', 'al-developer', 'al-reviewer')
$archivedSkills = New-Object System.Collections.Generic.List[string]

if (Test-Path -LiteralPath $skillsDir -PathType Container) {
    foreach ($skillName in $looseSkillNames) {
        $loosePath = Join-Path $skillsDir $skillName
        if (Test-Path -LiteralPath $loosePath) {
            if (-not (Test-Path -LiteralPath $archiveDir -PathType Container)) {
                New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
            }
            $archiveTarget = Join-Path $archiveDir $skillName
            if (Test-Path -LiteralPath $archiveTarget) {
                $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                $archiveTarget = Join-Path $archiveDir "$skillName-$stamp"
            }
            Move-Item -LiteralPath $loosePath -Destination $archiveTarget -Force
            $archivedSkills.Add($skillName)
        }
    }
}

Write-Host "Installed bc365-al-toolkit plugin to: $destDir"
Write-Host "Configured MCP servers in: $mcpConfigPath"
Write-Host "  al     -> $alMcpCmd"
Write-Host "  al-lsp -> $alLspMcpCmd"

if ($archivedSkills.Count -gt 0) {
    Write-Host "Archived loose skills to ${archiveDir}: $($archivedSkills -join ', ')"
} else {
    Write-Host "No shadowing loose al-analyst/al-developer/al-reviewer skills found in $skillsDir"
}

Write-Host ""
Write-Host "Prerequisites check:"
Write-Host "  1. AL toolchain (altool.exe / alc.exe) via .NET global tool or VS Code AL Language extension."
Write-Host "  2. Python 3 on PATH (required for al-lsp-mcp and bc365-permissionset)."
Write-Host "  3. Restart or reload Antigravity so the updated plugin and MCP servers take effect."
