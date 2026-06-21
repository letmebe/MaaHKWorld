# PowerShell script - Push new version to GitHub
# Usage: .\push-release.ps1 <version> <message>
# Example: .\push-release.ps1 v2.1.0 "New feature"

# Check parameters
if ($args.Count -lt 2) {
    Write-Host "Usage: .\push-release.ps1 <version> <message>" -ForegroundColor Yellow
    Write-Host "Example: .\push-release.ps1 v2.1.0 `"New feature`"" -ForegroundColor Yellow
    exit 1
}

$version = $args[0]
$message = $args[1]
$versionMessage = "$version - $message"

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

# Push to GitHub
Write-Host "[6/8] Push to GitHub..." -ForegroundColor Green
git push origin release:main --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to push! Check network and permissions" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Create tag on GitHub (not locally)
Write-Host "[7/8] Create tag $version on GitHub..." -ForegroundColor Green

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
