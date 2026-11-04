"""Compact evidence journal with copyable seller questions."""

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


def checklist_points(body: str) -> list[str]:
    """Normalize model-written checklist prose into readable, dash-free points."""
    cleaned = clean_detail(body)
    points = []
    for line in cleaned.splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.、)])\s*", "", line).strip()
        if not line:
            continue
        points.extend(part.strip() for part in re.split(r"(?<=[。！？])\s*", line) if part.strip())
    return points


def checklist_summary(body: str) -> str:
    points = checklist_points(body)
    return f"收货时逐项核对型号配置、外观功能、配件和售后；共 {len(points)} 项，展开查看完整清单。" if points else ""


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
        if "未见明显阻断项" in body:
            return "现有材料未见明显阻断项；这不代表建议购买，仍需自行核验实物、凭证和交易条款。"
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


def group_issues(issues):
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
    return groups


def issue_group_detail(name, items):
    if not items:
        return f"本轮没有识别到{name}事项。"
    lines = []
    for number, item in enumerate(items, 1):
        tag = '【优先核实】' if item.get('severity') == 'high' else ''
        lines.append(f"{number}. {tag}{item.get('summary', '')}")
        for evidence in item.get('evidence', []):
            quote = str(evidence.get('quote', '')).strip()
            if quote:
                lines.append(f"材料来源：{source_label(evidence.get('source', ''))}")
                lines.append(f"原文：{quote}")
        if item.get('question'):
            lines.append('建议核实：' + str(item['question']))
    return '\n'.join(lines)


def issue_overview(issues):
    groups = group_issues(issues)
    priority = sum(i.get('severity') == 'high' for items in groups.values() for i in items)
    summary = '\n'.join(f'{name}：共{len(items)}点' for name, items in groups.items())
    summary += f'\n优先核实：共{priority}点'
    lines = ['按问题条目统计；优先核实是上述问题的优先级，与分类数量不相加。']
    for name, items in groups.items():
        lines.append(f'\n{name}：共{len(items)}点')
        lines.append(issue_group_detail(name, items))
    return summary, '\n'.join(lines)


