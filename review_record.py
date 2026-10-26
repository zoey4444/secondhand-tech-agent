"""Portable review records, built from an explicit allowlist of fields."""
from datetime import datetime, timezone
from uuid import uuid4

APP_VERSION = "2.4"
INPUT_FIELDS = ("platform", "payment_channel", "category", "model", "price", "listing", "chat",
                "seller_replies", "previous_issues", "price_samples", "price_source")
OUTPUT_FIELDS = ("decision", "decision_reason", "analysis", "analysis_notice", "issues", "claims",
                 "questions", "round_changes", "price_comparison", "error")
DIAGNOSTIC_FIELDS = ("invalid_citations", "validation_errors", "initial_validation_errors",
                     "validation_incomplete", "repair_attempted", "model_attempts",
                     "model_latency_ms", "model_total_tokens", "trace")


def make_run_record(case, result, model_name, round_number=1):
    return {"schema_version": 1, "app_version": APP_VERSION, "run_id": uuid4().hex,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(), "model": model_name,
            "round": round_number,
            "input": {key: case[key] for key in INPUT_FIELDS if key in case},
            "output": {key: result[key] for key in OUTPUT_FIELDS if key in result},
            "diagnostics": {key: result[key] for key in DIAGNOSTIC_FIELDS if key in result}}
