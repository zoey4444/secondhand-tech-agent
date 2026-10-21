"""Run a same-model comparison on consented or clearly synthetic JSONL cases.

Example: python evaluate.py --input sample_cases.jsonl --output comparison.csv
This script makes paid model calls. It does not run when the app starts.
"""

import argparse
import csv
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent_core import run_review
from domain_knowledge import CATEGORY_CHECKLIST, transaction_guidance


def load_cases(path: Path) -> list[dict]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row.get("case"), dict) or not isinstance(row.get("must_find", []), list):
            raise ValueError(f"第 {line_number} 行缺少 case 或 must_find")
        cases.append(row)
    return cases


def coverage(text: str, labels: list[str]) -> str:
    if not labels:
        return ""
    return f"{sum(label in text for label in labels)}/{len(labels)}"


def run_comparison(rows: list[dict], llm) -> list[dict]:
    results = []
    for item in rows:
        case = item["case"]
        enriched_case = {**case, "category_guidance": CATEGORY_CHECKLIST.get(case.get("category", ""), ""),
                         "platform_guidance": transaction_guidance(case)}
        expected = item.get("expected_decision", "")
        labels = [str(label) for label in item.get("must_find", [])]
        started = time.perf_counter()
        agent = run_review(enriched_case, llm)
        agent_seconds = round(time.perf_counter() - started, 2)
        direct_prompt = (
            "你是二手数码购前核验助手。阅读以下材料，指出应核实的具体疑点、依据和最多三个追问；"
            "不要鉴定真伪，不要把卖家承诺当成事实。请用买家能直接发送的自然语言写追问。\n"
            + json.dumps(enriched_case, ensure_ascii=False)
        )
        started = time.perf_counter()
        try:
            baseline = llm.invoke([SystemMessage(content="你是谨慎的二手数码交易辅助顾问。"),
                                   HumanMessage(content=direct_prompt)])
            baseline_text = str(baseline.content)
            baseline_error = ""
        except Exception as exc:
            baseline_text = ""
            baseline_error = type(exc).__name__
        baseline_seconds = round(time.perf_counter() - started, 2)
        output = agent.get("analysis", "")
        results.append({"case_id": item.get("id", ""), "source_type": item.get("source_type", ""),
                        "scenario": item.get("scenario", ""), "expected_focus": item.get("expected_focus", ""),
                        "label_status": item.get("label_status", ""),
                        "expected_decision": expected, "agent_decision": agent.get("decision", "error"),
                        "decision_match": int(expected == agent.get("decision")) if expected else "",
                        "agent_label_coverage": coverage(output, labels),
                        "baseline_label_coverage": coverage(baseline_text, labels),
                        "agent_invalid_citations": agent.get("invalid_citations", ""),
                        "agent_seconds": agent_seconds, "baseline_seconds": baseline_seconds,
                        "agent_error": agent.get("error", ""), "baseline_error": baseline_error,
                        "agent_output": output, "baseline_output": baseline_text})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true", help="只检查案例格式，不调用模型")
    parser.add_argument("--ids", nargs="+", help="只运行指定案例编号，例如 --ids T01 T08")
    parser.add_argument("--env-file", type=Path, help="从指定的本地 .env 读取密钥，不会输出密钥内容")
    args = parser.parse_args()
    cases = load_cases(args.input)
    if args.ids:
        wanted = set(args.ids)
        cases = [item for item in cases if item.get("id") in wanted]
        if len(cases) != len(wanted):
            parser.error("有案例编号未在输入文件中找到")
    if args.validate_only:
        print(f"案例格式检查通过：{len(cases)} 条；未调用模型。")
        return
    if args.output is None:
        parser.error("正式对照运行必须指定 --output")
    load_dotenv(dotenv_path=args.env_file)
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise SystemExit("请先在本地 .env 配置 DEEPSEEK_API_KEY；不要把密钥写进案例文件。")
    llm = ChatOpenAI(model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"), api_key=key,
                     base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                     temperature=0.1, timeout=35, max_retries=0)
    rows = run_comparison(cases, llm)
    if rows:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f"完成 {len(rows)} 条案例；结果已写入 {args.output}。请人工复核引用和结论。")


if __name__ == "__main__":
    main()
