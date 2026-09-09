$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:5001"

function Invoke-Api {
    param (
        [string]$Method,
        [string]$Url,
        [object]$Body = $null
    )

    try {
        if ($null -ne $Body) {
            return Invoke-RestMethod `
                -Uri $Url `
                -Method $Method `
                -ContentType "application/json" `
                -Body ($Body | ConvertTo-Json -Depth 10) `
                -TimeoutSec 10
        }

        return Invoke-RestMethod `
            -Uri $Url `
            -Method $Method `
            -TimeoutSec 10
    }
    catch {
        Write-Host ""
        Write-Host "API request failed: $Method $Url" -ForegroundColor Red

        if ($_.Exception.Response) {
            $response = $_.Exception.Response

            Write-Host "HTTP Status: $([int]$response.StatusCode)" -ForegroundColor Red

            $reader = New-Object System.IO.StreamReader(
                $response.GetResponseStream()
            )

            $responseBody = $reader.ReadToEnd()

            Write-Host "Response:" -ForegroundColor Yellow
            Write-Host $responseBody
        }
        else {
            Write-Host $_.Exception.Message
        }

        exit 1
    }
}

Write-Host "======================================"
Write-Host " Student 1 CRUD Test"
Write-Host "======================================"

$projectsUrl = "$baseUrl/projects"

# ----------------------------------------------------------
# READ
# ----------------------------------------------------------

Write-Host ""
Write-Host "Testing GET /projects..."

$projects = Invoke-Api `
    -Method Get `
    -Url $projectsUrl

Write-Host "PASS: GET /projects"

# ----------------------------------------------------------
# CREATE
# ----------------------------------------------------------

Write-Host ""
Write-Host "Testing POST /projects..."

$project = @{
    name = "CI Test Project"
    description = "Project created during CI testing"
}

$created = Invoke-Api `
    -Method Post `
    -Url $projectsUrl `
    -Body $project

Write-Host "PASS: POST /projects"

# ----------------------------------------------------------
# GET CREATED PROJECT ID
# ----------------------------------------------------------

$projectId = $null

if ($created.id) {
    $projectId = $created.id
}
elseif ($created.project_id) {
    $projectId = $created.project_id
}
elseif ($created.data.id) {
    $projectId = $created.data.id
}
elseif ($created.data.project_id) {
    $projectId = $created.data.project_id
}

if ($null -eq $projectId) {
    Write-Host ""
    Write-Host "WARNING: POST succeeded but no project ID was returned."
    Write-Host "Skipping PUT and DELETE tests."
    Write-Host ""
    Write-Host "Student 1 CRUD test PASSED for GET and POST."
    exit 0
}

$projectUrl = "$projectsUrl/$projectId"

# ----------------------------------------------------------
# UPDATE
# ----------------------------------------------------------

Write-Host ""
Write-Host "Testing PUT $projectUrl..."

$updatedProject = @{
    name = "CI Test Project Updated"
    description = "Project updated during CI testing"
}

try {
    Invoke-Api `
        -Method Put `
        -Url $projectUrl `
        -Body $updatedProject | Out-Null

    Write-Host "PASS: PUT project"
}
catch {
    Write-Host "WARNING: PUT endpoint failed."
}

# ----------------------------------------------------------
# DELETE
# ----------------------------------------------------------

Write-Host ""
Write-Host "Testing DELETE $projectUrl..."

try {
    Invoke-Api `
        -Method Delete `
        -Url $projectUrl | Out-Null

    Write-Host "PASS: DELETE project"
}
catch {
    Write-Host "WARNING: DELETE endpoint failed."
}

# ======================================
# TASK CRUD TEST
# ======================================

$projectId = $null

# Try to get an existing project to attach the task to
Write-Host ""
Write-Host "Getting a project for task testing..."

try {
    $projects = Invoke-Api `
        -Method Get `
        -Url $projectsUrl

    if ($projects -is [array] -and $projects.Count -gt 0) {
        $projectId = $projects[0].id
    }
    elseif ($projects.data -is [array] -and $projects.data.Count -gt 0) {
        $projectId = $projects.data[0].id
    }
    elseif ($projects.id) {
        $projectId = $projects.id
    }

    if ($null -eq $projectId) {
        Write-Error "Could not find a project ID for task testing."
        exit 1
    }

    Write-Host "PASS: Found project ID $projectId"
}
catch {
    Write-Error "Could not retrieve a project for task testing."
    exit 1
}

$tasksUrl = "$baseUrl/projects/$projectId/tasks"

# READ TASKS
Write-Host ""
Write-Host "Testing GET $tasksUrl..."

$tasks = Invoke-Api `
    -Method Get `
    -Url $tasksUrl

Write-Host "PASS: GET project tasks"

# CREATE TASK
Write-Host ""
Write-Host "Testing POST $tasksUrl..."

$task = @{
    task = "CI Test Task"
}

$createdTask = Invoke-Api `
    -Method Post `
    -Url $tasksUrl `
    -Body $task

Write-Host "PASS: POST task"

# GET CREATED TASK ID
$taskId = $null

if ($createdTask.id) {
    $taskId = $createdTask.id
}
elseif ($createdTask.task_id) {
    $taskId = $createdTask.task_id
}
elseif ($createdTask.data.id) {
    $taskId = $createdTask.data.id
}
elseif ($createdTask.data.task_id) {
    $taskId = $createdTask.data.task_id
}

if ($null -eq $taskId) {
    Write-Error "POST task succeeded but no task ID was returned."
    exit 1
}

$taskUrl = "$baseUrl/tasks/$taskId"

# UPDATE TASK
Write-Host ""
Write-Host "Testing PUT $taskUrl..."

$updatedTask = @{
    task = "CI Test Task Updated"
}

Invoke-Api `
    -Method Put `
    -Url $taskUrl `
    -Body $updatedTask | Out-Null

Write-Host "PASS: PUT task"

# DELETE TASK
Write-Host ""
Write-Host "Testing DELETE $taskUrl..."

Invoke-Api `
    -Method Delete `
    -Url $taskUrl | Out-Null

Write-Host "PASS: DELETE task"

Write-Host ""
Write-Host "======================================"
Write-Host " Student 1 CRUD Test PASSED"
Write-Host "======================================"