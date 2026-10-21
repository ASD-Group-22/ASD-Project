# Release 2 Integrated Azure Deployment Results

- UTC validation time: 2026-10-21T11:28:42Z
- Resource group: lab11-rg
- Shared home: https://g22-r2-home.gentlemushroom-26567496.australiaeast.azurecontainerapps.io
- Result: PASS

## Validation

- PASS: Exactly 16 Group 22 Release 2 Container Apps exist
- PASS: All 16 Container Apps have provisioning state Succeeded
- PASS: Shared home returns HTML
- PASS: Shared home links to Student 1 Azure frontend
- PASS: Shared home links to Student 2 Azure frontend
- PASS: Shared home links to Student 3 Azure frontend
- PASS: Shared home links to Student 4 Azure frontend
- PASS: Shared home links to Student 5 Azure frontend
- PASS: Student 1 CREATE produced a project
- PASS: Student 1 READ returned created project
- PASS: Student 1 UPDATE changed project
- PASS: Student 1 DELETE removed project
- PASS: Student 2 CREATE produced a listing
- PASS: Student 2 READ returned created listing
- PASS: Student 2 UPDATE changed listing
- PASS: Student 2 DELETE soft-deactivated listing
- PASS: Student 2 inactive listing is excluded from active collection
- PASS: Student 3 CREATE produced a group
- PASS: Student 3 READ returned created group
- PASS: Student 3 UPDATE changed group members
- PASS: Student 3 DELETE removed group
- PASS: Student 4 CREATE returned a profile ID
- PASS: Student 4 READ returned created profile
- PASS: Student 4 UPDATE changed profile skill
- PASS: Student 4 DELETE completed successfully
- PASS: Student 5 CREATE produced a campus space
- PASS: Student 5 READ returned created campus space
- PASS: Student 5 UPDATE changed campus space
- PASS: Student 5 DELETE removed campus space

## Notes

- All feature requests were made through the externally exposed frontend applications.
- Student backends and databases remained internal Azure Container Apps.
- ACA scale-to-zero cold starts are retried automatically.
- Student 2 DELETE is a soft-delete and leaves the validation record inactive.

## GitHub Actions Deployment

- Workflow run: https://github.com/ASD-Group-22/ASD-Project/actions/runs/39589826282
- Commit: f18c9175457e54423db1214b37e9a57e433c63fa
- Image tag: release2-f18c917
- Resource group: lab11-rg
- Container Apps environment: lab11-env-31080-standard
- Registry: lab11registry3098
