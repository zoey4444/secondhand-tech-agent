import os
import uuid
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agent_core import run_review, cart_gate
from market_comparison import compare_prices
from domain_knowledge import PLATFORMS, CATEGORIES, MODEL_OPTIONS, checklist_for_case, transaction_guidance
from cart_scene import show_cart_scene
from image_dialogue import extract_chat_images
from product_preview import show_product_preview
from puzzle_feedback import show_puzzle_feedback
from review_policy import source_label
from review_record import APP_VERSION, make_run_record
from verification_progress import show_verification_progress
from seller_profile import render_seller_input, show_seller_feedback
from product_import import render_listing_import
from material_changes import compare_rounds, show_material_changes

load_dotenv()

st.set_page_config(page_title="证据拼图 · 二手数码购前核验", page_icon="🧩", layout="wide")

st.markdown("""
<style>
.stApp {background:linear-gradient(155deg,#caebed 0%,#B5dae9 53%,#cce7d9 100%);color:#174b60;}
[data-testid="stHeader"] {background:#caebeddd;}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,[data-testid="stWidgetLabel"] p {color:#174b60 !important;}
h1,h2,h3 {color:#174b60 !important;}
.hero {padding:27px 31px;border:2px solid #63bad9;border-radius:27px;background:linear-gradient(110deg,#caebed,#B5dae9 58%,#cce7d9);margin:8px 0 18px;box-shadow:0 13px 26px #63bad933;animation:rise .55s ease-out;}
.hero-kicker {color:#267895;letter-spacing:.12em;font-size:13px;font-weight:900;}
.hero-title {font-size:34px;font-weight:900;color:#174b60;margin:8px 0;}
.hero-sub {color:#2d6477;font-size:16px;}
.journey{position:relative;margin:16px 0 24px;padding:17px 15px 65px;background:#cce7d9;border:2px solid #63bad9;border-radius:24px;overflow:hidden;}
.journey-stops{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;position:relative;z-index:1;}
.journey-stop{text-align:center;padding:9px 5px;border:2px dashed #63bad9;border-radius:15px;background:#caebed;color:#286782;font-size:13px;font-weight:800;}
.journey-stop.done{border-style:solid;background:#B5dae9}.journey-stop.active{border-style:solid;background:#63bad9;color:#123d51;box-shadow:0 0 0 4px #caebed;}
.journey-rail{position:absolute;left:9%;right:9%;bottom:30px;height:8px;border-radius:99px;background:#B5dae9;border:1px solid #63bad9;}
.journey-cart{position:absolute;bottom:12px;left:var(--to);font-size:34px;line-height:1;transform:translateX(-50%);filter:drop-shadow(0 4px 3px #318aa766);}
.journey-cart.moving{animation:cart-roll .9s cubic-bezier(.22,.72,.2,1) both;}
@keyframes cart-roll{from{left:var(--from);transform:translateX(-50%) rotate(-9deg)}60%{transform:translateX(-50%) rotate(8deg)}to{left:var(--to);transform:translateX(-50%) rotate(0)}}
div.st-key-step_platform,div.st-key-step_device,div.st-key-step_evidence {background:#cce7d9;border:2px solid #63bad9 !important;border-radius:23px !important;padding:16px 20px;box-shadow:0 10px 20px #63bad92d;animation:rise .55s ease-out both;}
div.st-key-seller_reply_stage {background:linear-gradient(120deg,#cce7d9,#caebed,#B5dae9);border:2px solid #63bad9 !important;border-radius:23px !important;padding:18px 22px;box-shadow:0 10px 20px #63bad92d;margin-top:19px;animation:rise .5s ease-out both;}
div.st-key-step_device{background:#B5dae9;animation-delay:.1s;margin-top:15px}div.st-key-step_evidence{background:#caebed;animation-delay:.2s;margin-top:15px}
div.st-key-step_platform h3,div.st-key-step_device h3,div.st-key-step_evidence h3{margin-top:0;font-size:22px;}
div.stButton > button[kind="primary"] {background:#63bad9 !important;color:#123d51 !important;border:2px solid #318aa7 !important;border-radius:15px;font-weight:900;min-height:52px;box-shadow:0 6px 0 #318aa7;transition:transform .2s,box-shadow .2s;}
div.stButton > button[kind="primary"]:hover {background:#caebed !important;transform:translateY(-2px);box-shadow:0 8px 0 #318aa7;}
[data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input {background:#caebed !important;color:#174b60 !important;border:1px solid #63bad9 !important;border-radius:11px;}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {background:#caebed !important;color:#174b60 !important;border:1px solid #63bad9 !important;border-radius:11px;}
[data-testid="stSelectbox"] div[data-baseweb="select"] span {color:#174b60 !important;}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder {color:#47788a !important;opacity:1 !important;}
[data-baseweb="popover"] ul {background:#caebed !important;}
[data-testid="stCaptionContainer"] p {color:#315d6e !important;}
.small-note {font-size:13px;color:#315d6e;}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:650px){.journey{padding:12px 8px 57px}.journey-stops{gap:4px}.journey-stop{font-size:11px;padding:8px 3px}.journey-cart{font-size:29px}}
@media(prefers-reduced-motion:reduce){.hero,.journey-cart,div.st-key-step_platform,div.st-key-step_device,div.st-key-step_evidence{animation:none}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-kicker">SECOND-HAND TECH · TOSS TO CART</div>
  <div class="hero-title">🧩 证据拼图 · 二手数码购前核验</div>
  <div class="hero-sub">对照商品描述和聊天，找出待核实的地方，整理成给卖家的追问；收到答复后，继续更新判断。</div>
</div>
""", unsafe_allow_html=True)
st.caption(f"版本 {APP_VERSION} · 分析以你提供的材料为依据，不能鉴定真伪或保证交易安全。购物车展示当前核验状态。")
with st.expander("提交的文字和截图会怎样使用？"):
    st.write("点击分析时，商品文字和聊天记录会发送给配置的模型服务；截图在点击识别时发送。请先遮盖姓名、电话、地址、账号等个人信息。")
    st.write("应用将当前交易记录保存在本次会话中，不主动写入服务器文件。需要留存时，可自行下载本次核验记录；刷新页面或服务重启可能使会话丢失。")

