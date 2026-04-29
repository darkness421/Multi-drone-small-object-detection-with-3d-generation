$ErrorActionPreference = "Continue"

function Show-Command($Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        $command | Select-Object Name, Source, Version | Format-Table -AutoSize
    } else {
        Write-Host "${Name}: not found"
    }
}

Write-Host "== Git =="
git --version
git status --short --branch
git remote -v

Write-Host "`n== IDE =="
Show-Command code
Show-Command devenv

$vswhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    & $vswhere -latest -products * -format json
} else {
    Write-Host "vswhere: not found"
}

Write-Host "`n== Runtime =="
Show-Command python
Show-Command node
Show-Command npm
Show-Command gh

Write-Host "`n== NVIDIA =="
nvidia-smi

Write-Host "`n== Isaac Sim candidates =="
Show-Command isaac-sim
Show-Command omniverse-launcher
