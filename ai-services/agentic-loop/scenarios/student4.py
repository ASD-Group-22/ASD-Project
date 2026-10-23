"""Student 4 - Skill Profile agentic validation scenarios.

Feature-owned scenarios executed by the single shared Release 1
Plan -> Act -> Observe -> Adapt validation loop.
"""

FEATURE = "student-4-skill-profile"


def get_scenarios():
    """Return Student 4 MCP and RAG validation scenarios."""

    return {
        "mcp": [
            {
                "id": "student4_mcp_profile_4",
                "feature": FEATURE,
                "description": (
                    "Retrieve Skill Profile 4 through the "
                    "shared Student 4 MCP tool."
                ),
                "action": "call_tool",
                "tool": "student4_get_skill_profile",
                "arguments": {
                    "profile_id": 4,
                },
                "expected": {
                    "success": True,
                    "profile_id": 4,
                    "profile_student_id": 4,
                    "profile_skills_include": [
                        "Python",
                        "Flask",
                    ],
                },
            },
            {
                "id": "student4_mcp_invalid_profile",
                "feature": FEATURE,
                "description": (
                    "Verify Student 4 MCP rejects an invalid "
                    "profile ID clearly."
                ),
                "action": "call_tool",
                "tool": "student4_get_skill_profile",
                "arguments": {
                    "profile_id": 0,
                },
                "expected": {
                    "success": False,
                    "error": (
                        "profile_id must be a positive integer"
                    ),
                },
            },
        ],
        "rag": [
            {
                "id": "student4_rag_retrieve_profile_4",
                "feature": FEATURE,
                "description": (
                    "Retrieve trusted Skill Profile context "
                    "for profile 4."
                ),
                "action": "retrieve",
                "request": {
                    "query": (
                        "Skill Profile ID 4 Python Flask"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "minimum_results": 1,
                    "source_prefix": "student-4:",
                },
            },
            {
                "id": "student4_rag_grounded_profile_4",
                "feature": FEATURE,
                "description": (
                    "Generate a grounded answer describing "
                    "Skill Profile 4."
                ),
                "action": "answer",
                "request": {
                    "query": (
                        "What skills are listed for "
                        "Skill Profile ID 4?"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "answer_required": True,
                    "minimum_citations": 1,
                    "citation_source_prefix": "student-4:",
                    "confidence_required": True,
                },
            },
            {
                "id": "student4_rag_insufficient_context",
                "feature": FEATURE,
                "description": (
                    "Verify an unsupported question does not "
                    "produce a fabricated Skill Profile answer."
                ),
                "action": "answer",
                "request": {
                    "query": (
                        "What is the exact final exam mark "
                        "of student 999999 in year 2099?"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "insufficient_context",
                    "answer": "Insufficient context.",
                    "citation_count": 0,
                    "confidence_category": "Insufficient",
                },
            },
        ],
        "multi-agent-review": [
            {
                "id": "student4_multi_agent_workflow_review",
                "feature": FEATURE,
                "review_title": "Student 4 Multi-Agent Workflow Review",
                "description": (
                    "Review a real Student 4 workflow for agent outputs, "
                    "profile evidence, and human review."
                ),
                "review": {
                    "feature": "student4",
                    "workflow_dir": (
                        "ai-services/multi-agent-server/runtime/workflows"
                    ),
                },
            },
        ],
                "testing-report-review": [
            {
                "id": "student4_testing_report_review",
                "feature": FEATURE,
                "review_title": "Student 4 Testing Report Review",
                "description": (
                    "Review Student 4 test and security evidence "
                    "and identify unsupported claims or missing checks."
                ),
                "review": {
                    "primary_path": (
                        "reports/release2/student-4-testing-report.md"
                    ),
                    "supplemental_paths": [
                        ".pre-commit-config.yaml",
                        ".github/workflows/student-4-ci.yml",
                        "student-4/backend/tests/test_endpoints.py",
                        "reports/release2/evidence/student-4-endpoint-tests.txt",
                        "reports/release2/evidence/student-4-security-checks.txt",
                    ],
                },
            },
        ],
        "cloud-deployment-review": [
            {
                "id": "student4_cloud_deployment_review",
                "feature": FEATURE,
                "review_title": "Student 4 Cloud Deployment Review",
                "description": (
                    "Review shared cloud deployment evidence for "
                    "Student 4 CRUD and disabled-by-default AI services."
                ),
                "review": {
                    "primary_path": (
                        "reports/release2/cloud-deployment-report.md"
                    ),
                    "supplemental_paths": [
                        ".github/workflows/cloud-deployment.yml",
                        "reports/release2/cloud-deployment-results.md",
                        "scripts/cloud/azure/deploy-backends.sh",
                        "scripts/cloud/azure/SERVICE_MAP.md",
                    ],
                },
            },
        ],
    }
