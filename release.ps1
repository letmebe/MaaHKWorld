# PowerShell script - Release management
# Usage:
#   .\release.ps1 push <version> <message>  # Publish new version
# Example:
#   .\release.ps1 push v2.1.0 "New feature"

# Check parameters
if ($args.Count -lt 3) {
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\release.ps1 push <version> <message>" -ForegroundColor Yellow
    Write-Host "Example:" -ForegroundColor Yellow
    Write-Host "  .\release.ps1 push v2.1.0 `"New feature`"" -ForegroundColor Yellow
    exit 1
}

$version = $args[1]
$message = $args[2]
$versionMessage = "$version - $message"

# Files to exclude from release (relative to project root)
$excludeFiles = @(
    "DEVELOPMENT.md"
)

# Display start information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Publish new version to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check current branch and switch to main if needed
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "[1/6] Switch to main branch from: $currentBranch" -ForegroundColor Yellow
    git checkout main
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Error] Failed to switch to main branch!" -ForegroundColor Red
        exit 1
    }
    $currentBranch = "main"
} else {
    Write-Host "[1/6] Current branch: $currentBranch" -ForegroundColor Green
}

# Create temporary release branch
Write-Host "[2/6] Create temporary release branch..." -ForegroundColor Green
$tempBranch = "release-temp-" + (Get-Random)
git checkout --orphan $tempBranch
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to create temporary branch!" -ForegroundColor Red
    exit 1
}

# Clear all files in release branch (use --cached to keep working directory files)
Write-Host "[3/6] Clear release branch..." -ForegroundColor Green
git rm -rf . --cached 2>&1 | Out-Null

# Add .gitignore first (so its rules take effect)
Write-Host "[4/6] Add .gitignore first..." -ForegroundColor Green
if (Test-Path ".gitignore") {
    git add .gitignore
}

# Add .gitmodules to preserve submodule configuration
Write-Host "[4.5/6] Add .gitmodules..." -ForegroundColor Green
if (Test-Path ".gitmodules") {
    git add .gitmodules
    # Add submodules explicitly to preserve submodule references
    git config -f .gitmodules --get-regexp path | ForEach-Object {
        $submodulePath = ($_ -split '\s+')[1]
        Write-Host "  Adding submodule: $submodulePath" -ForegroundColor Gray
        git add $submodulePath 2>&1 | Out-Null
    }
}

# Add all files from current working directory, excluding specified files
Write-Host "[5/6] Add files (excluding: $($excludeFiles -join ', '))..." -ForegroundColor Green

# Build exclude patterns for git add
$excludePatterns = $excludeFiles | ForEach-Object { ":!$_" }

# Add all files except excluded ones (now .gitignore rules will work)
git add --all $excludePatterns
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to add files!" -ForegroundColor Red
    git checkout -f $currentBranch 2>&1 | Out-Null
    git branch -D $tempBranch 2>&1 | Out-Null
    exit 1
}

# Commit version
Write-Host "[6/6] Commit new version: $versionMessage" -ForegroundColor Green
git commit -m $versionMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Warning] No changes to commit" -ForegroundColor Yellow
}

# Push to GitHub
Write-Host "[7/6] Push to GitHub..." -ForegroundColor Green
git push origin "${tempBranch}:main" --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to push! Check network and permissions" -ForegroundColor Red
    git checkout -f $currentBranch 2>&1 | Out-Null
    git branch -D $tempBranch 2>&1 | Out-Null
    exit 1
}

# Create tag on GitHub (not locally)
Write-Host "Create tag $version on GitHub..." -ForegroundColor Green

# Delete old tag on GitHub if exists
git push origin --delete $version 2>&1 | Out-Null

# Create and push new tag
git tag -a $version -m $versionMessage
git push origin $version 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Tag $version created on GitHub" -ForegroundColor Green
    # Delete local tag
    git tag -d $version 2>&1 | Out-Null
} else {
    Write-Host "[Warning] Failed to create tag on GitHub" -ForegroundColor Yellow
    git tag -d $version 2>&1 | Out-Null
}

# Switch back to original branch (force to ignore local changes)
Write-Host ""
Write-Host "Switch back to branch: $currentBranch" -ForegroundColor Green
git checkout -f $currentBranch

# Delete temporary release branch
git branch -D $tempBranch 2>&1 | Out-Null
Write-Host "Deleted temporary branch: $tempBranch" -ForegroundColor Yellow

# Display completion information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[Done] Publish complete!" -ForegroundColor Green
Write-Host "Version: $versionMessage" -ForegroundColor White
Write-Host "Local branch: $currentBranch (full history)" -ForegroundColor White
Write-Host "GitHub: main (clean history)" -ForegroundColor White
Write-Host "Excluded files: $($excludeFiles -join ', ')" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