def get_api_key() -> str:
    """Read a local environment variable or a Streamlit Cloud secret."""
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("DEEPSEEK_API_KEY", "")).strip()
    except (FileNotFoundError, KeyError):
        return ""


def render_chat_input(prefix: str, label: str, height: int = 145) -> str:
    """Allow typed dialogue or screenshot transcription, with an editable OCR draft."""
    def clear_old_transcript():
        st.session_state.pop(f"{prefix}_ocr_text", None)
    typed = st.text_area(label, key=f"{prefix}_typed", height=height,
                         placeholder="可以直接粘贴对话文字，也可以上传聊天截图。")
    images = st.file_uploader("上传聊天截图（可选，最多3张）", type=["png", "jpg", "jpeg", "webp"],
                              accept_multiple_files=True, key=f"{prefix}_images", on_change=clear_old_transcript,
                              help="按聊天顺序选择图片；上传前请遮盖个人信息。")
    if images:
        if not st.session_state.get(f"{prefix}_ocr_text"):
            st.info("这些截图尚未转成分析文字。请先点击下方“识别截图中的对话”；直接继续时，图片内容不会参与判断。")
        st.caption(f"已选择 {len(images)} 张截图。先点击识别，再核对下方文字；更换截图后请重新识别。")
        with st.expander("预览已选截图"):
            for image in images[:3]:
                st.image(image, width=300)
    if st.button("🔎 识别截图中的对话", key=f"{prefix}_recognize", disabled=not images):
        try:
            with st.spinner("正在读取截图中的聊天文字……"):
                transcript = extract_chat_images(
                    images, get_api_key(), os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                    model=os.getenv("DEEPSEEK_VISION_MODEL", "deepseek-flash"),
                )
            if transcript:
                st.session_state[f"{prefix}_ocr_text"] = transcript
                st.rerun()
            else:
                st.warning("没有识别出对话文字。请换清晰截图，或直接粘贴文字。")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"截图识别失败：{exc}。可以换清晰截图，或直接粘贴文字。")
    recognized = ""
    if f"{prefix}_ocr_text" in st.session_state:
        recognized = st.text_area("识别结果（请核对并修改错字）", key=f"{prefix}_ocr_text", height=150)
        st.caption("识别可能漏字或认错说话人。请检查后再提交；未核对的截图文字不能当成证据。")
    return "\n\n".join(part.strip() for part in (typed, recognized) if part.strip())


