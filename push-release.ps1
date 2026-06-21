# PowerShell script - Push new version to GitHub
# Usage: .\push-release.ps1 "v2.1.0 - New feature"

# Check parameters
if ($args.Count -eq 0) {
    Write-Host "Usage: .\push-release.ps1 `"version message`"" -ForegroundColor Yellow
    Write-Host "Example: .\push-release.ps1 `"v2.1.0 - New feature`"" -ForegroundColor Yellow
    exit 1
}

$versionMessage = $args[0]

# Display start information
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Start publishing new version to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Save current branch
$currentBranch = git branch --show-current
Write-Host "[1/8] Current branch: $currentBranch" -ForegroundColor Green

# Switch to release branch
Write-Host "[2/8] Switch to release branch..." -ForegroundColor Green
git checkout release
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to switch branch! Ensure release branch exists" -ForegroundColor Red
    exit 1
}

# Get latest code from main branch (without merging history)
Write-Host "[3/8] Get latest code from main branch..." -ForegroundColor Green
git checkout main -- .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to get code!" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Add all files (exclude DEVELOPMENT.md)
Write-Host "[4/8] Add files to staging area (exclude DEVELOPMENT.md)..." -ForegroundColor Green
git add --all -- ":!DEVELOPMENT.md"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to add files!" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Commit new version
Write-Host "[5/8] Commit new version: $versionMessage" -ForegroundColor Green
git commit -m $versionMessage
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Warning] No changes to commit" -ForegroundColor Yellow
}

# Extract version number and create tag
Write-Host "[6/8] Create version tag..." -ForegroundColor Green
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
Write-Host "[7/8] Push to GitHub..." -ForegroundColor Green
git push origin release:main --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to push! Check network and permissions" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Push tag to GitHub
if ($version -ne "") {
    Write-Host "[8/8] Push tag $version to GitHub..." -ForegroundColor Green
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
Write-Host "[Done] Publish complete!" -ForegroundColor Green
Write-Host "Version: $versionMessage" -ForegroundColor White
Write-Host "Local branch: $currentBranch (full history)" -ForegroundColor White
Write-Host "GitHub: main (clean history)" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
