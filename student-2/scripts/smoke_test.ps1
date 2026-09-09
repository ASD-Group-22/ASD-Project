$ErrorActionPreference = "Stop"
function Test-Url($Url) {
    Write-Host "Checking $Url"
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10
    if ($response.StatusCode -ne 200) { throw "Expected HTTP 200 from $Url, got $($response.StatusCode)" }
    Write-Host "PASS $Url -> $($response.StatusCode)"
}
Test-Url "http://localhost:8202/"
Test-Url "http://localhost:5202/"
Test-Url "http://localhost:5302/"
Test-Url "http://localhost:5202/skill-exchange"
Write-Host "Student 2 smoke checks passed."