def review_case(case: dict) -> dict:
    key = get_api_key()
    if not key:
        return {"error": "还没有配置 DeepSeek API Key。本地请填写 .env；部署后请在 Streamlit Cloud 的 Secrets 中设置。"}
    llm = ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        api_key=key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=0.1,
        # Cloud cold starts and shared API capacity can exceed a short local timeout.
        timeout=90,
        max_retries=0,
    )
    payload = {**case, "category_guidance": checklist_for_case(case),
               "platform_guidance": transaction_guidance(case)}
    return run_review(payload, llm)


def show_journey(stage: int, from_stage: int) -> None:
    labels = ("🎟️ 选平台", "🎨 定型号", "🧷 贴线索", "🛒 投掷")
    stops = "".join(
        f'<div class="journey-stop {"done" if index < stage else "active" if index == stage else ""}">{label}</div>'
        for index, label in enumerate(labels, 1)
    )
    positions = (10, 35, 60, 85)
    moving = "moving" if from_stage != stage else ""
    st.markdown(
        f'<div class="journey"><div class="journey-stops">{stops}</div><div class="journey-rail"></div>'
        f'<div class="journey-cart {moving}" style="--from:{positions[from_stage - 1]}%;--to:{positions[stage - 1]}%">🛒</div></div>',
        unsafe_allow_html=True,
    )


def reset_product():
    for key in list(st.session_state):
        del st.session_state[key]


st.button("清空全部，换一件商品", on_click=reset_product,
          help="清除本次商品信息、截图、卖家回复和核验结果，回到第一步。需要留存时请先下载记录。")
stage = st.session_state.setdefault("journey_stage", 1)
from_stage = st.session_state.get("journey_from", stage)
show_journey(stage, from_stage)
st.session_state["journey_from"] = stage

if stage == 1:
    render_listing_import(get_api_key(), os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                          os.getenv("DEEPSEEK_VISION_MODEL", "deepseek-flash"))
    with st.container(border=True, key="step_platform"):
        st.markdown("### 🎟️ 第一站 · 选交易场景")
        saved_platform = st.session_state.get("confirmed_platform", PLATFORMS[0])
        platform = st.selectbox("在哪里看到这件商品？", PLATFORMS,
                                index=PLATFORMS.index(saved_platform) if saved_platform in PLATFORMS else 0,
                                key="journey_platform_choice",
                                help="这里记录商品展示渠道；下单付款的地方单独填写。")
        payment_options = ["尚未确定", "闲鱼", "转转", "淘宝", "京东", "小红书", "当面付款", "个人转账", "其他渠道"]
        saved_payment = st.session_state.get("confirmed_payment_channel", "尚未确定")
        payment_channel = st.selectbox("准备在哪里下单付款？", payment_options,
                                      index=payment_options.index(saved_payment) if saved_payment in payment_options else 0,
                                      key="journey_payment_channel")
        if st.button("确认平台，让购物车前进 →", type="primary", use_container_width=True):
            st.session_state["confirmed_platform"] = platform
            st.session_state["confirmed_payment_channel"] = payment_channel
            st.session_state["journey_stage"] = 2
            st.session_state["journey_from"] = 1
            st.rerun()
else:
    platform = st.session_state["confirmed_platform"]
    with st.container(border=True, key="step_platform"):
        st.markdown(f"### ✅ 第一站 · 展示：{platform}")
        st.caption(f"下单付款：{st.session_state.get('confirmed_payment_channel', '尚未确定')}")
        if st.button("修改交易平台", key="edit_platform"):
            st.session_state.pop("review_result", None)
            st.session_state.pop("scene_token", None)
            st.session_state["journey_stage"] = 1
            st.rerun()

