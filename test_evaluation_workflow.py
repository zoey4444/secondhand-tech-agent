"""Offline checks for evidence preservation and fair sequential comparison.

The fake model below validates orchestration only. These are not model quality
results and must never be included in a competition effectiveness score.
"""
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import evaluate
from review_record import APP_VERSION

TEST_TEMP = ROOT / ".autotest_tmp"
TEST_TEMP.mkdir(exist_ok=True)


BASE = {
    "id": "OFFLINE-01", "source_type": "离线编排测试，非效果评测",
    "label_status": "草拟，待人工复核", "expected_decision": "wait",
    "must_find": ["电池"],
    "case": {"platform": "闲鱼", "category": "手机", "model": "Apple iPhone 14",
             "price": "1800", "listing": "电池情况未知。", "chat": ""},
}


class BaselineModel:
    model_name = "offline-test-model"

    def __init__(self):
        self.calls = []

    def invoke(self, messages):
        self.calls.append(deepcopy(messages))
        return SimpleNamespace(content=f"基线自身的第{len(self.calls)}次回答：电池仍需核对。",
                               usage_metadata={"total_tokens": 23})


def agent_result(index=1):
    return {"decision": "wait", "analysis": f"Agent第{index}轮：电池待核对。",
            "issues": [{"id": f"agent-private-issue-{index}", "summary": "电池待核对"}],
            "invalid_citations": 0, "model_attempts": 1, "model_total_tokens": 17,
            "validation_incomplete": False}


