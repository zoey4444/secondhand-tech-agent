"""Compare a listed price with user-provided, comparable used-listing samples."""
from __future__ import annotations

import re
from statistics import median


def compare_prices(case: dict) -> dict:
    raw = str(case.get("price_samples") or "").strip()
    if not raw:
        return {"status": "not_provided",
                "summary": "还没有同款二手参考价，暂时无法判断标价与同款挂牌样本的差异。"}
    parts = [part.strip() for part in re.split(r"[,，;；\s]+", raw) if part.strip()]
    if len(parts) > 5 or any(not re.fullmatch(r"[￥¥]?\d+(?:\.\d{1,2})?", part) for part in parts):
        return {"status": "invalid", "summary": "参考价请填 3 至 5 个正数，用逗号分隔，例如 450，480，500。"}
    samples = [float(part.lstrip("￥¥")) for part in parts]
    if any(value <= 0 for value in samples):
        return {"status": "invalid", "summary": "参考价必须大于 0 元。"}
    if len(samples) < 3:
        return {"status": "insufficient", "sample_count": len(samples),
                "summary": "目前只有少于 3 个同款报价；再补几个样本，才适合做价格对比。"}
    listed_raw = str(case.get("price") or "").strip()
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", listed_raw):
        return {"status": "no_listing_price", "sample_count": len(samples),
                "summary": "商品没有明确的数字标价，无法与同款二手报价比较。"}
    listed = float(listed_raw)
    midpoint = median(samples)
    difference = (listed / midpoint - 1) * 100
    label = '低于样本中位数' if difference < 0 else '高于样本中位数' if difference > 0 else '等于样本中位数'
    source = str(case.get("price_source") or "").strip()[:180]
    origin = f"来源和查看日期：{source}。" if source else "未注明样本来源和查看日期，参考性有限。"
    summary = (f"商品标价 {listed:g} 元；你提供的 {len(samples)} 条同款二手挂牌价"
               f"范围 {min(samples):g}–{max(samples):g} 元，中位数 {midpoint:g} 元。"
               f"标价{label}（相对中位数 {difference:+.0f}%）。{origin}"
               "请确认型号、容量/版本、成色和配件是否可比；挂牌价不等于实际成交价。")
    return {"status": "compared", "sample_count": len(samples), "sample_min": min(samples),
            "sample_max": max(samples), "sample_median": midpoint,
            "listed_price": listed, "difference_percent": round(difference, 1),
            "label": label, "source": source, "summary": summary}