if stage == 2:
    with st.container(border=True, key="step_device"):
        st.markdown("### 🎨 第二站 · 给商品定造型")
        saved_category = st.session_state.get("confirmed_category", CATEGORIES[0])
        category = st.selectbox("这是什么数码产品？", CATEGORIES,
                                index=CATEGORIES.index(saved_category) if saved_category in CATEGORIES else 0,
                                key="device_category")
        saved_choice = st.session_state.get("confirmed_model_choice", "")
        options = [*MODEL_OPTIONS[category]]
        model_choice = st.selectbox("① 从常见型号中选择", options,
                                    index=options.index(saved_choice) if saved_choice in options else None,
                                    placeholder="选择型号，或选手动填写", key=f"device_model_{category}")
        needs_manual = model_choice == "其他型号（手动填写）" or "需填写" in (model_choice or "")
        if needs_manual:
            unknown_series = model_choice == "其他型号（手动填写）"
            if unknown_series:
                st.caption("选择“其他型号”时，请填写品牌和完整型号。")
                model = st.text_input("填写品牌 / 型号", placeholder="例如：Apple、Sony 或其他品牌的完整型号",
                                      value=st.session_state.get("confirmed_manual_model", ""),
                                      key=f"manual_model_{category}").strip()
            else:
                st.caption("品牌 / 系列已由上方型号选择带入；这里只填写具体代际 / 版本，或选择“不清楚”。")
                base_model = model_choice.replace("（需填写代际）", "").replace("（需填写具体型号）", "")
                generation_detail = st.selectbox("具体代际 / 版本", ["不清楚"], index=None,
                                                 placeholder="填写具体代际 / 版本",
                                                 accept_new_options=True,
                                                 key=f"generation_status_{category}",
                                                 help="直接输入具体代际 / 版本，或打开下拉菜单选择“不清楚”。")
                generation_detail = (generation_detail or "").strip()
                model = base_model + (f"；具体代际 / 版本：{generation_detail}" if generation_detail else "")
                if generation_detail == "不清楚":
                    model += "；具体代际 / 版本不清楚"
        else:
            model = model_choice or ""
        model_details = st.text_input("版本 / 容量 / 配置（选填）", placeholder="例如：256GB、降噪版、16GB+512GB",
                                      value=st.session_state.get("confirmed_model_details", ""),
                                      key=f"model_details_{category}")
        if model and model_details.strip():
            model = f"{model}；{model_details.strip()}"
        st.caption("型号和配置用于核对商品描述、聊天及参考报价是否对应同一件商品；不清楚的内容无需猜测。")
        if st.button("确认型号，让购物车前进 →", type="primary", use_container_width=True):
            if not model.strip():
                st.warning("请填写或选择已知的品牌 / 系列；如果只是不清楚代际或版本，请在下方“具体代际 / 版本”中选择“不清楚”。")
            else:
                st.session_state["confirmed_category"] = category
                st.session_state["confirmed_model"] = model
                st.session_state["confirmed_model_choice"] = model_choice
                st.session_state["confirmed_manual_model"] = (generation_detail if needs_manual and not unknown_series else model if needs_manual else "")
                st.session_state["confirmed_model_details"] = model_details.strip()
                st.session_state["journey_stage"] = 3
                st.session_state["journey_from"] = 2
                st.rerun()
elif stage > 2:
    category = st.session_state["confirmed_category"]
    model = st.session_state["confirmed_model"]
    with st.container(border=True, key="step_device"):
        st.markdown(f"### ✅ 第二站 · {category} · {model}")
        if st.button("修改商品型号", key="edit_device"):
            st.session_state.pop("review_result", None)
            st.session_state.pop("scene_token", None)
            st.session_state["journey_stage"] = 2
            st.rerun()
else:
    category, model = "", ""

