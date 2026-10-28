# Release 2 Evidence Index

This file indexes the principal Release 2 implementation and assessment evidence for Group 22.

## Final Validation Baseline

Final software-changing commit:

`9d623239f4e30840b00e5ef221702114317a519c`

Successful final integration workflow:

- Workflow: `Release 2 - Integration CI`
- Run: `39973124752`
- Result: PASS
- Branch: `release2/final-integration`

Later commits update documentation/evidence only.

## 1. Integrated Local Application

Primary configuration:

- `docker-compose.yml`
- `shared/`
- `student-1/`
- `student-2/`
- `student-3/`
- `student-4/`
- `student-5/`

The integrated local application contains the unified home page and all five frontend, backend/API, and database microservice sets.

## 2. Shared Multi-Agent Server

Implementation:

- `ai-services/multi-agent-server/`

Feature adapters:

- `ai-services/multi-agent-server/adapters/student1.py`
- `ai-services/multi-agent-server/adapters/student2.py`
- `ai-services/multi-agent-server/adapters/student3.py`
- `ai-services/multi-agent-server/adapters/student4.py`
- `ai-services/multi-agent-server/adapters/student5.py`

Required flow:

`Planner -> Worker -> Reviewer -> Human Review`

Committed workflow evidence:

- `reports/release2/evidence/workflow-5c3695bf-7921-4367-b371-f7179a006be9.json`
- `reports/release2/evidence/workflow-77cf1613-b732-41a2-8974-e64bdec772d5.json`
- `reports/release2/evidence/workflow-b138eeeb-8960-4f80-aef7-b754f05a5c26.json`
- `reports/release2/evidence/workflow-c5f23592-3390-43f9-beda-02659d6af279.json`

## 3. Pre-Commit Security Testing

Configuration:

- `.pre-commit-config.yaml`
- `ruff.toml`

Student evidence:

### Student 1
- `reports/release2/evidence/student-1-security-checks-initial.txt`
- `reports/release2/evidence/student-1-security-checks-final.txt`

### Student 2
- `reports/release2/evidence/student-2-security-checks-final.txt`

### Student 3
- `reports/release2/evidence/student-3-security-checks-initial.txt`
- `reports/release2/evidence/student-3-security-checks-final.txt`

### Student 4
- `reports/release2/evidence/student-4-security-checks-initial.txt`
- `reports/release2/evidence/student-4-security-checks-final.txt`

### Student 5
- `reports/release2/evidence/student-5-security-checks-initial.txt`
- `reports/release2/evidence/student-5-security-checks-final.txt`

Final security validation uses:

- Ruff security/correctness rules
- detect-secrets
- pip-audit

## 4. Post-Commit Endpoint CI/CD Testing

Testing reports:

- `reports/release2/student-1-testing-report.md`
- `reports/release2/student-2-testing-report.md`
- `reports/release2/student-3-testing-report.md`
- `reports/release2/student-4-testing-report.md`
- `reports/release2/student-5-testing-report.md`

Successful final student workflow runs:

| Student | Run | Result |
| --- | ---: | --- |
| Student 1 | `39972587866` | PASS |
| Student 2 | `39973749169` | PASS |
| Student 3 | `39972587659` | PASS |
| Student 4 | `39972587459` | PASS |
| Student 5 | `39972587538` | PASS |

Each assigned student workflow tests two backend/API endpoint functions as required by Release 2.

## 5. Agentic-Loop Review Modes

Implementation:

- `ai-services/agentic-loop/`

Committed Release 2 agentic review evidence:

- `reports/release2/evidence/student-4-agentic-reviews.jsonl`

This committed validation evidence contains successful Release 2 runs for:

- Multi-Agent Workflow Review
- Testing Report Review
- Cloud Deployment Report Review

## 6. Cloud Deployment

Cloud platform:

Microsoft Azure Container Apps

Workflow:

- `.github/workflows/cloud-deployment.yml`

Reusable deployment scripts:

- `scripts/cloud/azure/`

Deployment evidence:

- `reports/release2/cloud-deployment-report.md`
- `reports/release2/cloud-deployment-results.md`

The cloud deployment report also records the final human release decision after review of the deployment and agentic-loop evidence.

Successful Azure deployment evidence includes the integrated frontend, backend/API, and database services with required baseline AI services disabled.

## 7. Release 2 Testing Reports

Per-student reports:

- `reports/release2/student-1-testing-report.md`
- `reports/release2/student-2-testing-report.md`
- `reports/release2/student-3-testing-report.md`
- `reports/release2/student-4-testing-report.md`
- `reports/release2/student-5-testing-report.md`

## 8. Final Integration Evidence

Final validated software commit:

`9d623239f4e30840b00e5ef221702114317a519c`

Final successful integration workflow:

`39973124752`

Final integration result:

`PASS`
