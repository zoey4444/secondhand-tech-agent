"""Shared presentation labels and buyer-message normalization."""
import re

STATUS_LABELS = {
    "open": "待核实", "unanswered": "尚未回答",
    "answered_claim_only": "卖家已说明，尚未核实",
    "contradicted": "两处说法不一致",
    "awaiting_independent_evidence": "上轮疑点仍待核实",
}


def source_label(name):
    if name.startswith("reply_"):
        return f"第 {name.split('_')[-1]} 次卖家回复"
    return {"platform": "展示渠道", "payment_channel": "下单付款渠道",
            "model": "所填型号", "category": "品类", "price": "所填标价",
            "listing": "商品描述", "chat": "聊天记录"}.get(name, "提交材料")


def natural_question(text):
    text = re.sub(r"^\s*(?:[-*•]\s*|\d+[.)、]\s*)", "", text).replace("**", "").strip()
    text = re.sub(r"^(?:你好|您好)[，,！!。]?\s*", "", text)
    text = text.replace("请卖家", "").replace("能否提供", "方便发一下").replace("请提供", "方便发一下")
    text = re.sub(r"^(?:请明确|请确认)", "想确认一下", text)
    text = text.replace("是否", "是不是")
    # Avoid requesting procedures/metrics that may be unavailable or damaging.
    if re.search(r"浸水|泡水|清水.{0,8}测试", text):
        return "之前有进水或维修过吗？方便说明使用情况，并当面检查屏幕、按键和充电吗？"
    if re.search(r"(?:官网|官方|序列号).{0,18}(?:查询|查验).{0,10}激活锁", text):
        return "方便在交付前退出账号，重置后当面确认能正常设置和激活吗？"
    text = text.rstrip("。；; ")
    return text + ("" if not text or text.endswith(("？", "?", "！", "!")) else "？")


def unique_questions(questions):
    result, seen = [], set()
    for raw in questions:
        question = natural_question(raw)
        if not question:
            continue
        key = re.sub(r"\W", "", question)
        if re.search(r"原盒|收纳包|配件|随货", question) and re.search(r"随货|清单|合照|包含|发出|都带|哪些", question):
            key = "delivery_contents"
        elif re.search(r"取消配对|初始配对|抹掉.*内容", question):
            key = "unpair_and_setup"
        elif re.search(r"最终成交价|最后按多少钱|现在报价是", question):
            key = "final_price"
        if key not in seen:
            result.append(question)
            seen.add(key)
    return result[:3]


def device_question(question, case):
    model = str(case.get("model", "")).lower().replace(" ", "")
    if "iphone14" in model and "循环" in question:
        return "方便发一下本机能显示的电池健康或最大容量页面，并说一下有没有换过电池吗？"
    if "mac" in model and re.search(r"m[1-9]", model) and "固件密码" in question:
        return "交付前方便退出账号、重置机器，并当面确认能正常设置和登录吗？"
    if "原彩" in question and re.search(r"证明|确认.{0,6}原装", question):
        return "屏幕换过或修过吗？方便提供维修记录或检测结果吗？"
    return question