if stage == 3:
    with st.container(border=True, key="step_evidence"):
        st.markdown("### 🧷 第三站 · 为商品贴上线索")
        evidence_left, evidence_right = st.columns([0.8, 1.2], gap="large")
        with evidence_left:
            saved_price = str(st.session_state.get("confirmed_price", "")).strip()
            default_price_mode = "未标价" if saved_price == "未标价" else "已标价"
            price_mode = st.radio("价格情况", ["已标价", "未标价"], horizontal=True,
                                  index=0 if default_price_mode == "已标价" else 1,
                                  key="journey_price_mode")
            if "journey_price_number" not in st.session_state:
                try:
                    st.session_state["journey_price_number"] = float(saved_price) if saved_price else None
                except ValueError:
                    st.session_state["journey_price_number"] = None
            if price_mode == "已标价":
                price_number = st.number_input("商品标价（元）", min_value=0.01,
                                               step=10.0, format="%.2f", key="journey_price_number",
                                               placeholder="输入数字，例如 420")
                price = f"{price_number:g}" if price_number is not None else ""
                st.caption("会核对不同材料里的价格；填写同款二手报价后，还能看样本价格对比。")
            else:
                price = "未标价"
                st.info("智能体会把最终成交价列为待核实项。")
            sample_prices = st.text_input(
                "同款二手参考价（选填）", value=st.session_state.get("confirmed_price_samples", ""),
                placeholder="例如：450，480，500", key="journey_price_samples",
                help="填 3 至 5 个同型号、容量/版本和成色接近的二手挂牌价，用逗号分隔。")
            sample_source = st.text_input(
                "参考来源和查看日期（选填）", value=st.session_state.get("confirmed_price_source", ""),
                placeholder="例如：闲鱼同款搜索，2026-10-26", key="journey_price_source")
            sample_preview = compare_prices({"price": price, "price_samples": sample_prices,
                                             "price_source": sample_source})
            if sample_preview["status"] == "invalid":
                st.warning(sample_preview["summary"])
            elif sample_preview["status"] == "insufficient":
                st.caption(sample_preview["summary"])
            chat = render_chat_input("initial_chat", "卖家沟通内容（选填）")
        with evidence_right:
            listing = st.text_area("商品标题与描述", height=245, key="journey_listing",
                                   value=st.session_state.get("confirmed_listing", ""),
                                   placeholder="粘贴商品介绍、成色、配件及售后说明；先遮盖姓名、电话、地址和订单号。")
        seller_profile = render_seller_input(
            get_api_key(), os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            os.getenv("DEEPSEEK_VISION_MODEL", "deepseek-flash"))
        if st.button("确认线索，拼出商品 →", type="primary", use_container_width=True):
            if sample_preview["status"] == "invalid":
                st.warning("请先修正同款二手参考价：输入 3 至 5 个正数，用逗号分隔。")
            elif price_mode == "已标价" and not price.strip():
                st.warning("请输入数字标价或选择“未标价”。")
            else:
                st.session_state.update({"confirmed_price": price.strip(), "confirmed_listing": listing.strip(),
                                         "confirmed_chat": chat.strip(), "confirmed_price_samples": sample_prices.strip(),
                                         "confirmed_price_source": sample_source.strip(),
                                         "confirmed_seller_profile": seller_profile,
                                         "journey_stage": 4, "journey_from": 3})
                st.rerun()
elif stage == 4:
    price = st.session_state["confirmed_price"]
    listing = st.session_state["confirmed_listing"]
    chat = st.session_state["confirmed_chat"]
    with st.container(border=True, key="step_evidence"):
        st.markdown("### ✅ 第三站 · 商品线索已贴好")
        price_caption = "未标价，需核实最终成交价" if price == "未标价" else f"标价 ¥{price}"
        st.caption(f"{price_caption} · {'商品描述已填写' if listing else '暂无商品描述，将列为待补信息'}")
        if st.button("修改价格或描述", key="edit_evidence"):
            st.session_state.pop("review_result", None)
            st.session_state.pop("scene_token", None)
            st.session_state["journey_stage"] = 3
            st.rerun()
else:
    price, listing, chat = "", "", ""

show_product_preview(category, model, platform, price, listing)
st.progress((stage - 1) / 3, text=f"✨ 已确认 {stage - 1} / 3 站")
submitted = stage == 4 and st.button("🛒 商品已成形，进入投掷场景", type="primary", use_container_width=True)

