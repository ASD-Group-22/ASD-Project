$ErrorActionPreference = "Stop"

$frontendUrl = "http://localhost:3001"
$backendUrl = "http://localhost:5001/health"
$databaseUrl = "http://localhost:6001/health"

function Test-Endpoint {
    param (
        [string]$Name,
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -Method Get `
            -UseBasicParsing `
            -TimeoutSec 10

        if ($response.StatusCode -eq 200) {
            Write-Host "PASS: $Name -> HTTP $($response.StatusCode)"
        }
        else {
            Write-Error "FAIL: $Name -> HTTP $($response.StatusCode)"
            exit 1
        }
    }
    catch {
        Write-Error "FAIL: $Name -> $Url"
        Write-Error $_.Exception.Message
        exit 1
    }
}

Write-Host "======================================"
Write-Host " Student 1 Smoke Test"
Write-Host "======================================"

Test-Endpoint "Frontend" $frontendUrl
Test-Endpoint "Backend" $backendUrl
Test-Endpoint "Database" $databaseUrl

Write-Host ""
Write-Host "Student 1 smoke test PASSED."