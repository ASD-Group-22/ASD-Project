"""Student 3 reviewer provenance, output repair and shared-path regression tests."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests


ROOT = Path(__file__).resolve().parents[2]
SERVER_ROOT = ROOT / "ai-services" / "multi-agent-server"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, "path", [str(SERVER_ROOT), *sys.path]):
        spec.loader.exec_module(module)
    return module


def inputs(with_gap=True):
    requirements = {"python": {"level": "intermediate"}}
    if with_gap:
        requirements["docker"] = {"level": "beginner"}
    profiles = [
        {"student_id": 1, "skills": {"python": 2}},
        {"student_id": 2, "skills": {"python": 1}},
        {"student_id": 3, "skills": {"python": 1}},
    ]
    evidence = {
        "feature": "student3",
        "requirements": requirements,
        "profiles": profiles,
        "request_context": {"subject": "ASD", "group_size": 3, "student_ids": [1, 2, 3]},
        "deterministic_group_proposal": [{
            "group_name": "ASD Group 1",
            "member_student_ids": [1, 2, 3],
            "covered_required_skills": ["python"],
            "missing_required_skills": ["docker"] if with_gap else [],
        }],
        "allowed_output_references": ["requirements:ASD", "profile:1", "profile:2", "profile:3"],
    }
    worker = {
        "status": "success",
        "result": {
            "answer": "ASD Group 1: students 1, 2, 3; covers python."
            + (" Docker is not covered." if with_gap else ""),
            "selected_references": evidence["allowed_output_references"],
            "limitations": ["Only recorded profiles were used."],
        },
    }
    planner = {"status": "success", "plan": {
        "objective": "Balance recorded skills for ASD",
        "steps": ["Read requirements and profiles", "Check each proposed group"],
    }}
    return planner, evidence, worker


def model_output(decision="approve", plan_followed=True, evidence_grounded=True, findings=None):
    return json.dumps({
        "decision": decision,
        "plan_followed": plan_followed,
        "evidence_grounded": evidence_grounded,
        "finding_ids": findings or [],
    })


class ReviewerReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.adapter = load_module(SERVER_ROOT / "adapters" / "student3.py", "student3_review_test")
        self.planner, self.evidence, self.worker = inputs()

    def run_review(self, outputs):
        with patch.object(self.adapter, "_model_review", side_effect=outputs) as model:
            result = self.adapter.review_work("Balance ASD", self.planner, self.evidence, self.worker)
        return result, model

    def test_real_model_decision_is_success_and_keeps_model_judgments(self):
        result, model = self.run_review([model_output()])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model_response_status"], "valid")
        self.assertEqual(result["review"]["source"], "student3_llama_reviewer")
        self.assertEqual(result["review"]["decision"], "approve")
        self.assertTrue(result["review"]["plan_followed"])
        self.assertTrue(result["review"]["evidence_grounded"])
        self.assertEqual(model.call_count, 1)

    def test_disclosed_unavoidable_gaps_do_not_invalidate_approval(self):
        result, _ = self.run_review([model_output()])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["review"]["decision"], "approve")
        self.assertIn("ASD Group 1 is missing recorded required skills: docker.", result["review"]["issues"])
        self.assertTrue(any("cannot contain a different provider" in issue for issue in result["review"]["issues"]))

    def test_reviewer_can_still_choose_revise_or_reject_with_supported_findings(self):
        for decision in ("revise", "reject"):
            with self.subTest(decision=decision):
                result, _ = self.run_review([model_output(decision, findings=["evidence_warning_1"])])
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["review"]["decision"], decision)

    def test_bad_json_retries_only_model_review_then_keeps_valid_result(self):
        result, model = self.run_review(['{"error":"No matching group found"}', model_output()])
        self.assertEqual(model.call_count, 2)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["model_response_status"], "valid_after_retry")
        self.assertEqual(result["attempts"][0]["status"], "invalid_output")
        self.assertIn("No matching group", result["attempts"][0]["untrusted_model_output"])
        self.assertIn("Repair the review JSON", model.call_args.args[0][-1]["content"])

    def test_two_bad_outputs_are_fallback_not_success_or_invented_model_decision(self):
        result, model = self.run_review(['{"error":"No matching group found"}'] * 2)
        self.assertEqual(model.call_count, 2)
        self.assertEqual(result["status"], "fallback")
        self.assertEqual(result["model_response_status"], "invalid_output")
        self.assertEqual(result["review"]["source"], "student3_evidence_guardrail")
        self.assertEqual(result["review"]["decision"], "needs_human_review")
        self.assertIsNone(result["review"]["plan_followed"])
        self.assertIsNone(result["review"]["evidence_grounded"])
        self.assertIn("invalid decision", result["fallback_reason"])

    def test_unavailable_model_does_not_retry_or_report_success(self):
        for error in (requests.ConnectionError("offline"), requests.Timeout("timed out")):
            with self.subTest(error=error):
                result, model = self.run_review([error])
                self.assertEqual(model.call_count, 1)
                self.assertEqual(result["status"], "fallback")
                self.assertEqual(result["model_response_status"], "unavailable")

    def test_invalid_membership_cannot_receive_model_approval(self):
        self.evidence["deterministic_group_proposal"][0]["member_student_ids"] = [1, 1, 99]
        result, _ = self.run_review([model_output()] * 2)
        self.assertEqual(result["status"], "fallback")
        self.assertTrue(any("repeats student IDs" in issue for issue in result["review"]["issues"]))
        self.assertTrue(any("outside the selected evidence" in issue for issue in result["review"]["issues"]))

    def test_unsupported_references_cannot_receive_model_approval(self):
        self.worker["result"]["selected_references"] = ["profile:999"]
        result, _ = self.run_review([model_output()] * 2)
        self.assertEqual(result["status"], "fallback")
        self.assertTrue(any("unsupported evidence references" in issue for issue in result["review"]["issues"]))

    def test_reviewer_can_report_false_judgments_without_adapter_overwriting_them(self):
        result, _ = self.run_review([model_output(
            "revise", plan_followed=False, evidence_grounded=False,
            findings=["check_plan_alignment", "check_worker_claims"],
        )])
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["review"]["plan_followed"])
        self.assertFalse(result["review"]["evidence_grounded"])

    def test_invented_findings_and_wrong_types_are_not_accepted(self):
        invalid_outputs = [
            model_output("revise", findings=["Invent a new student"]),
            model_output(plan_followed="true"),
            model_output("revise"),
            'not json',
            '[]',
        ]
        for invalid in invalid_outputs:
            with self.subTest(output=invalid):
                result, _ = self.run_review([invalid] * 2)
                self.assertEqual(result["status"], "fallback")

    def test_evidence_does_not_change_between_attempts(self):
        before = copy.deepcopy((self.planner, self.evidence, self.worker))
        self.run_review(['{"error":"invalid"}', model_output()])
        self.assertEqual(before, (self.planner, self.evidence, self.worker))

    def test_compact_prompt_contains_actual_worker_plan_schema_and_evidence(self):
        result, model = self.run_review([model_output()])
        messages, schema, _ = model.call_args.args
        payload = json.loads(messages[1]["content"])
        self.assertEqual(payload["planner"], self.planner)
        self.assertEqual(payload["worker"], self.worker)
        self.assertEqual(payload["requirements"], self.evidence["requirements"])
        self.assertIn("RESPONSE JSON SCHEMA", messages[0]["content"])
        self.assertIn("finding_ids", schema["properties"])
        self.assertTrue(schema["properties"]["finding_ids"]["items"]["enum"])
        self.assertEqual(result["status"], "success")

    def test_ollama_call_preserves_shared_model_configuration_and_enforces_schema(self):
        response = Mock()
        response.json.return_value = {"message": {"content": model_output()}}
        schema = self.adapter._review_schema(self.adapter._finding_catalog(
            self.adapter._validation_summary(self.planner, self.evidence, self.worker)
        ))
        with patch.object(self.adapter.requests, "post", return_value=response) as post:
            raw = self.adapter._model_review([{"role": "user", "content": "Review"}], schema, 40.0)
        self.assertEqual(raw, model_output())
        self.assertEqual(post.call_args.args[0], self.adapter.OLLAMA_URL + "/api/chat")
        self.assertEqual(post.call_args.kwargs["json"]["model"], self.adapter.REVIEWER_MODEL)
        self.assertEqual(post.call_args.kwargs["json"]["format"], schema)
        self.assertEqual(post.call_args.kwargs["timeout"], (5.0, 40.0))

    def test_review_time_budget_prevents_extra_calls(self):
        with patch.object(self.adapter, "monotonic", side_effect=[0.0, 0.0, 999.0]):
            result, model = self.run_review(['{"error":"invalid"}'])
        self.assertEqual(model.call_count, 1)
        self.assertEqual(result["status"], "fallback")
        self.assertIn("time budget", result["fallback_reason"])

    def test_other_student_review_paths_still_use_original_shared_reviewer(self):
        coordinator = load_module(SERVER_ROOT / "coordinator.py", "student3_hook_test")
        sentinel = {"status": "success", "review": {"decision": "approve"}}
        for feature in ("student1", "student2", "student4", "student5"):
            with self.subTest(feature=feature):
                adapter = SimpleNamespace(feature=feature)
                with patch.object(coordinator, "review_with_shared_agent", return_value=sentinel) as shared:
                    result = coordinator._review_with_feature_hook(
                        adapter, "Other student's request", self.planner, {}, self.worker,
                    )
                self.assertIs(result, sentinel)
                shared.assert_called_once_with("Other student's request", self.planner, {}, self.worker)

    def test_student3_hook_keeps_fallback_status_in_saved_workflow(self):
        coordinator = load_module(SERVER_ROOT / "coordinator.py", "student3_saved_review_test")
        fallback = {
            "status": "fallback", "agent": "reviewer", "model": "test-reviewer",
            "review": {"decision": "needs_human_review", "source": "student3_evidence_guardrail"},
        }
        adapter = SimpleNamespace(gather_evidence=lambda *args: self.evidence, review_work=lambda *args: fallback)
        history = []

        def append_history(workflow, stage, message, details=None):
            history.append((stage, details))

        with patch.multiple(
            coordinator,
            load_adapter=Mock(return_value=adapter),
            plan_workflow=Mock(return_value=self.planner),
            perform_work=Mock(return_value=self.worker),
            save_workflow=Mock(), append_audit=Mock(), append_history=append_history,
        ):
            workflow = coordinator.create_workflow(
                feature="student3", task_type="group_formation_recommendation",
                user_request="Balance ASD", context={"subject": "ASD"},
            )
        self.assertEqual(workflow["reviewer"]["status"], "fallback")
        self.assertEqual(workflow["status"], "awaiting_human_review")
        reviewer_history = [details for stage, details in history if stage == "reviewer"]
        self.assertEqual(reviewer_history[0]["status"], "fallback")


if __name__ == "__main__":
    unittest.main()
