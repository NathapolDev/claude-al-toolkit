[CmdletBinding()]
param(
  [Parameter(Position = 0)]
  [string] $ProjectDir = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$ProjectFolder = Get-Item -LiteralPath (Resolve-Path -LiteralPath $ProjectDir).Path
if (-not $ProjectFolder.PSIsContainer) {
  throw "ProjectDir must be a directory: $ProjectDir"
}

# Resolve an invocation from inside an AL project's subdirectory as well.
while ($null -ne $ProjectFolder -and
       -not (Test-Path -LiteralPath (Join-Path $ProjectFolder.FullName 'app.json') -PathType Leaf)) {
  $ProjectFolder = $ProjectFolder.Parent
}
if ($null -eq $ProjectFolder) {
  throw "No app.json in '$ProjectDir' or its parents. Select an AL project folder first."
}

# Assign only after validation. This affects this PowerShell process and its children.
$env:AL_PROJECT_DIR = $ProjectFolder.FullName
Write-Output $env:AL_PROJECT_DIR