def build_puzzle_html(analysis: str, evidence_notes: str, case: dict | None = None, review: dict | None = None) -> str:
    sections = split_analysis(analysis)
    notes = evidence_notes.strip()
    if not review and notes and not notes.startswith("规则扫描未发现"):
        sections["缺失或矛盾"] = "已发现的线索：\n" + notes + "\n\n还需核实的地方：\n" + sections.get("缺失或矛盾", "")
    questions = seller_message(sections.get("建议向卖家核实", ""), case)
    tiles = [
        ("已知信息", "当前材料能确认的内容"),
        ("缺失或矛盾", "需要补充或核实的证据"),
        ("建议向卖家核实", "把具体问题发给卖家"),
        ("验货清单", "收货时逐项检查"),
    ]
    if "回复后的变化" in sections:
        tiles.insert(0, ("回复后的变化", "对照上轮疑点看进展"))
    sections["填写信息的作用"] = feedback_text((review or {}).get("input_feedback") or build_input_feedback(case or {}, review or {}))
    rendered = []
    for title, subtitle in tiles:
        body = sections.get(title, "这一项没有形成单独的分析内容，可结合手账中的其他记录查看。")
        if title == "建议向卖家核实" and questions:
            body = questions
        summary = card_summary(title, body, notes, case)
        issue_groups = None
        if title == '缺失或矛盾':
            if review is not None:
                summary, body = issue_overview(review.get('issues', []))
                issue_groups = group_issues(review.get('issues', []))
                if review.get('analysis_notice') or review.get('error'):
                    summary += '\n分析未完整完成，请展开核对。'
            else:
                summary = '问题数量待确认，展开查看原文。'
        modifier = {
            '已知信息': 'pz-known', '缺失或矛盾': 'pz-issues',
            '建议向卖家核实': 'pz-questions', '验货清单': 'pz-checklist',
            '回复后的变化': 'pz-update',
        }.get(title, '')
        issue_counts = ''
        issue_details_html = ''
        if issue_groups is not None:
            issue_counts = '<div class="pz-counts">'
            detail_parts = []
            for name, items in issue_groups.items():
                issue_counts += (f'<button class="pz-count" type="button" data-category="{escape(name, quote=True)}" '
                                 f'aria-label="查看{name}：{len(items)}点" aria-expanded="false" aria-controls="detailPanel">'
                                 f'<b>{len(items)}</b><small>{escape(name)}</small></button>')
                detail_parts.append(
                    f'<div class="pz-issue-detail" data-category="{escape(name, quote=True)}" hidden>'
                    f'{escape(issue_group_detail(name, items))}</div>')
            issue_counts += '</div>'
            priority = sum(item.get('severity') == 'high' for items in issue_groups.values() for item in items)
            issue_counts += f'<div class="pz-priority">优先核实 <strong>{priority}</strong> 点 · 点击分类查看对应内容</div>'
            issue_details_html = ''.join(detail_parts)
        summary_html = issue_counts or f'<p class="pz-summary">{escape(summary)}</p>'
        question_button = '<button class="pz-copy" id="copySeller" type="button">复制追问</button><span id="copyStatus" class="pz-copy-status" aria-live="polite"></span>' if title == "建议向卖家核实" and questions else ""
        expand_button = '' if issue_groups is not None else f'<button class="pz-expand" type="button" aria-expanded="false" data-closed-label="{"查看要发送的话 ↓" if title == "建议向卖家核实" else "查看补充说明 ↓"}">{"查看要发送的话 ↓" if title == "建议向卖家核实" else "查看补充说明 ↓"}</button>'
        action_html = f'<div class="pz-actions">{question_button}{expand_button}</div>' if question_button or expand_button else ''
        detail_text = '\n'.join(f'• {point}' for point in checklist_points(body)) if title == '验货清单' else clean_detail(body)
        rendered.append(
            f'<article class="pz-tile {modifier}">'
            f'<h3>{escape(title)}</h3><div class="pz-sub">{escape(subtitle)}</div>'
            f'{summary_html}'
            f'{action_html}'
            f'<div class="pz-details" hidden>{escape(detail_text)}</div>{issue_details_html}'
            '</article>'
        )
    html = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}html{scroll-padding-top:72px}body{margin:0;background:#caebed;color:#174b60;font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif}[hidden]{display:none!important}
.pz-shell{padding:20px 22px;border:1px solid #63bad9;border-radius:20px;background:#caebed;min-height:0}
.pz-head{display:flex;align-items:end;justify-content:space-between;gap:15px;margin-bottom:16px}.pz-head h2{font-size:24px;margin:0;color:#174b60}.pz-head p{font-size:13px;margin:0;color:#315d6c}
.pz-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(250px,.8fr) minmax(0,1.25fr);gap:12px;align-items:stretch}
.pz-tile{min-width:0;min-height:196px;border-radius:16px;padding:18px 20px;background:#caebed;border:1px solid #8bc9d8;color:#174b60;display:flex;flex-direction:column}
.pz-known{background:#caebed}.pz-issues{background:#B5dae9}.pz-questions{background:#cce7d9}.pz-checklist{grid-column:1/-1;min-height:120px;background:#cce7d9;display:grid;grid-template-columns:minmax(190px,.55fr) minmax(0,1.45fr);column-gap:24px;align-items:start}.pz-checklist h3{grid-column:1;grid-row:1}.pz-checklist .pz-sub{grid-column:1;grid-row:2}.pz-checklist .pz-summary{grid-column:2;grid-row:1/3;align-self:center;margin:0}.pz-checklist .pz-actions{grid-column:1/-1;grid-row:3;margin-top:12px}.pz-update{grid-column:1/-1;min-height:0;flex-direction:row;align-items:center;gap:14px;padding:12px 18px}.pz-update .pz-sub{display:none}.pz-update .pz-summary{flex:1;margin:0}.pz-update .pz-actions{margin:0}
.pz-tile h3{margin:0;font-size:19px;line-height:1.35}.pz-sub{font-size:13px;font-weight:700;color:#286782;margin-top:4px}.pz-summary{white-space:pre-line;font-size:14px;font-weight:600;line-height:1.65;margin:14px 0 16px;word-break:break-word}.pz-checklist .pz-summary{margin:4px 0 12px}.pz-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:auto}
.pz-counts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:16px 0 8px}.pz-count{display:flex;align-items:baseline;gap:7px;width:100%;padding:7px 9px;border:1px solid transparent;border-radius:9px;background:#caebed;color:#174b60;font:inherit;text-align:left;cursor:pointer}.pz-count:hover,.pz-count-active{border-color:#318aa7;background:#cce7d9}.pz-count:focus-visible{outline:3px solid #174b60;outline-offset:2px}.pz-count b{font-size:20px;line-height:1}.pz-count small{font-size:12px;color:#315d6c}.pz-priority{font-size:12px;color:#315d6c;margin:2px 0 14px}
.pz-tile.pz-selected{outline:2px solid #258db1;outline-offset:2px}
.pz-expand,.pz-copy,.pz-close{cursor:pointer;border-radius:9px;font-size:13px;font-weight:800;padding:8px 11px}.pz-expand,.pz-close{border:1px solid #63bad9;background:#caebed;color:#1b6178}.pz-copy{border:0;background:#63bad9;color:#123e50}.pz-expand:hover,.pz-copy:hover,.pz-close:hover{filter:brightness(1.04)}.pz-expand:focus-visible,.pz-copy:focus-visible,.pz-close:focus-visible{outline:3px solid #174b60;outline-offset:2px}.pz-copy-status{font-size:12px;font-weight:800;color:#1b6379}
.pz-panel{margin-top:18px;padding:20px;border:1px solid #8bc9d8;border-radius:16px;background:#caebed}.pz-panel-head{display:flex;align-items:start;justify-content:space-between;gap:15px}.pz-panel-kicker{font-size:12px;font-weight:800;color:#287897}.pz-panel h3{font-size:21px;margin:4px 0 8px}.pz-panel-summary{font-size:15px;font-weight:700;line-height:1.6;margin:0 0 16px;padding:11px 14px;background:#cce7d9;border-radius:10px}.pz-panel-label{font-size:13px;font-weight:900;color:#286782;margin:14px 0 7px}.pz-panel-body{white-space:pre-wrap;font-size:14px;line-height:1.7;word-break:break-word}
.pz-panel{scroll-margin-top:72px}.pz-notice{font-size:13px;line-height:1.6;padding:12px 15px;margin:0 0 14px;border:1px solid #63bad9;border-radius:10px;background:#B5dae9;color:#174b60}.pz-foot{font-size:12px;margin-top:16px;color:#315d6c}.pz-tips{font-size:12px;line-height:1.6;margin-top:12px;color:#315d6c}.pz-tips details{margin:5px 0}.pz-tips summary{cursor:pointer}.pz-tip-body{white-space:pre-wrap;padding:8px 0;max-height:240px;overflow:auto}.pz-hidden{position:absolute;left:-99999px;top:-99999px}
@media(max-width:1050px){.pz-grid{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.pz-questions{grid-column:1/-1}.pz-checklist{grid-template-columns:minmax(150px,.45fr) minmax(0,1.55fr)}}
@media(max-width:650px){.pz-shell{padding:16px 14px}.pz-grid{grid-template-columns:1fr}.pz-tile,.pz-checklist,.pz-questions,.pz-update{grid-column:1;min-height:0}.pz-checklist{display:flex}.pz-update{flex-direction:column;align-items:stretch;gap:4px}.pz-update .pz-summary{margin:7px 0}.pz-update .pz-actions{margin-top:7px}.pz-head{display:block}.pz-head p{margin-top:7px}.pz-counts{grid-template-columns:repeat(2,minmax(0,1fr))}}
/* Parchment evidence board with distinct card colours, preserving text contrast. */
body{background:#f5ce87;color:#491c17}.pz-shell{background:#ffe0a1;border:4px solid #643820;border-radius:6px;box-shadow:inset 0 0 0 4px #e3d2ab}.pz-head h2{color:#491c17}.pz-head p,.pz-foot,.pz-tips{color:#643820}
.pz-tile{border:3px solid #643820;border-radius:4px;color:#491c17;box-shadow:4px 4px 0 #ba7a50;background:#ffe0a1}.pz-known{background:#f5ce87}.pz-issues{background:#f9c49d}.pz-questions{background:#f5ce87}.pz-checklist{background:#e8e5cd}.pz-update{background:#e7eddc}
.pz-sub,.pz-panel-kicker,.pz-panel-label{color:#5c7550}.pz-count{border-radius:3px;background:#ffe0a1;color:#491c17}.pz-count:hover,.pz-count-active{border-color:#7c955f;background:#eaf0d5}.pz-count small,.pz-priority{color:#643820}.pz-tile.pz-selected{outline-color:#638551}
.pz-expand,.pz-close{border:2px solid #643820;border-radius:3px;background:#f8eed4;color:#491c17}.pz-copy{border:2px solid #4c725c;border-radius:3px;background:#4b7fcb;color:#491c17}.pz-panel{border:3px solid #643820;border-radius:4px;background:#ffe0a1}.pz-panel-summary{border-radius:3px;background:#e6ebd3}.pz-notice{border:2px solid #643820;border-radius:3px;background:#f2e9cb;color:#491c17}
/* A bound field journal: numbered paper tabs replace the puzzle metaphor. */
.pz-shell{position:relative;padding-left:42px;background:#f8e8b9}
.pz-shell:before{content:"";position:absolute;left:15px;top:76px;bottom:20px;width:11px;background:radial-gradient(circle at center,#643820 0 4px,transparent 5px) center top/11px 48px repeat-y;pointer-events:none}
.pz-head{padding-bottom:13px;border-bottom:3px dashed #ba7a50;margin-bottom:25px}
.pz-grid{gap:23px 14px}
.pz-tile{position:relative;border-left:7px solid #4c725c;padding-top:28px;box-shadow:5px 5px 0 #ba7a50}
.pz-tile:before{position:absolute;left:12px;top:-13px;min-width:92px;padding:3px 9px;border:2px solid #643820;border-radius:2px;background:#4c725c;color:#ffe0a1;box-shadow:2px 2px 0 #ba7a50;font-size:12px;font-weight:900;letter-spacing:.08em;line-height:1.2}
.pz-known:before{content:"01 · 商品档案"}.pz-issues:before{content:"02 · 待核线索";background:#970138}.pz-questions:before{content:"03 · 卖家追问";background:#3a47a0}.pz-checklist:before{content:"04 · 验货清单"}.pz-update:before{content:"新回复 · 变化记录";background:#970138}
.pz-checklist{padding-top:28px}.pz-update{padding-top:24px}
.pz-panel{border-left:7px solid #4c725c}.pz-panel-kicker{letter-spacing:.08em}
@media(max-width:650px){.pz-shell{padding-left:33px}.pz-shell:before{left:10px}.pz-head{margin-bottom:25px}.pz-grid{gap:23px}}
</style></head><body><div class="pz-shell"><div class="pz-head"><h2>叽有数的线索手账</h2><p>优先核实属于问题子集，不与分类数量相加。</p></div>
__ANALYSIS_NOTICE__<div class="pz-grid">__TILES__</div>
<section class="pz-panel" id="detailPanel" hidden tabindex="-1"><div class="pz-panel-head"><div><div class="pz-panel-kicker">当前翻开的记录</div><h3 id="panelTitle"></h3></div><button class="pz-close" id="closePanel" type="button">收起 ↑</button></div><p class="pz-panel-summary" id="panelSummary"></p><div class="pz-panel-label" id="panelLabel">补充说明</div><div class="pz-panel-body" id="panelBody"></div></section>
__TIPS__
<textarea id="sellerMessage" class="pz-hidden" aria-hidden="true">__COPY_TEXT__</textarea></div>
<script>
const panel=document.getElementById('detailPanel');let selected=null;let selectedControl=null;
function clearSelection(){if(selected){selected.classList.remove('pz-selected');selected.querySelectorAll('.pz-count').forEach(function(item){item.classList.remove('pz-count-active');item.setAttribute('aria-expanded','false')});const expand=selected.querySelector('.pz-expand');if(expand){expand.textContent=expand.dataset.closedLabel;expand.setAttribute('aria-expanded','false')}}selected=null;selectedControl=null}
function openPanel(tile,control,title,summary,label,body){document.querySelectorAll('.pz-tile').forEach(function(item){item.classList.remove('pz-selected');item.querySelectorAll('.pz-count').forEach(function(count){count.classList.remove('pz-count-active');count.setAttribute('aria-expanded','false')});const expand=item.querySelector('.pz-expand');if(expand){expand.textContent=expand.dataset.closedLabel;expand.setAttribute('aria-expanded','false')}});selected=tile;selectedControl=control;tile.classList.add('pz-selected');if(control.classList.contains('pz-expand')){control.textContent='收起详细内容 ↑';control.setAttribute('aria-expanded','true')}else{control.classList.add('pz-count-active');control.setAttribute('aria-expanded','true')}document.getElementById('panelTitle').textContent=title;document.getElementById('panelSummary').textContent=summary;document.getElementById('panelLabel').textContent=label;document.getElementById('panelBody').textContent=body;panel.hidden=false;document.getElementById('panelTitle').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center',inline:'nearest'});panel.focus({preventScroll:true})}
document.querySelectorAll('.pz-expand').forEach(function(button){button.addEventListener('click',function(){const tile=button.closest('.pz-tile');if(selected===tile&&selectedControl===button&&!panel.hidden){panel.hidden=true;clearSelection();return}const title=tile.querySelector('h3').textContent;const summary=tile.querySelector('.pz-summary');const detail=tile.querySelector('.pz-details');openPanel(tile,button,title,summary?summary.textContent:tile.dataset.summary||'',title==='建议向卖家核实'?'可以直接复制发送':'补充说明',detail?detail.textContent:'当前没有可展开的补充内容。')})});
document.querySelectorAll('.pz-count').forEach(function(button){button.addEventListener('click',function(){const tile=button.closest('.pz-tile');const category=button.dataset.category;const detail=Array.from(tile.querySelectorAll('.pz-issue-detail')).find(function(item){return item.dataset.category===category});if(!detail)return;if(selectedControl===button&&!panel.hidden){panel.hidden=true;clearSelection();return}const count=button.querySelector('b').textContent;openPanel(tile,button,category+' · '+count+'点',category+'类问题共'+count+'点。展开内容列出具体问题、材料原文与建议核实动作。','对应问题与材料依据',detail.textContent.trim()||'本轮没有可展示的材料依据。')})});
document.getElementById('closePanel').addEventListener('click',function(){panel.hidden=true;clearSelection()});
const copy=document.getElementById('copySeller');if(copy){copy.addEventListener('click',async function(){const input=document.getElementById('sellerMessage');const status=document.getElementById('copyStatus');let copied=false;try{if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(input.value);copied=true}}catch(e){}if(!copied){input.style.left='0';input.style.top='0';input.style.display='block';input.focus();input.select();try{copied=document.execCommand('copy')}catch(e){}input.style.display='none';input.style.left='-99999px';input.style.top='-99999px'}status.textContent=copied?'已复制，可粘贴给卖家 ✓':'复制未成功，请展开后手动复制'})}
</script></body></html>"""
    notice = str((review or {}).get("analysis_notice", "")).strip()
    notice_html = f'<aside class="pz-notice" role="note"><strong>本次分析提示：</strong>{escape(notice)}</aside>' if notice else ""
    html = html.replace("__COPY_TEXT__", escape(questions)).replace("__TILES__", "".join(rendered)).replace("__ANALYSIS_NOTICE__", notice_html)
    boundary = sections.get('判断边界') or '仅核对提交材料，不鉴定真伪或保证交易安全；卖家陈述仍需凭证或实物核验。'
    tips = ('<aside class="pz-tips" aria-label="使用提示">'
            '<details><summary>判断边界：材料分析不等于实物鉴定</summary>'
            f'<div class="pz-tip-body">{escape(clean_detail(boundary))}</div></details>'
            '<details><summary>填写信息的作用：查看各项输入如何参与判断</summary>'
            f'<div class="pz-tip-body">{escape(sections["填写信息的作用"])}</div></details></aside>')
    return html.replace('__TIPS__', tips)


def show_puzzle_feedback(analysis: str, evidence_notes: str, case: dict | None = None, review: dict | None = None) -> None:
    components.html(build_puzzle_html(analysis, evidence_notes, case, review), height=680, scrolling=True)