class EvaluationWorkflowTests(unittest.TestCase):
    def test_multi_round_methods_keep_their_own_history(self):
        item = deepcopy(BASE)
        item["followup_replies"] = ["电池健康85%。", "刚才说错了，实际是80%。"]
        original = deepcopy(item)
        agent_inputs = []

        def run(case, llm):
            agent_inputs.append(deepcopy(case))
            return agent_result(len(agent_inputs))

        model = BaselineModel()
        with patch.object(evaluate, "run_review", side_effect=run):
            results = evaluate.run_comparison([item], model)

        self.assertEqual(item, original)
        self.assertEqual([row["round"] for row in results], [1, 2, 3])
        self.assertNotIn("seller_replies", agent_inputs[0])
        self.assertNotIn("previous_issues", agent_inputs[0])
        self.assertEqual(agent_inputs[1]["seller_replies"], item["followup_replies"][:1])
        self.assertEqual(agent_inputs[2]["seller_replies"], item["followup_replies"])
        self.assertEqual(agent_inputs[2]["previous_issues"][0]["id"], "agent-private-issue-2")
        self.assertEqual([message.type for message in model.calls[-1]],
                         ["system", "human", "ai", "human", "ai", "human"])
        baseline_context = "\n".join(str(message.content) for message in model.calls[-1])
        self.assertIn("基线自身的第1次回答", baseline_context)
        self.assertNotIn("agent-private", baseline_context)
        self.assertNotIn("Agent第", baseline_context)
        for agent_input, baseline_call in zip(agent_inputs, model.calls):
            expected = {key: value for key, value in agent_input.items() if key != "previous_issues"}
            encoded = baseline_call[-1].content.split("\n", 1)[1]
            self.assertEqual(json.loads(encoded), expected)

    def test_case_seller_replies_are_replayed_from_initial_round(self):
        item = deepcopy(BASE)
        item["case"]["seller_replies"] = ["我确认电池没有换过。"]
        with patch.object(evaluate, "run_review", return_value=agent_result()) as review:
            results = evaluate.run_comparison([item], BaselineModel())
        self.assertEqual(len(results), 2)
        self.assertNotIn("seller_replies", review.call_args_list[0].args[0])
        self.assertEqual(review.call_args_list[1].args[0]["seller_replies"], ["我确认电池没有换过。"])

    def test_record_contains_provenance_and_diagnostics_not_quality_score(self):
        item = deepcopy(BASE)
        item["followup_replies"] = ["电池健康85%。"]
        model = BaselineModel()
        model.api_key = "must-not-be-exported"
        with patch.object(evaluate, "run_review", return_value=agent_result()):
            results = evaluate.run_comparison([item], model)
        first, second = results
        self.assertEqual(first["app_version"], APP_VERSION)
        self.assertEqual(first["model"], model.model_name)
        self.assertTrue(first["timestamp_utc"].endswith("+00:00"))
        self.assertEqual(first["batch_id"], second["batch_id"])
        self.assertEqual(first["label_status"], "草拟，待人工复核")
        self.assertEqual(first["expected_decision"], "wait")
        self.assertEqual(second["expected_decision"], "")
        self.assertEqual(first["baseline_total_tokens"], 23)
        self.assertEqual(first["agent_total_tokens"], 17)
        self.assertNotIn("decision_match", first)
        self.assertNotIn("accuracy", first)
        self.assertIn("不是准确率", first["coverage_note"])
        self.assertNotIn(model.api_key, json.dumps(results))
        record = json.loads(second["agent_record_json"])
        self.assertEqual(record["round"], 2)
        self.assertEqual(record["diagnostics"]["model_attempts"], 1)
        self.assertIn("previous_issues", record["input"])

    def test_runtime_error_is_saved_and_only_its_case_stops(self):
        first = deepcopy(BASE)
        first["followup_replies"] = ["这轮不应被运行。"]
        second = deepcopy(BASE)
        second["id"] = "OFFLINE-02"
        saved = []
        with patch.object(evaluate, "run_review", side_effect=[RuntimeError("private details"), agent_result()]):
            results = evaluate.run_comparison([first, second], BaselineModel(), on_result=saved.append)
        self.assertEqual([row["case_id"] for row in results], ["OFFLINE-01", "OFFLINE-02"])
        self.assertEqual(results[0]["pair_status"], "error")
        self.assertEqual(results[0]["agent_error"], "RuntimeError")
        self.assertNotIn("private details", json.dumps(results))
        self.assertEqual(saved, results)

    def test_baseline_error_is_not_a_successful_pair(self):
        model = BaselineModel()
        model.invoke = lambda messages: (_ for _ in ()).throw(TimeoutError("sensitive connection"))
        with patch.object(evaluate, "run_review", return_value=agent_result()):
            result = evaluate.run_comparison([deepcopy(BASE)], model)[0]
        self.assertEqual(result["pair_status"], "error")
        self.assertEqual(result["baseline_error"], "TimeoutError")
        self.assertEqual(result["baseline_output"], "")

    def test_checkpoint_survives_later_interruption(self):
        second = deepcopy(BASE)
        second["id"] = "OFFLINE-02"
        with tempfile.TemporaryDirectory(dir=TEST_TEMP) as folder:
            output = Path(folder) / "partial.csv"
            with patch.object(evaluate, "run_review", side_effect=[agent_result(), KeyboardInterrupt]):
                with self.assertRaises(KeyboardInterrupt):
                    evaluate.write_comparison([deepcopy(BASE), second], BaselineModel(), output)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                saved = list(csv.DictReader(handle))
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]["case_id"], BASE["id"])
            self.assertEqual(saved[0]["agent_output"], agent_result()["analysis"])

    def test_previous_results_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP) as folder:
            output = Path(folder) / "existing.csv"
            output.write_text("existing result", encoding="utf-8")
            with patch.object(evaluate, "run_review") as review:
                with self.assertRaises(FileExistsError):
                    evaluate.write_comparison([deepcopy(BASE)], BaselineModel(), output)
            self.assertEqual(output.read_text(encoding="utf-8"), "existing result")
            review.assert_not_called()

    def test_label_readiness_reports_missing_and_unreviewed_labels(self):
        rows = evaluate.load_cases(ROOT / "evaluation_cases_30.jsonl")
        self.assertEqual(evaluate.label_readiness(rows), (6, 30, 30))

    def test_loader_rejects_invalid_expected_decision(self):
        item = deepcopy(BASE)
        item["expected_decision"] = "maybe"
        with tempfile.TemporaryDirectory(dir=TEST_TEMP) as folder:
            path = Path(folder) / "invalid-decision.jsonl"
            path.write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected_decision"):
                evaluate.load_cases(path)

    def test_loader_rejects_ambiguous_rounds_and_saved_agent_state(self):
        invalid_items = []
        item = deepcopy(BASE)
        item["case"]["previous_issues"] = []
        invalid_items.append([item])
        item = deepcopy(BASE)
        item["followup_replies"] = [""]
        invalid_items.append([item])
        item = deepcopy(BASE)
        item["followup_replies"] = ["回复"]
        item["case"]["seller_replies"] = ["另一个回复"]
        invalid_items.append([item])
        invalid_items.append([deepcopy(BASE), deepcopy(BASE)])
        invalid_items.append([["not a case object"]])
        with tempfile.TemporaryDirectory(dir=TEST_TEMP) as folder:
            path = Path(folder) / "invalid.jsonl"
            for rows in invalid_items:
                with self.subTest(rows=rows):
                    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in rows), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        evaluate.load_cases(path)


if __name__ == "__main__":
    unittest.main()
