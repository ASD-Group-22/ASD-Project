# Student 4 Release 2 Testing Evidence

## Scope

Student 4 Skill Profile Service adds profile-grounded Multi-Agent
review through the shared server, with frontend and backend proxy
routes and a Student 4 evidence adapter.

## Automated endpoint tests

Four local tests passed for two distinct backend endpoint functions:
api_create_profile and api_get_profile.

Cases:
- Successful creation forwards the supplied payload and returns 201.
- Empty creation data returns 400 without calling the database.
- Successful retrieval forwards the profile ID and returns its data.
- Missing-profile retrieval preserves the database service's 404.

These are Flask endpoint tests with mocked database calls. They do
not prove live database persistence or external AI availability.

Test source: student-4/backend/tests/test_endpoints.py
Recorded output: reports/release2/evidence/student-4-endpoint-tests.txt

## Security checks

The staged changes passed the configured Ruff security/correctness,
detect-secrets, and pip-audit hooks.

Configuration: .pre-commit-config.yaml
Recorded output: reports/release2/evidence/student-4-security-checks.txt

These results apply to the scope selected by the configured hooks.

## Manual Multi-Agent checks

Verified:
- Backend connectivity to the shared server.
- Retrieval of profile 1 as workflow evidence.
- Successful Worker output using llama3.1:8b.
- Successful Reviewer output.
- Frontend approval publishes the accepted answer.
- Frontend correction publishes the replacement text.
- Terminal rejection returns rejected with no final response.

The initial qwen2.5:0.5b Worker returned an invalid limitations field.
Switching the Worker to llama3.1:8b produced valid output in the
subsequent observed run. Model output remains nondeterministic.

## Agentic review

The Student 4 multi-agent-review scenario passed on its first attempt:
executed 1, passed 1, failed 0, skipped 0.

Audit: ai-services/agentic-loop/evidence/agentic-validation.jsonl
Original workflows: ai-services/multi-agent-server/runtime/workflows

## CI and remaining limits

The Student 4 CI workflow includes the four endpoint tests.
Remote CI execution has not yet been verified for these changes.

Partial acceptance, full R1 regression checks, final integration,
and Student 4 cloud CRUD verification remain outstanding.