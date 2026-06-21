# PowerShell script - Initialize release branch
# Usage: .\init-release.ps1 <version> <message>
# Example: .\init-release.ps1 v2.0.0 "Initial version"

# Check parameters
if ($args.Count -lt 2) {
    Write-Host "Usage: .\init-release.ps1 <version> <message>" -ForegroundColor Yellow
    Write-Host "Example: .\init-release.ps1 v2.0.0 `"Initial version`"" -ForegroundColor Yellow
    exit 1
}

$version = $args[0]
$message = $args[1]
$versionMessage = "$version - $message"

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

# Push to GitHub
Write-Host "[5/6] Push to GitHub..." -ForegroundColor Green
git push origin release:main --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to push! Check network and permissions" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Create tag on GitHub (not locally)
Write-Host "[6/6] Create tag $version on GitHub..." -ForegroundColor Green

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
Write-Host "[Done] Initialization complete!" -ForegroundColor Green
Write-Host "Version: $versionMessage" -ForegroundColor White
Write-Host "Local branches:" -ForegroundColor White
Write-Host "  - $currentBranch (full history, for development)" -ForegroundColor White
Write-Host "  - release (clean history, for publishing)" -ForegroundColor White
Write-Host "GitHub: main = release" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "For future releases use: .\push-release.ps1 <version> <message>" -ForegroundColor Yellow