if submitted:
    current = {"platform": platform, "payment_channel": st.session_state.get("confirmed_payment_channel", "尚未确定"),
               "category": category, "model": model.strip(), "price": price.strip(), "listing": listing.strip(), "chat": chat.strip(),
               "price_samples": st.session_state.get("confirmed_price_samples", ""),
               "price_source": st.session_state.get("confirmed_price_source", ""),
               "seller_profile": st.session_state.get("confirmed_seller_profile", "")}
    st.session_state.update(review_case=current, scene_token=uuid.uuid4().hex, analysis_attempted=False,
                            seller_replies=[], review_round=1, decision_change="", review_history=[])
    st.session_state.pop("review_result", None)
    st.session_state.pop("review_error", None)
    st.session_state.pop("round_previous_issues", None)
    st.rerun()

if stage == 4 and "scene_token" in st.session_state:
    saved_case = st.session_state["review_case"]
    saved_result = st.session_state.get("review_result")
    decision, reason = cart_gate(saved_result) if saved_result else ("pending", "")
    event = show_cart_scene(saved_case["category"], saved_case["model"], saved_case["platform"], saved_case["price"],
                            decision, reason, st.session_state["scene_token"])
    if (isinstance(event, dict) and event.get("action") == "toss" and event.get("token") == st.session_state["scene_token"]
            and not st.session_state.get("analysis_attempted")):
        st.session_state["analysis_attempted"] = True
        with st.spinner("正在核对材料，结果与拼图马上一起呈现……"):
            result = review_case(saved_case)
        st.session_state["review_history"].append(make_run_record(saved_case, result, os.getenv("DEEPSEEK_MODEL", "deepseek-flash")))
        if result.get("error"):
            st.session_state["review_error"] = result["error"]
        else:
            st.session_state["review_result"] = result
        st.rerun()
    if st.session_state.get("review_error"):
        st.error(st.session_state["review_error"])
        if st.button("重新准备商品，再投一次"):
            st.session_state.update(scene_token=uuid.uuid4().hex, analysis_attempted=False)
            st.session_state.pop("review_error", None)
            st.rerun()

