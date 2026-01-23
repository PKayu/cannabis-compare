# Cannabis Aggregator - Development Startup Script (PowerShell)
# Usage: .\start-dev.ps1
# If you get an execution policy error, run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

param(
    [switch]$SkipBrowser = $false
)

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Cannabis Aggregator - Development Environment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Function to run command in new PowerShell window
function Start-ServerWindow {
    param(
        [string]$Title,
        [string]$Command
    )
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $Command -WindowStyle Normal
}

# Step 1: Setup backend venv
if (-Not (Test-Path "backend\venv")) {
    Write-Host "[1/4] Creating Python virtual environment..." -ForegroundColor Yellow
    Push-Location backend
    python -m venv venv
    Pop-Location
    Write-Host ""
}

# Step 2: Install backend dependencies
Write-Host "[2/4] Setting up backend dependencies..." -ForegroundColor Yellow
& "backend\venv\Scripts\Activate.ps1"
pip install -r backend\requirements.txt | Out-Null
Write-Host "Backend ready." -ForegroundColor Green
Write-Host ""

# Step 3: Install frontend dependencies
if (-Not (Test-Path "frontend\node_modules")) {
    Write-Host "[3/4] Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
    Write-Host ""
} else {
    Write-Host "[3/4] Frontend dependencies already installed." -ForegroundColor Green
    Write-Host ""
}

# Step 4: Launch servers
Write-Host "[4/4] Launching servers..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting backend on http://localhost:8000" -ForegroundColor Green
Write-Host "Starting frontend on http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C in either window to stop the servers." -ForegroundColor Cyan
Write-Host ""

# Start backend server
$backendCommand = "cd '$PSScriptRoot\backend' && `"$PSScriptRoot\backend\venv\Scripts\Activate.ps1`" && uvicorn main:app --reload"
Start-ServerWindow -Title "Cannabis Backend" -Command $backendCommand

# Wait a moment then start frontend
Start-Sleep -Seconds 2
$frontendCommand = "cd '$PSScriptRoot\frontend' && npm run dev"
Start-ServerWindow -Title "Cannabis Frontend" -Command $frontendCommand

# Open API docs in browser
if (-Not $SkipBrowser) {
    Start-Sleep -Seconds 3
    Write-Host ""
    Write-Host "Opening API documentation in browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000/docs"
}

Write-Host ""
Write-Host "Development servers started!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
