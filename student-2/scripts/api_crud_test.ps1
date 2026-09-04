$ErrorActionPreference = "Stop"
$Base = "http://localhost:5202"

Write-Host "1) Read seeded listings"
$list = Invoke-RestMethod -Uri "$Base/skill-exchange" -Method Get
if ($list.listings.Count -lt 10) { throw "Expected at least 10 active seeded listings." }

Write-Host "2) Read single listing"
$one = Invoke-RestMethod -Uri "$Base/skill-exchange/1" -Method Get
if ($one.listing_id -ne 1) { throw "Could not read listing 1." }

Write-Host "3) Search"
$search = Invoke-RestMethod -Uri "$Base/skill-exchange/search?skill=Python" -Method Get
if ($search.listings.Count -lt 1) { throw "Search returned no Python result." }

Write-Host "4) Create"
$payload = @{
    student_id = 2001
    student_name = "Release Zero Test"
    skill_offered = "Docker"
    skill_wanted = "Python"
    availability = "Tue evening"
    description = "Temporary CRUD validation listing"
    status = "active"
} | ConvertTo-Json
$created = Invoke-RestMethod -Uri "$Base/skill-exchange" -Method Post -ContentType "application/json" -Body $payload
$id = $created.listing.listing_id
if (-not $id) { throw "Create did not return listing_id." }

Write-Host "5) Update listing $id"
$update = @{
    student_id = 2001
    student_name = "Release Zero Test"
    skill_offered = "Docker"
    skill_wanted = "Git"
    availability = "Tue evening"
    description = "Updated CRUD validation listing"
    status = "active"
} | ConvertTo-Json
$updated = Invoke-RestMethod -Uri "$Base/skill-exchange/$id" -Method Put -ContentType "application/json" -Body $update
if ($updated.listing.skill_wanted -ne "Git") { throw "Update failed." }

Write-Host "6) Deterministic match evidence"
$matches = Invoke-RestMethod -Uri "$Base/skill-exchange/1/matches" -Method Get
if ($matches.candidates.Count -lt 1) { throw "Seeded listing 1 should have a candidate." }

Write-Host "7) Deactivate listing $id"
$deleted = Invoke-RestMethod -Uri "$Base/skill-exchange/$id" -Method Delete
if ($deleted.listing.status -ne "inactive") { throw "Deactivate failed." }

Write-Host "PASS: Student 2 CRUD/search/candidate API validation completed."