if stage == 4 and "review_result" in st.session_state:
    saved_case = st.session_state["review_case"]
    saved_result = st.session_state["review_result"]
    decision, reason = cart_gate(saved_result)
    st.markdown(f"### 🧪 第 {st.session_state['review_round']} 轮核验")
    if st.session_state.get("decision_change"):
        st.info(st.session_state["decision_change"])
    if saved_result.get("material_changes"):
        show_material_changes(saved_result["material_changes"])
    elif saved_result.get("round_changes"):
        with st.expander("这次答复解决了什么，还缺什么？", expanded=True):
            for change in saved_result["round_changes"]:
                st.write(f"{change['change']}：{change['summary']}")
    if st.button("重新分析当前材料", key="reanalyze_current"):
        retry_case = {**saved_case, "seller_replies": st.session_state["seller_replies"]}
        # Re-analyse the same round and retain every already identified issue.
        prior_by_id = {issue["id"]: issue for issue in st.session_state.get("round_previous_issues", [])}
        prior_by_id.update({issue["id"]: issue for issue in saved_result.get("issues", [])})
        retry_case["previous_issues"] = list(prior_by_id.values())
        with st.spinner("正在重新核对当前材料……"):
            retried = review_case(retry_case)
        st.session_state.setdefault("review_history", []).append(make_run_record(
            retry_case, retried, os.getenv("DEEPSEEK_MODEL", "deepseek-flash"), st.session_state["review_round"]))
        if retried.get("error"):
            st.error(retried["error"])
        else:
            st.session_state["review_result"] = retried
            st.session_state["decision_change"] = "已重新分析当前材料；结果仍需结合原文和实物核对。"
            st.rerun()
    with st.expander("🔎 查看待核实问题", expanded=False):
        st.caption("这里只列出需要处理的问题；完整原文和处理状态可下载核验记录查看。")
        for index, issue in enumerate(saved_result.get("issues", [])[:10], 1):
            with st.container(border=True):
                priority = {"high": "优先核实", "medium": "需要核实", "low": "补充确认"}.get(issue["severity"], "待核实")
                st.markdown(f"**{index}. {priority}｜{issue['summary']}**")
                if issue.get("question"):
                    st.write(f"建议动作：{issue['question']}")
        if saved_result.get("claims"):
            with st.expander("查看从原文提取的陈述（尚未核实）"):
                for claim in saved_result["claims"]:
                    st.write(f"{source_label(claim['source'])}：『{claim['quote']}』→ {claim['claim']}")
    comparison = saved_result.get("price_comparison", {})
    with st.container(border=True):
        st.markdown("### 💰 同款二手价格对比")
        st.write(comparison.get("summary", "没有可用的同款二手参考价，暂时无法判断价格是否接近市价。"))
        if comparison.get("status") == "compared":
            st.caption("参考的是你提供的挂牌价样本，实际成交价和机况可能不同；价格差异本身不能证明商品有问题。")
    show_puzzle_feedback(saved_result.get("analysis", ""), saved_result.get("evidence_notes", ""), saved_case, saved_result)
    show_seller_feedback(saved_case)
    show_verification_progress({**saved_case, "seller_replies": st.session_state.get("seller_replies", [])}, saved_result)

    with st.container(border=True, key="seller_reply_stage"):
        st.markdown("### 💌 补充回复或核验材料，更新判断")
        st.caption("可粘贴卖家回复，或上传聊天截图识别；先遮盖姓名、头像、电话、地址、账号和完整序列号。识别结果可修改，然后再分析。")
        new_reply = render_chat_input(f"reply_round_{st.session_state['review_round']}", "新回复或补充材料（请注明来源）")
        if st.button("🔁 根据补充材料重新分析", key="analyze_seller_reply", type="primary", use_container_width=True):
            if not new_reply.strip():
                st.warning("先粘贴卖家的回复，或上传截图并点击‘识别截图中的对话’。")
            else:
                updated_replies = [*st.session_state["seller_replies"], new_reply.strip()]
                followup_case = {
                    **saved_case,
                    "seller_replies": updated_replies,
                    "previous_issues": saved_result.get("issues", []),
                }
                with st.spinner("正在对照上一轮疑点，检查新回复……"):
                    followup_result = review_case(followup_case)
                if not followup_result.get("error"):
                    followup_result["material_changes"] = compare_rounds(saved_result, followup_result, new_reply.strip())
                st.session_state.setdefault("review_history", []).append(make_run_record(
                    followup_case, followup_result, os.getenv("DEEPSEEK_MODEL", "deepseek-flash"), st.session_state["review_round"] + 1))
                if followup_result.get("error"):
                    st.error(followup_result["error"])
                else:
                    st.session_state["round_previous_issues"] = saved_result.get("issues", [])
                    old_decision, _ = cart_gate(saved_result)
                    new_decision, _ = cart_gate(followup_result)
                    labels = {"allow": "当前材料未见明显异常", "reject": "先解决交易冲突或付款问题", "wait": "仍需补充或核对信息"}
                    if new_decision == old_decision:
                        change = f"与上一轮相比，购物车判断仍是「{labels[new_decision]}」。请看‘回复后的变化’拼图，确认疑点是否真正解决。"
                    else:
                        change = f"购物车判断从「{labels[old_decision]}」变为「{labels[new_decision]}」。请核对下方依据；卖家陈述仍需凭证或实物支持。"
                    st.session_state["seller_replies"] = updated_replies
                    st.session_state["review_result"] = followup_result
                    st.session_state["review_round"] += 1
                    st.session_state["decision_change"] = change
                    st.rerun()
    if st.session_state["seller_replies"]:
        with st.expander(f"查看已提交的 {len(st.session_state['seller_replies'])} 次卖家回复"):
            for index, reply in enumerate(st.session_state["seller_replies"], 1):
                st.markdown(f"**第 {index} 次回复**")
                st.text(reply)

if stage == 4 and st.session_state.get("review_history"):
    records = st.session_state["review_history"]
    st.download_button("下载本次核验记录", json.dumps(records, ensure_ascii=False, indent=2),
                       file_name=f"review-{records[0]['run_id'][:8]}.json", mime="application/json", key="download_review")
    st.caption(f"版本 {APP_VERSION} · 已保留本次会话 {len(records)} 次分析记录，含输入、回答和处理状态，便于复核。")


