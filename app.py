import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agent_core import run_review, cart_gate
from domain_knowledge import PLATFORMS, CATEGORIES, MODEL_OPTIONS, PLATFORM_GUIDANCE, CATEGORY_CHECKLIST
from cart_scene import show_cart_scene
from image_dialogue import extract_chat_images
from product_preview import show_product_preview
from puzzle_feedback import show_puzzle_feedback

load_dotenv()

st.set_page_config(page_title="二手数码购物车实验室", page_icon="🛒", layout="wide")

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
  <div class="hero-title">🛒 把二手数码商品投进购物车</div>
  <div class="hero-sub">每完成一站，购物车就向前开一步。三站确认后，商品成形，再亲手投进购物车。</div>
</div>
""", unsafe_allow_html=True)

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
    typed = st.text_area(label, key=f"{prefix}_typed", height=height,
                         placeholder="可以直接粘贴对话文字，也可以上传聊天截图。")
    images = st.file_uploader("上传聊天截图（可选，最多3张）", type=["png", "jpg", "jpeg", "webp"],
                              accept_multiple_files=True, key=f"{prefix}_images",
                              help="按聊天顺序选择图片；上传前请遮盖个人信息。")
    if images:
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
        timeout=35,
        max_retries=0,
    )
    payload = {**case, "category_guidance": CATEGORY_CHECKLIST.get(case["category"], ""),
               "platform_guidance": PLATFORM_GUIDANCE.get(case["platform"], "")}
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


stage = st.session_state.setdefault("journey_stage", 1)
from_stage = st.session_state.get("journey_from", stage)
show_journey(stage, from_stage)
st.session_state["journey_from"] = stage

if stage == 1:
    with st.container(border=True, key="step_platform"):
        st.markdown("### 🎟️ 第一站 · 选交易场景")
        saved_platform = st.session_state.get("confirmed_platform", PLATFORMS[0])
        platform = st.selectbox("商品主要在哪个平台交易？", PLATFORMS,
                                index=PLATFORMS.index(saved_platform) if saved_platform in PLATFORMS else 0,
                                key="journey_platform_choice",
                                help="小红书可能只是展示渠道；这里选择最终沟通或成交的平台。")
        if st.button("确认平台，让购物车前进 →", type="primary", use_container_width=True):
            st.session_state["confirmed_platform"] = platform
            st.session_state["journey_stage"] = 2
            st.session_state["journey_from"] = 1
            st.rerun()
else:
    platform = st.session_state["confirmed_platform"]
    with st.container(border=True, key="step_platform"):
        st.markdown(f"### ✅ 第一站 · {platform}")
        if st.button("修改交易平台", key="edit_platform"):
            st.session_state.pop("review_result", None)
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
        options = MODEL_OPTIONS[category]
        model_choice = st.selectbox("选择具体型号", options,
                                    index=options.index(saved_choice) if saved_choice in options else None,
                                    placeholder="选择型号，或选手动填写", key=f"device_model_{category}")
        needs_manual = model_choice == "其他型号（手动填写）" or "需填写" in (model_choice or "")
        if needs_manual:
            model = st.text_input("填写准确型号", placeholder="写上品牌、型号及代际",
                                  value=st.session_state.get("confirmed_manual_model", ""),
                                  key=f"manual_model_{category}").strip()
        else:
            model = model_choice or ""
        model_details = st.text_input("版本 / 容量 / 配置（选填）", placeholder="例如：256GB、降噪版、16GB+512GB",
                                      value=st.session_state.get("confirmed_model_details", ""),
                                      key=f"model_details_{category}")
        if model and model_details.strip():
            model = f"{model}；{model_details.strip()}"
        st.caption("找不到型号？选择“其他型号（手动填写）”就能自己填。")
        if st.button("确认型号，让购物车前进 →", type="primary", use_container_width=True):
            if not model.strip():
                st.warning("先选一个型号，或手动填写准确型号。")
            else:
                st.session_state["confirmed_category"] = category
                st.session_state["confirmed_model"] = model
                st.session_state["confirmed_model_choice"] = model_choice
                st.session_state["confirmed_manual_model"] = model.split("；")[0] if needs_manual else ""
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
            st.session_state["journey_stage"] = 2
            st.rerun()
else:
    category, model = "", ""

if stage == 3:
    with st.container(border=True, key="step_evidence"):
        st.markdown("### 🧷 第三站 · 为商品贴上线索")
        evidence_left, evidence_right = st.columns([0.8, 1.2], gap="large")
        with evidence_left:
            price = st.text_input("价格标签", placeholder="例如：¥420", key="journey_price",
                                  value=st.session_state.get("confirmed_price", ""))
            chat = render_chat_input("initial_chat", "卖家沟通内容（选填）")
        with evidence_right:
            listing = st.text_area("商品标题与描述", height=245, key="journey_listing",
                                   value=st.session_state.get("confirmed_listing", ""),
                                   placeholder="粘贴商品介绍、成色、配件及售后说明；先遮盖姓名、电话、地址和订单号。")
        if st.button("确认线索，拼出商品 →", type="primary", use_container_width=True):
            if not price.strip() or not listing.strip():
                st.warning("请先填写价格和商品描述，再确认这一站。")
            else:
                st.session_state.update({"confirmed_price": price.strip(), "confirmed_listing": listing.strip(),
                                         "confirmed_chat": chat.strip(), "journey_stage": 4, "journey_from": 3})
                st.rerun()
elif stage == 4:
    price = st.session_state["confirmed_price"]
    listing = st.session_state["confirmed_listing"]
    chat = st.session_state["confirmed_chat"]
    with st.container(border=True, key="step_evidence"):
        st.markdown("### ✅ 第三站 · 商品线索已贴好")
        st.caption(f"标价 {price} · 商品描述已填写")
        if st.button("修改价格或描述", key="edit_evidence"):
            st.session_state.pop("review_result", None)
            st.session_state["journey_stage"] = 3
            st.rerun()
else:
    price, listing, chat = "", "", ""

show_product_preview(category, model, platform, price, listing)
st.progress((stage - 1) / 3, text=f"✨ 已确认 {stage - 1} / 3 站")
submitted = stage == 4 and st.button("🛒 商品已成形，进入投掷场景", type="primary", use_container_width=True)

if submitted:
    current = {"platform": platform, "category": category, "model": model.strip(), "price": price.strip(), "listing": listing.strip(), "chat": chat.strip()}
    with st.spinner("正在核对商品信息，绘制投掷场景……"):
        result = review_case(current)
    if result.get("error"):
        st.error(result["error"])
    else:
        st.session_state["review_case"] = current
        st.session_state["review_result"] = result
        st.session_state["seller_replies"] = []
        st.session_state["review_round"] = 1
        st.session_state["decision_change"] = ""

if "review_result" in st.session_state:
    saved_case = st.session_state["review_case"]
    saved_result = st.session_state["review_result"]
    decision, reason = cart_gate(saved_result)
    st.markdown(f"### 🧪 第 {st.session_state['review_round']} 轮核验")
    if st.session_state.get("decision_change"):
        st.info(st.session_state["decision_change"])
    show_cart_scene(saved_case["category"], saved_case["model"], saved_case["platform"], saved_case["price"], decision, reason)
    with st.expander("🔎 为什么这样判断？", expanded=False):
        st.caption("这里列出需要核实的地方及对应原文，方便你自己判断。")
        for index, issue in enumerate(saved_result.get("issues", [])[:10], 1):
            with st.container(border=True):
                priority = {"high": "优先核实", "medium": "需要核实", "low": "补充确认"}.get(issue["severity"], "待核实")
                st.markdown(f"**{index}. {priority}｜{issue['summary']}**")
                for item in issue.get("evidence", []):
                    st.write(f"来源 {item['source']}：『{item['quote']}』")
                status = {"unanswered": "还没得到答复", "answered_claim_only": "卖家已解释，仍需核对",
                          "contradicted": "回复前后不一致", "awaiting_independent_evidence": "还缺少可核对的凭证"}.get(issue['status'], "待核实")
                st.caption(status)
        if saved_result.get("claims"):
            with st.expander("查看从原文提取的陈述（尚未核实）"):
                for claim in saved_result["claims"]:
                    st.write(f"{claim['source']}：『{claim['quote']}』→ {claim['claim']}")
    show_puzzle_feedback(saved_result.get("analysis", ""), saved_result.get("evidence_notes", ""), saved_case)

    with st.container(border=True, key="seller_reply_stage"):
        st.markdown("### 💌 卖家回复了？把新线索放进来")
        st.caption("可粘贴卖家回复，或上传聊天截图识别；先遮盖姓名、头像、电话、地址、账号和完整序列号。识别结果可修改，然后再分析。")
        new_reply = render_chat_input(f"reply_round_{st.session_state['review_round']}", "卖家的新回复")
        if st.button("🔁 根据卖家回复重新分析", key="analyze_seller_reply", type="primary", use_container_width=True):
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
                if followup_result.get("error"):
                    st.error(followup_result["error"])
                else:
                    old_decision, _ = cart_gate(saved_result)
                    new_decision, _ = cart_gate(followup_result)
                    labels = {"allow": "可进入购物车", "reject": "暂不建议进入购物车", "wait": "等待补充信息"}
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

