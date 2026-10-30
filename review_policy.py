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
            "listing": "商品描述", "chat": "聊天记录", "seller_profile": "用户提供的卖家主页材料"}.get(name, "提交材料")


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


def _final_price_question(question):
    return bool(re.search(
        r"成交(?:价格|价|金额)|(?:多少钱|哪个价格|多少元).{0,8}成交|"
        r"(?:按|以).{0,15}(?:价格|金额|元).{0,5}成交|"
        r"最终(?:价格|价)|最后按.{0,12}(?:多少|哪个|哪一)|现在报价是|"
        r"(?:标价|报价|售价).{0,35}(?:按哪|为准|多少)", question))


def _order_update_question(question):
    return "订单" in question and bool(re.search(r"改|更新|写|调整|同步", question))


def _merge_price_questions(first, second):
    # Keep the concrete conflicting prices rather than the generic rule question.
    def detail_score(question):
        amounts = set(re.findall(r"\d+(?:\.\d+)?\s*(?:元|块)", question))
        sources = sum(word in question for word in ("商品页", "描述", "聊天", "回复"))
        return len(amounts), sources, len(question)

    main, other = sorted((first, second), key=detail_score, reverse=True)
    if _order_update_question(other) and not _order_update_question(main):
        main += "确认后方便把最终价格写进商品页和订单吗？"
    return main


def unique_questions(questions):
    result, positions = [], {}
    for raw in questions:
        question = natural_question(raw)
        if not question:
            continue
        key = re.sub(r"\W", "", question)
        if _final_price_question(question):
            key = "final_price"
        elif re.search(r"原盒|收纳包|配件|随货", question) and re.search(r"随货|清单|合照|包含|发出|都带|哪些", question):
            key = "delivery_contents"
        elif re.search(r"取消配对|初始配对|抹掉.*内容", question):
            key = "unpair_and_setup"
        if key not in positions:
            positions[key] = len(result)
            result.append(question)
        elif key == "final_price":
            index = positions[key]
            result[index] = _merge_price_questions(result[index], question)
    return result[:3]


def device_question(question, case):
    model = str(case.get("model", "")).lower().replace(" ", "")
    if "iphone14" in model and "循环" in question:
        return "方便发一下本机能显示的电池健康或最大容量页面，并说一下有没有换过电池吗？"
    if "mac" in model and re.search(r"m[1-9]", model) and "固件密码" in question:
        return "交付前方便退出账号、重置机器，并当面确认能正常设置和登录吗？"
    if "原彩" in question and re.search(r"证明|确认.{0,6}原装", question):
        return "屏幕换过或修过吗？方便提供维修记录或检测结果吗？"
    is_graphics_card = (case.get("category", "") in {"", "台式电脑/配件"}
                        and not re.search(r"整机|主机|台式机|台式电脑", model)
                        and bool(re.search(r"geforce|rtx|gtx|radeon|显卡", model)))
    if is_graphics_card and re.search(r"螺丝|防拆|背板", question) and re.search(r"拆|修|原装", question):
        return "显卡有拆修或更换零件吗？方便说明情况，并提供已有维修记录和螺丝、防拆贴照片供参考吗？"
    if is_graphics_card and re.search(r"点亮|运行|负载|稳定|性能", question) and re.search(r"视频|截图|证明|确认", question):
        return "方便发一段本机测试视频，能看到显卡型号、游戏或测试程序运行、温度和画面情况吗？"
    return question
