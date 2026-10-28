param(
    [string]$ResourceGroup = "lab11-rg"
)

$ErrorActionPreference = "Stop"

$Evidence = [System.Collections.Generic.List[string]]::new()
$Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmss")

function Add-Pass {
    param([string]$Message)

    Write-Host "PASS: $Message" -ForegroundColor Green
    $script:Evidence.Add("PASS: $Message")
}

function Require {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw "FAIL: $Message"
    }

    Add-Pass $Message
}

function Get-AppUrl {
    param([string]$Name)

    $fqdn = az containerapp show `
        --name $Name `
        --resource-group $ResourceGroup `
        --query properties.configuration.ingress.fqdn `
        --output tsv

    if (-not $fqdn) {
        throw "Could not resolve FQDN for $Name"
    }

    return "https://$fqdn"
}

function Invoke-CloudRequest {
    param(
        [Parameter(Mandatory)]
        [string]$Uri,

        [Parameter(Mandatory)]
        [ValidateSet("Get", "Post", "Put", "Delete")]
        [string]$Method,

        $Body = $null,

        [int]$MaxAttempts = 12
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $params = @{
                Uri        = $Uri
                Method     = $Method
                TimeoutSec = 300
            }

            if ($null -ne $Body) {
                $params.ContentType = "application/json"
                $params.Body = (
                    $Body |
                    ConvertTo-Json -Depth 12 -Compress
                )
            }

            return Invoke-RestMethod @params
        }
        catch {
            $statusCode = $null

            try {
                $statusCode = [int]$_.Exception.Response.StatusCode
            }
            catch {
            }

            $details = $_.ErrorDetails.Message
            $message = $_.Exception.Message

            # ACA can expose a downstream database cold start as HTTP 500
            # when a backend's own internal request timeout expires.
            $transient = (
                $statusCode -in @(500, 502, 503, 504) -or
                $details -match "App port is not ready|timed out|timeout" -or
                $message -match "500|502|503|504|timed out|timeout"
            )

            if (-not $transient -or $attempt -ge $MaxAttempts) {
                throw
            }

            Write-Host `
                "Transient ACA readiness failure on $Method $Uri - retry $attempt/$MaxAttempts..." `
                -ForegroundColor Yellow

            Start-Sleep -Seconds 10
        }
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "GROUP 22 RELEASE 2 INTEGRATED AZURE VALIDATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$homeUrl = Get-AppUrl "g22-r2-home"

$urls = @{
    1 = Get-AppUrl "g22-r2-s1-web"
    2 = Get-AppUrl "g22-r2-s2-web"
    3 = Get-AppUrl "g22-r2-s3-web"
    4 = Get-AppUrl "g22-r2-s4-web"
    5 = Get-AppUrl "g22-r2-s5-web"
}

Write-Host "`n===== DEPLOYMENT TOPOLOGY =====" -ForegroundColor Cyan

$apps = (
    az containerapp list `
        --resource-group $ResourceGroup `
        --output json |
    ConvertFrom-Json
)

$r2Apps = @(
    $apps |
    Where-Object { $_.name -like "g22-r2-*" }
)

Require ($r2Apps.Count -eq 16) `
    "Exactly 16 Group 22 Release 2 Container Apps exist"

Require (
    @(
        $r2Apps |
        Where-Object {
            $_.properties.provisioningState -ne "Succeeded"
        }
    ).Count -eq 0
) "All 16 Container Apps have provisioning state Succeeded"

Write-Host "`n===== SHARED HOME =====" -ForegroundColor Cyan

$homeHtml = Invoke-CloudRequest `
    -Uri "$homeUrl/" `
    -Method Get

Require ([string]$homeHtml -match "<html|<!DOCTYPE") `
    "Shared home returns HTML"

foreach ($i in 1..5) {
    Require (
        ([string]$homeHtml).Contains($urls[$i])
    ) "Shared home links to Student $i Azure frontend"
}

# ============================================================
# STUDENT 1
# ============================================================

Write-Host "`n===== STUDENT 1 PROJECT CRUD =====" -ForegroundColor Cyan

$s1Id = $null
$s1Name = "R2 Cloud Validation Project $Stamp"

try {
    $createBody = @{
        name        = $s1Name
        description = "Temporary Release 2 Azure CRUD validation project."
        start_date  = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
        end_date    = (Get-Date).AddDays(8).ToString("yyyy-MM-dd")
    }

    Invoke-CloudRequest `
        -Uri "$($urls[1])/api/projects" `
        -Method Post `
        -Body $createBody |
    Out-Null

    $projects = Invoke-CloudRequest `
        -Uri "$($urls[1])/api/projects" `
        -Method Get

    $project = @($projects) |
        Where-Object { $_.name -eq $s1Name } |
        Select-Object -First 1

    Require ($null -ne $project) `
        "Student 1 CREATE produced a project"

    $s1Id = $project.id

    $read = Invoke-CloudRequest `
        -Uri "$($urls[1])/api/projects/$s1Id" `
        -Method Get

    Require ($read.name -eq $s1Name) `
        "Student 1 READ returned created project"

    $updatedDescription = "Updated by Release 2 cloud validation."

    Invoke-CloudRequest `
        -Uri "$($urls[1])/api/projects/$s1Id" `
        -Method Put `
        -Body @{
            description = $updatedDescription
        } |
    Out-Null

    $read = Invoke-CloudRequest `
        -Uri "$($urls[1])/api/projects/$s1Id" `
        -Method Get

    Require ($read.description -eq $updatedDescription) `
        "Student 1 UPDATE changed project"

    Invoke-CloudRequest `
        -Uri "$($urls[1])/api/projects/$s1Id" `
        -Method Delete |
    Out-Null

    $projects = Invoke-CloudRequest `
        -Uri "$($urls[1])/api/projects" `
        -Method Get

    Require (
        -not (
            @($projects) |
            Where-Object { $_.id -eq $s1Id }
        )
    ) "Student 1 DELETE removed project"

    $s1Id = $null
}
finally {
    if ($null -ne $s1Id) {
        try {
            Invoke-CloudRequest `
                -Uri "$($urls[1])/api/projects/$s1Id" `
                -Method Delete |
            Out-Null
        }
        catch {
        }
    }
}

# ============================================================
# STUDENT 2
# ============================================================

Write-Host "`n===== STUDENT 2 SKILL EXCHANGE CRUD =====" -ForegroundColor Cyan

$s2Id = $null
$s2Name = "Cloud Validation $Stamp"

try {
    $listing = @{
        student_id    = 900001
        student_name  = $s2Name
        skill_offered = "Azure"
        skill_wanted  = "Testing"
        availability  = "Friday afternoon"
        description   = "Temporary Release 2 cloud validation listing."
        status        = "active"
    }

    Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange" `
        -Method Post `
        -Body $listing |
    Out-Null

    $active = Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange" `
        -Method Get

    $created = @($active.listings) |
        Where-Object { $_.student_name -eq $s2Name } |
        Select-Object -First 1

    Require ($null -ne $created) `
        "Student 2 CREATE produced a listing"

    $s2Id = $created.listing_id

    $read = Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange/$s2Id" `
        -Method Get

    Require ($read.student_name -eq $s2Name) `
        "Student 2 READ returned created listing"

    $listing.description = "Updated Release 2 validation listing."

    Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange/$s2Id" `
        -Method Put `
        -Body $listing |
    Out-Null

    $read = Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange/$s2Id" `
        -Method Get

    Require (
        $read.description -eq "Updated Release 2 validation listing."
    ) "Student 2 UPDATE changed listing"

    Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange/$s2Id" `
        -Method Delete |
    Out-Null

    $read = Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange/$s2Id" `
        -Method Get

    Require ($read.status -eq "inactive") `
        "Student 2 DELETE soft-deactivated listing"

    $active = Invoke-CloudRequest `
        -Uri "$($urls[2])/api/skill-exchange" `
        -Method Get

    Require (
        -not (
            @($active.listings) |
            Where-Object { $_.listing_id -eq $s2Id }
        )
    ) "Student 2 inactive listing is excluded from active collection"

    $s2Id = $null
}
finally {
    if ($null -ne $s2Id) {
        try {
            Invoke-CloudRequest `
                -Uri "$($urls[2])/api/skill-exchange/$s2Id" `
                -Method Delete |
            Out-Null
        }
        catch {
        }
    }
}

# ============================================================
# STUDENT 3
# ============================================================

Write-Host "`n===== STUDENT 3 GROUP CRUD =====" -ForegroundColor Cyan

$s3Id = $null
$s3Name = "R2 Validation Group $Stamp"

try {
    Invoke-CloudRequest `
        -Uri "$($urls[3])/api/ui/groups/finalise" `
        -Method Post `
        -Body @{
            group_name = $s3Name
            members    = @(1, 4)
        } |
    Out-Null

    $groups = Invoke-CloudRequest `
        -Uri "$($urls[3])/api/ui/groups" `
        -Method Get

    $group = @($groups) |
        Where-Object { $_.group_name -eq $s3Name } |
        Select-Object -First 1

    Require ($null -ne $group) `
        "Student 3 CREATE produced a group"

    $s3Id = $group.id

    Require (@($group.members).Count -eq 2) `
        "Student 3 READ returned created group"

    Invoke-CloudRequest `
        -Uri "$($urls[3])/api/ui/groups/by-id/$s3Id" `
        -Method Put `
        -Body @{
            group_name = $s3Name
            members    = @(1, 4, 5)
        } |
    Out-Null

    $groups = Invoke-CloudRequest `
        -Uri "$($urls[3])/api/ui/groups" `
        -Method Get

    $group = @($groups) |
        Where-Object { $_.id -eq $s3Id } |
        Select-Object -First 1

    Require (@($group.members).Count -eq 3) `
        "Student 3 UPDATE changed group members"

    Invoke-CloudRequest `
        -Uri "$($urls[3])/api/ui/groups/by-id/$s3Id" `
        -Method Delete |
    Out-Null

    $groups = Invoke-CloudRequest `
        -Uri "$($urls[3])/api/ui/groups" `
        -Method Get

    Require (
        -not (
            @($groups) |
            Where-Object { $_.id -eq $s3Id }
        )
    ) "Student 3 DELETE removed group"

    $s3Id = $null
}
finally {
    if ($null -ne $s3Id) {
        try {
            Invoke-CloudRequest `
                -Uri "$($urls[3])/api/ui/groups/by-id/$s3Id" `
                -Method Delete |
            Out-Null
        }
        catch {
        }
    }
}

# ============================================================
# STUDENT 4
# ============================================================

Write-Host "`n===== STUDENT 4 SKILL PROFILE CRUD =====" -ForegroundColor Cyan

$s4Id = $null
$s4StudentId = 900004

try {
    $profile = @{
        student_id = $s4StudentId
        skills = @(
            @{
                skill_name  = "Azure Validation"
                skill_level = "Intermediate"
                strength    = "Cloud testing"
                weakness    = "Advanced optimisation"
            }
        )
    }

    $createdProfile = Invoke-CloudRequest `
        -Uri "$($urls[4])/profiles" `
        -Method Post `
        -Body $profile

    $s4Id = $createdProfile.profile_id

    if (-not $s4Id) {
        $s4Id = $createdProfile.id
    }

    Require ($null -ne $s4Id) `
        "Student 4 CREATE returned a profile ID"

    $read = Invoke-CloudRequest `
        -Uri "$($urls[4])/profiles/$s4Id" `
        -Method Get

    Require ($read.student_id -eq $s4StudentId) `
        "Student 4 READ returned created profile"

    $profile.skills[0].strength = "Integrated Azure CRUD testing"

    Invoke-CloudRequest `
        -Uri "$($urls[4])/profiles/$s4Id" `
        -Method Put `
        -Body $profile |
    Out-Null

    $read = Invoke-CloudRequest `
        -Uri "$($urls[4])/profiles/$s4Id" `
        -Method Get

    Require (
        $read.skills[0].strength -eq "Integrated Azure CRUD testing"
    ) "Student 4 UPDATE changed profile skill"

    Invoke-CloudRequest `
        -Uri "$($urls[4])/profiles/$s4Id" `
        -Method Delete |
    Out-Null

    $s4Id = $null

    Add-Pass "Student 4 DELETE completed successfully"
}
finally {
    if ($null -ne $s4Id) {
        try {
            Invoke-CloudRequest `
                -Uri "$($urls[4])/profiles/$s4Id" `
                -Method Delete |
            Out-Null
        }
        catch {
        }
    }
}

# ============================================================
# STUDENT 5
# ============================================================

Write-Host "`n===== STUDENT 5 CAMPUS SPACE CRUD =====" -ForegroundColor Cyan

$s5Id = $null
$s5Name = "R2 Validation Space $Stamp"

try {
    $space = @{
        space_name     = $s5Name
        building       = "Building 11"
        building_level = "5"
        room_number    = "VALIDATION"
        max_capacity   = 2
        space_type     = "Collaborative Study"
        noise_level    = "Moderate"
        facilities     = @(
            "Wi-Fi",
            "Power Outlets"
        )
        accessibility  = "Wheelchair Accessible"
        opening_time   = "08:00"
        closing_time   = "18:00"
        description    = "Temporary Release 2 cloud CRUD validation space."
        image_url      = ""
    }

    Invoke-CloudRequest `
        -Uri "$($urls[5])/api/spaces" `
        -Method Post `
        -Body $space |
    Out-Null

    $spaces = Invoke-CloudRequest `
        -Uri "$($urls[5])/api/spaces" `
        -Method Get

    $createdSpace = @($spaces) |
        Where-Object { $_.space_name -eq $s5Name } |
        Select-Object -First 1

    Require ($null -ne $createdSpace) `
        "Student 5 CREATE produced a campus space"

    $s5Id = $createdSpace.space_id

    $read = Invoke-CloudRequest `
        -Uri "$($urls[5])/api/spaces/$s5Id" `
        -Method Get

    Require ($read.space_name -eq $s5Name) `
        "Student 5 READ returned created campus space"

    $space.max_capacity = 3
    $space.description = "Updated Release 2 cloud validation space."

    Invoke-CloudRequest `
        -Uri "$($urls[5])/api/spaces/$s5Id" `
        -Method Put `
        -Body $space |
    Out-Null

    $read = Invoke-CloudRequest `
        -Uri "$($urls[5])/api/spaces/$s5Id" `
        -Method Get

    Require ($read.max_capacity -eq 3) `
        "Student 5 UPDATE changed campus space"

    Invoke-CloudRequest `
        -Uri "$($urls[5])/api/spaces/$s5Id" `
        -Method Delete |
    Out-Null

    $spaces = Invoke-CloudRequest `
        -Uri "$($urls[5])/api/spaces" `
        -Method Get

    Require (
        -not (
            @($spaces) |
            Where-Object { $_.space_id -eq $s5Id }
        )
    ) "Student 5 DELETE removed campus space"

    $s5Id = $null
}
finally {
    if ($null -ne $s5Id) {
        try {
            Invoke-CloudRequest `
                -Uri "$($urls[5])/api/spaces/$s5Id" `
                -Method Delete |
            Out-Null
        }
        catch {
        }
    }
}

Write-Host "`n===== WRITING CLOUD EVIDENCE =====" -ForegroundColor Cyan

$reportDirectory = Join-Path `
    $PSScriptRoot `
    "..\..\..\reports\release2"

$reportDirectory = [System.IO.Path]::GetFullPath($reportDirectory)

New-Item `
    -ItemType Directory `
    -Path $reportDirectory `
    -Force |
Out-Null

$reportPath = Join-Path `
    $reportDirectory `
    "cloud-deployment-results.md"

$lines = @(
    "# Release 2 Integrated Azure Deployment Results"
    ""
    "- UTC validation time: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))"
    "- Resource group: $ResourceGroup"
    "- Shared home: $homeUrl"
    "- Result: PASS"
    ""
    "## Validation"
    ""
)

$lines += $Evidence | ForEach-Object {
    "- $_"
}

$lines += @(
    ""
    "## Notes"
    ""
    "- All feature requests were made through the externally exposed frontend applications."
    "- Student backends and databases remained internal Azure Container Apps."
    "- ACA scale-to-zero cold starts are retried automatically."
    "- Student 2 DELETE is a soft-delete and leaves the validation record inactive."
)

$lines |
    Set-Content `
        -Path $reportPath `
        -Encoding utf8

Write-Host "Evidence written to:" -ForegroundColor Green
Write-Host "  $reportPath"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "GROUP 22 RELEASE 2 INTEGRATED AZURE VALIDATION: PASS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green


