"""Compact puzzle-style review with copyable seller questions."""

import re
from html import escape

import streamlit.components.v1 as components
from review_policy import source_label, unique_questions
from input_feedback import build_input_feedback, feedback_text


def split_analysis(analysis: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^#{1,3}\s+(.+?)\s*$", analysis))
    names = ("回复后的变化", "已知信息", "缺失或矛盾", "建议向卖家核实", "验货清单", "初步风险提示", "判断边界")
    for index, match in enumerate(matches):
        heading = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(analysis)
        content = analysis[match.end():end].strip()
        for name in names:
            if name in heading:
                sections[name] = content
                break
    if not sections and analysis.strip():
        sections["已知信息"] = analysis.strip()
    return sections


def seller_message(section: str, case: dict | None = None) -> str:
    return "\n".join(unique_questions(section.splitlines()))


def first_complete_sentence(body: str) -> str:
    """Use a complete short sentence; never cut model text mid-thought."""
    body = "\n".join(line for line in body.splitlines() if not re.match(r"\s*(?:依据|状态|listing|chat)[：:]", line))
    cleaned = re.sub(r"[*#`]+", "", body)
    cleaned = re.sub(r"(?m)^\s*[-•]\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for match in re.finditer(r"[^。！？；]+[。！？；]", cleaned):
        sentence = match.group().strip(" -|：")
        if len(sentence) >= 8 and "|---" not in sentence and "unanswered" not in sentence:
            return sentence
    return ""


def checklist_summary(body: str) -> str:
    """Preview complete inspection actions instead of a generic category slogan."""
    cleaned = re.sub(r"[*#`]+", "", body)
    actions = [re.sub(r"^\s*(?:[-•]|\d+[.、)])\s*", "", item).strip()
               for item in re.split(r"[；;\n]+", cleaned)]
    actions = [item for item in actions if item]
    return "\n".join(f"• {item}" for item in actions[:3])


def card_summary(title: str, body: str, notes: str = "", case: dict | None = None) -> str:
    case = case or {}
    model = case.get("model", "").split("；")[0].strip()
    platform = case.get("platform", "").strip()
    price = case.get("price", "").strip()
    category = case.get("category", "数码商品").strip()
    if title == "回复后的变化":
        if "标价为" in notes and "价格" in body:
            return "卖家补充了解释；原有价格矛盾仍需用订单或付款记录核对。"
        if any(word in body for word in ("仍缺", "未回答", "未提供", "答非所问")):
            return "卖家已有回复，但部分关键问题或独立证据仍未补齐。"
        return "已收到卖家新回复；请对照上一轮疑点查看哪些得到回答。"
    if title == "已知信息":
        if platform and model and price:
            if price in {"未标价", "价格面议", "面议", "私聊报价", "待定", "暂无报价"}:
                return f"当前核验的是{platform}上的{model}；商品页未提供明确价格，最终成交价需要先确认。"
            return f"当前核验的是{platform}上的{model}，标价{price}；商品陈述尚未核实。"
        return "这里汇总已填写的商品信息；卖家描述仍属于待核实陈述。"
    if title == "缺失或矛盾":
        if price in {"未标价", "价格面议", "面议", "私聊报价", "待定", "暂无报价"}:
            return "商品页没有明确标价，先确认最终成交价，并核对平台订单金额。"
        has_price = "标价与商品描述中的价格不一致" in notes or "标价与商品描述中的价格不一致" in body
        has_model = "选择的耳机型号与描述中的系列不一致" in notes or "选择的耳机型号与描述中的系列不一致" in body
        if has_price and has_model:
            return "价格和型号都存在前后不一致，先核实最终成交价与准确型号。"
        if has_price:
            listing_price = re.search(r'(?:listing|商品描述)[：:]\s*[“"]([^”"]+)', body)
            if price and listing_price:
                shown_price = price if price.endswith(("元", "块")) else price + "元"
                return f"标价{shown_price}，描述写{listing_price.group(1)}；请先确认最终成交价。"
            return "标价与商品描述中的价格不一致，先核实最终成交价。"
        if has_model:
            return "选择的型号与商品描述不一致，先确认实际型号。"
        return first_complete_sentence(body) or "本轮还有信息缺口或待核查之处，请查看对应依据。"
    if title == "建议向卖家核实":
        return "把未解决的疑点整理成追问，可一键复制并发送给卖家。"
    if title == "验货清单":
        return checklist_summary(body) or f"按{category}的型号、主要功能、配件和凭证逐项验货。"
    if title == "初步风险提示":
        if "有若干事项需核实" in body:
            return "目前有若干事项需核实，先补证据再决定是否购买。"
        if "当前材料未见明显异常信号" in body:
            return "现有材料未见明显异常信号，付款前仍要核对实物和凭证。"
        return "现有材料不足以明确判断，请先补充关键事实。"
    if title == "判断边界":
        return "本助手只核验提交的材料，不能鉴定真伪或保证交易安全。"
    return first_complete_sentence(body) or "查看本项的完整依据与核验步骤。"


def clean_detail(body: str) -> str:
    lines = [line.replace("**", "").rstrip() for line in body.splitlines()]
    # Evidence and status remain in the downloadable/internal record. They are
    # deliberately hidden from the buyer-facing card because the same wording
    # is already represented by the concise issue and seller question.
    lines = [line for line in lines if not re.match(r"\s*(?:依据|状态)[：:]", line)]
    return "\n".join(line for line in lines if not re.fullmatch(r"\s*\|?[-:|\s]+\|?\s*", line))


def issue_overview(issues):
    groups = {"缺失": [], "矛盾": [], "其他待核实": []}
    seen = set()
    for item in issues:
        if item.get('kind') == 'injection':
            continue
        key = item.get('id') or item.get('summary', '')
        if key in seen:
            continue
        seen.add(key)
        kind, text = item.get('kind', ''), item.get('summary', '')
        if kind in {'price_conflict', 'price_revision', 'model_conflict'} or item.get('status') == 'contradicted':
            group = '矛盾'
        elif kind.startswith('missing') or re.search(r'缺少|缺失|未提供|未说明|不清楚|未知|未确定|未明确|没有.{0,12}(?:说明|凭证|记录|描述)', text):
            group = '缺失'
        elif re.search(r'不一致|相互矛盾|前后矛盾|条件冲突', text):
            group = '矛盾'
        else:
            group = '其他待核实'
        groups[group].append(item)
    priority = sum(i.get('severity') == 'high' for items in groups.values() for i in items)
    summary = '\n'.join(f'{name}：共{len(items)}点' for name, items in groups.items())
    summary += f'\n优先核实：共{priority}点'
    lines = ['按问题条目统计；优先核实是上述问题的优先级，与分类数量不相加。']
    for name, items in groups.items():
        lines.append(f'\n{name}：共{len(items)}点')
        for number, item in enumerate(items, 1):
            tag = '【优先核实】' if item.get('severity') == 'high' else ''
            lines.append(f"{number}. {tag}{item.get('summary', '')}")
            for evidence in item.get('evidence', []):
                lines.append(f"引用{source_label(evidence.get('source', ''))}：{evidence.get('quote', '')}")
            if item.get('question'):
                lines.append('建议动作：' + item['question'])
    return summary, '\n'.join(lines)


def build_puzzle_html(analysis: str, evidence_notes: str, case: dict | None = None, review: dict | None = None) -> str:
    sections = split_analysis(analysis)
    notes = evidence_notes.strip()
    if not review and notes and not notes.startswith("规则扫描未发现"):
        sections["缺失或矛盾"] = "已发现的线索：\n" + notes + "\n\n还需核实的地方：\n" + sections.get("缺失或矛盾", "")
    questions = seller_message(sections.get("建议向卖家核实", ""), case)
    tiles = [
        ("已知信息", "🔎", "01", "把商品说清楚"),
        ("缺失或矛盾", "🧩", "02", "先找证据缺口"),
        ("建议向卖家核实", "💬", "03", "一键复制给卖家"),
        ("验货清单", "🧰", "04", "收货时逐项检查"),
    ]
    if "回复后的变化" in sections:
        tiles.insert(0, ("回复后的变化", "🔁", "00", "对照上轮疑点看进展"))
    sections["填写信息的作用"] = feedback_text((review or {}).get("input_feedback") or build_input_feedback(case or {}, review or {}))
    tile_count = len(tiles)
    rendered = []
    for index, (title, icon, _number, subtitle) in enumerate(tiles, 1):
        body = sections.get(title, "这一项没有形成单独的分析内容，可结合其他拼图查看。")
        if title == "建议向卖家核实" and questions:
            body = questions
        summary = card_summary(title, body, notes, case)
        if title == '缺失或矛盾':
            if review is not None:
                summary, body = issue_overview(review.get('issues', []))
                if review.get('analysis_notice') or review.get('error'):
                    summary += '\n分析未完整完成，请展开核对。'
            else:
                summary = '问题数量待确认，展开查看原文。'
        question_button = '<button class="pz-copy" id="copySeller" type="button">📋 一键复制给卖家</button><span id="copyStatus" class="pz-copy-status" aria-live="polite"></span>' if title == "建议向卖家核实" and questions else ""
        rendered.append(
            f'<article class="pz-tile {"pz-question" if title == "建议向卖家核实" else ""}">'
            f'<div class="pz-num">拼图 {index:02d} / {tile_count:02d}</div>'
            f'<div class="pz-icon">{icon}</div>'
            f'<h3>{escape(title)}</h3><div class="pz-sub">{escape(subtitle)}</div>'
            f'<p class="pz-summary">{escape(summary)}</p>'
            '<div class="pz-actions">'
            f'{question_button}'
            f'<button class="pz-expand" type="button" aria-expanded="false" data-closed-label="{"查看要发送的话 ↓" if title == "建议向卖家核实" else "查看补充说明 ↓"}">{"查看要发送的话 ↓" if title == "建议向卖家核实" else "查看补充说明 ↓"}</button>'
            '</div>'
            f'<div class="pz-details" hidden>{escape(clean_detail(body))}</div>'
            '</article>'
        )
    html = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}html{scroll-padding-top:88px}body{margin:0;background:#caebed;color:#174b60;font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif}[hidden]{display:none!important}
.pz-shell{padding:24px;border:2px solid #63bad9;border-radius:26px;background:linear-gradient(150deg,#caebed,#cce7d9 48%,#B5dae9);min-height:0}
.pz-head{display:flex;align-items:end;justify-content:space-between;gap:15px;margin-bottom:21px}.pz-kicker{font-weight:900;font-size:12px;letter-spacing:2px;color:#277b99}.pz-head h2{font-size:26px;margin:4px 0 0;color:#174b60}.pz-head p{font-size:13px;margin:0;color:#315d6c}
.pz-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.pz-tile{--tile:#caebed;position:relative;min-height:190px;border-radius:22px;padding:17px 19px 15px;background:var(--tile);border:2px solid #63bad9;color:#174b60;box-shadow:0 8px 0 #63bad93b,0 15px 23px #63bad926;animation:pz-enter .48s both;transition:transform .2s,box-shadow .2s;display:flex;flex-direction:column}
.pz-tile:hover{transform:translateY(-3px);box-shadow:0 11px 0 #63bad940,0 20px 26px #63bad92b}
.pz-tile.pz-selected{outline:3px solid #258db1;outline-offset:2px}
.pz-tile:nth-child(2),.pz-tile:nth-child(6){--tile:#B5dae9}.pz-tile:nth-child(3),.pz-tile:nth-child(4){--tile:#cce7d9}.pz-tile:nth-child(5){--tile:#63bad9}
.pz-tile:nth-child(2){animation-delay:.07s}.pz-tile:nth-child(3){animation-delay:.14s}.pz-tile:nth-child(4){animation-delay:.21s}.pz-tile:nth-child(5){animation-delay:.28s}.pz-tile:nth-child(6){animation-delay:.35s}
.pz-tile:after{content:"";position:absolute;top:48%;right:-17px;width:28px;height:28px;border-radius:50%;background:var(--tile);border:2px solid #63bad9;z-index:3}.pz-tile:nth-child(3n):after{top:auto;right:42%;bottom:-17px}.pz-tile:last-child:after{display:none}
.pz-question{border-width:3px;box-shadow:0 9px 0 #63bad961,0 15px 26px #63bad938}
.pz-num{display:inline-block;align-self:flex-start;border-radius:999px;background:#caebed;border:1px solid #63bad9;padding:4px 9px;font-size:11px;font-weight:900;letter-spacing:1px}.pz-icon{font-size:28px;margin-top:8px}.pz-tile h3{margin:2px 0 0;font-size:20px}.pz-sub{font-size:12px;font-weight:750;color:#286782;margin-top:3px}.pz-summary{white-space:pre-line;font-size:14px;font-weight:650;line-height:1.55;margin:12px 0 14px;word-break:break-word}.pz-actions{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:auto}
.pz-expand,.pz-copy,.pz-close{cursor:pointer;border-radius:10px;font-size:12px;font-weight:900;padding:8px 10px}.pz-expand,.pz-close{border:1px solid #63bad9;background:#caebed;color:#1b6178}.pz-copy{border:0;background:#63bad9;color:#123e50}.pz-expand:hover,.pz-copy:hover,.pz-close:hover{filter:brightness(1.08)}.pz-copy-status{font-size:12px;font-weight:800;color:#1b6379}
.pz-panel{margin-top:24px;padding:22px;border:2px solid #63bad9;border-radius:23px;background:#caebed;box-shadow:0 10px 20px #63bad928}.pz-panel-head{display:flex;align-items:start;justify-content:space-between;gap:15px}.pz-panel-kicker{font-size:12px;font-weight:900;color:#287897;letter-spacing:1px}.pz-panel h3{font-size:22px;margin:4px 0 8px}.pz-panel-summary{font-size:15px;font-weight:750;line-height:1.6;margin:0 0 16px;padding:11px 14px;background:#cce7d9;border-left:4px solid #63bad9;border-radius:10px}.pz-panel-label{font-size:13px;font-weight:900;color:#286782;margin:14px 0 7px}.pz-panel-body{white-space:pre-wrap;font-size:14px;line-height:1.7;word-break:break-word}
.pz-panel{scroll-margin-top:88px}.pz-notice{font-size:13px;line-height:1.6;padding:12px 15px;margin:0 0 18px;border-left:4px solid #b27a15;border-radius:10px;background:#fff3d6;color:#5c461d}.pz-foot{font-size:12px;margin-top:20px;color:#315d6c}.pz-tips{font-size:12px;line-height:1.5;margin-top:12px;color:#315d6c}.pz-tips details{margin:5px 0}.pz-tips summary{cursor:pointer}.pz-tip-body{white-space:pre-wrap;padding:8px 0;max-height:240px;overflow:auto}.pz-hidden{position:absolute;left:-99999px;top:-99999px}
@keyframes pz-enter{from{opacity:0;transform:translateY(13px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
@media(max-width:960px){.pz-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pz-tile:nth-child(3n):after{top:48%;right:-17px;bottom:auto}.pz-tile:nth-child(2n):after{top:auto;right:42%;bottom:-17px}}
@media(max-width:600px){.pz-grid{grid-template-columns:1fr}.pz-tile{min-height:205px}.pz-tile:after,.pz-tile:nth-child(2n):after{top:auto;right:42%;bottom:-17px}.pz-head{display:block}.pz-head p{margin-top:8px}}
@media(prefers-reduced-motion:reduce){.pz-tile{animation:none;transition:none}}
</style></head><body><div class="pz-shell"><div class="pz-head"><div><div class="pz-kicker">REVIEW PUZZLE · 查看结论与核验依据</div><h2>🧩 商品核验拼图</h2></div><p>优先核实属于问题子集，不与分类数量相加。</p></div>
__ANALYSIS_NOTICE__<div class="pz-grid">__TILES__</div>
<section class="pz-panel" id="detailPanel" hidden tabindex="-1"><div class="pz-panel-head"><div><div class="pz-panel-kicker">当前选中的拼图</div><h3 id="panelTitle"></h3></div><button class="pz-close" id="closePanel" type="button">收起 ↑</button></div><p class="pz-panel-summary" id="panelSummary"></p><div class="pz-panel-label" id="panelLabel">补充说明</div><div class="pz-panel-body" id="panelBody"></div></section>
__TIPS__
<textarea id="sellerMessage" class="pz-hidden" aria-hidden="true">__COPY_TEXT__</textarea></div>
<script>
const panel=document.getElementById('detailPanel');let selected=null;
document.querySelectorAll('.pz-expand').forEach(function(button){button.addEventListener('click',function(){const tile=button.closest('.pz-tile');if(selected===tile&&!panel.hidden){panel.hidden=true;tile.classList.remove('pz-selected');button.textContent=button.dataset.closedLabel;button.setAttribute('aria-expanded','false');selected=null;return}document.querySelectorAll('.pz-tile').forEach(function(item){item.classList.remove('pz-selected');const b=item.querySelector('.pz-expand');b.textContent=b.dataset.closedLabel;b.setAttribute('aria-expanded','false')});selected=tile;tile.classList.add('pz-selected');button.textContent='收起详细内容 ↑';button.setAttribute('aria-expanded','true');const title=tile.querySelector('h3').textContent;document.getElementById('panelTitle').textContent=title;document.getElementById('panelSummary').textContent=tile.querySelector('.pz-summary').textContent;document.getElementById('panelLabel').textContent=title==='建议向卖家核实'?'可以直接复制发送':'补充说明';document.getElementById('panelBody').textContent=tile.querySelector('.pz-details').textContent;panel.hidden=false;document.getElementById('panelTitle').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center',inline:'nearest'});panel.focus({preventScroll:true})})});
document.getElementById('closePanel').addEventListener('click',function(){panel.hidden=true;if(selected){selected.classList.remove('pz-selected');const b=selected.querySelector('.pz-expand');b.textContent=b.dataset.closedLabel;b.setAttribute('aria-expanded','false');selected=null}});
const copy=document.getElementById('copySeller');if(copy){copy.addEventListener('click',async function(){const input=document.getElementById('sellerMessage');const status=document.getElementById('copyStatus');let copied=false;try{if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(input.value);copied=true}}catch(e){}if(!copied){input.style.left='0';input.style.top='0';input.style.display='block';input.focus();input.select();try{copied=document.execCommand('copy')}catch(e){}input.style.display='none';input.style.left='-99999px';input.style.top='-99999px'}status.textContent=copied?'已复制，可粘贴给卖家 ✓':'复制未成功，请展开后手动复制'})}
</script></body></html>"""
    notice = str((review or {}).get("analysis_notice", "")).strip()
    notice_html = f'<aside class="pz-notice" role="note"><strong>本次分析提示：</strong>{escape(notice)}</aside>' if notice else ""
    html = html.replace("__COPY_TEXT__", escape(questions)).replace("__TILES__", "".join(rendered)).replace("__ANALYSIS_NOTICE__", notice_html)
    boundary = sections.get('判断边界') or '仅核对提交材料，不鉴定真伪或保证交易安全；卖家陈述仍需凭证或实物核验。'
    tips = ('<aside class="pz-tips" aria-label="使用提示">'
            '<details><summary>💡 判断边界：材料分析不等于实物鉴定</summary>'
            f'<div class="pz-tip-body">{escape(clean_detail(boundary))}</div></details>'
            '<details><summary>💡 填写信息的作用：查看各项输入如何参与判断</summary>'
            f'<div class="pz-tip-body">{escape(sections["填写信息的作用"])}</div></details></aside>')
    return html.replace('__TIPS__', tips)


def show_puzzle_feedback(analysis: str, evidence_notes: str, case: dict | None = None, review: dict | None = None) -> None:
    components.html(build_puzzle_html(analysis, evidence_notes, case, review), height=680, scrolling=True)
