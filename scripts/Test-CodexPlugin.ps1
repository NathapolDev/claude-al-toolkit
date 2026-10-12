$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('codex-al-test-' + [guid]::NewGuid().ToString('N'))
$sourceRoot = Join-Path $testRoot 'marketplace with spaces'
$testHome = Join-Path $testRoot 'codex home'
New-Item -ItemType Directory -Force $sourceRoot, $testHome | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot '.agents') -Destination $sourceRoot -Recurse
Copy-Item -LiteralPath (Join-Path $repoRoot 'plugins') -Destination $sourceRoot -Recurse
$previousCodexHome = $env:CODEX_HOME
function Invoke-CodexJson {
    param([string[]] $Arguments)
    $output = & codex @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Codex failed: $Arguments" }
    return ($output -join "`n" | ConvertFrom-Json)
}
try {
    $env:CODEX_HOME = $testHome
    $marketplace = Invoke-CodexJson -Arguments @('plugin', 'marketplace', 'add', $sourceRoot, '--json')
    $installed = Invoke-CodexJson -Arguments @('plugin', 'add', 'al-toolkit@codex-al-toolkit', '--json')
    $sourceVersion = (Get-Content (Join-Path $sourceRoot 'plugins/al-toolkit/.codex-plugin/plugin.json') -Raw | ConvertFrom-Json).version
    if ($installed.version -ne $sourceVersion) { throw 'Unexpected installed version' }
    foreach ($path in @('.mcp.codex.json', 'scripts/al-mcp.cmd', 'scripts/al-build.cmd',
                        'references/al-rules.md', 'skills/al-analyst/SKILL.md',
                        'skills/al-developer/SKILL.md', 'skills/al-reviewer/SKILL.md')) {
        if (!(Test-Path -LiteralPath (Join-Path $installed.installedPath $path))) {
            throw "Cached payload missing: $path"
        }
    }
    foreach ($skill in Get-ChildItem (Join-Path $installed.installedPath 'skills/*/SKILL.md')) {
        $body = [IO.File]::ReadAllText($skill.FullName)
        if ($body -notmatch '(?s)\A---\r?\nname: [a-z-]+\r?\ndescription: >-\r?\n  [^\r\n]+\r?\n---') {
            throw "Invalid skill frontmatter: $skill"
        }
        if (!(Test-Path -LiteralPath (Join-Path $skill.DirectoryName '../../references/al-rules.md'))) {
            throw "Broken installed skill reference: $skill"
        }
    }
    $manifestPath = Join-Path $sourceRoot 'plugins/al-toolkit/.codex-plugin/plugin.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $parts = $sourceVersion.Split('.')
    $nextVersion = '{0}.{1}.{2}' -f $parts[0], $parts[1], ([int]$parts[2] + 1)
    $manifest.version = $nextVersion
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    $updated = Invoke-CodexJson -Arguments @('plugin', 'add', 'al-toolkit@codex-al-toolkit', '--json')
    if ($updated.version -ne $nextVersion) { throw 'Update did not install the newer version' }
    $listing = Invoke-CodexJson -Arguments @('plugin', 'list', '--json')
    $entry = $listing.installed | Where-Object pluginId -eq 'al-toolkit@codex-al-toolkit'
    if (!$entry.enabled -or $entry.version -ne $nextVersion) { throw 'Updated plugin is not enabled' }
    Write-Output 'PASS: relocated install, cached skills/references, version refresh, enabled plugin'
} finally {
    $env:CODEX_HOME = $previousCodexHome
    Write-Output "Test files retained at: $testRoot"
}