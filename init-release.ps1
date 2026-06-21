# PowerShell script - Initialize release branch
# Usage: .\init-release.ps1 "v2.0.0 - Initial version"

# Check parameters
if ($args.Count -eq 0) {
    Write-Host "Usage: .\init-release.ps1 `"version message`"" -ForegroundColor Yellow
    Write-Host "Example: .\init-release.ps1 `"v2.0.0 - Initial version`"" -ForegroundColor Yellow
    exit 1
}

$versionMessage = $args[0]

# Display start information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Initialize release branch" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if release branch already exists
$releaseBranch = git branch --list release
if ($releaseBranch) {
    Write-Host "[Warning] Release branch already exists!" -ForegroundColor Yellow
    $confirm = Read-Host "Delete and recreate? (y/n)"
    if ($confirm -eq "y") {
        git branch -D release
        Write-Host "Deleted old release branch" -ForegroundColor Yellow
    } else {
        Write-Host "Operation cancelled" -ForegroundColor Yellow
        exit 0
    }
}

# Save current branch
$currentBranch = git branch --show-current
Write-Host "[1/6] Current branch: $currentBranch" -ForegroundColor Green

# Create orphan branch (no parent commit)
Write-Host "[2/6] Create orphan branch release..." -ForegroundColor Green
git checkout --orphan release
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to create branch!" -ForegroundColor Red
    exit 1
}

# Add all files (exclude DEVELOPMENT.md)
Write-Host "[3/6] Add files to staging area (exclude DEVELOPMENT.md)..." -ForegroundColor Green
git add --all -- ":!DEVELOPMENT.md"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to add files!" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Commit initial version
Write-Host "[4/6] Commit initial version: $versionMessage" -ForegroundColor Green
git commit -m $versionMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to commit!" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Extract version number and create tag
Write-Host "[5/6] Create version tag..." -ForegroundColor Green
$version = ""
if ($versionMessage -match '^v[\d.]+') {
    $version = $matches[0]
    git tag -a $version -m $versionMessage
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Warning] Failed to create tag, may already exist" -ForegroundColor Yellow
    }
} else {
    Write-Host "[Warning] Cannot extract version number, skip tagging" -ForegroundColor Yellow
}

# Push to GitHub
Write-Host "[6/6] Push to GitHub..." -ForegroundColor Green
git push origin release:main --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to push! Check network and permissions" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Push tag to GitHub
if ($version -ne "") {
    Write-Host "Push tag $version to GitHub..." -ForegroundColor Green
    git push origin $version --force
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[Warning] Failed to push tag" -ForegroundColor Yellow
    }
}

# Switch back to original branch
Write-Host ""
Write-Host "Switch back to branch: $currentBranch" -ForegroundColor Green
git checkout $currentBranch

# Display completion information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[Done] Initialization complete!" -ForegroundColor Green
Write-Host "Version: $versionMessage" -ForegroundColor White
Write-Host "Local branches:" -ForegroundColor White
Write-Host "  - $currentBranch (full history, for development)" -ForegroundColor White
Write-Host "  - release (clean history, for publishing)" -ForegroundColor White
Write-Host "GitHub: main = release" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "For future releases use: .\push-release.ps1 `"version message`"" -ForegroundColor Yellow
