"""Compact puzzle-style review with copyable seller questions."""

import re
from html import escape

import streamlit.components.v1 as components


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


def seller_message(section: str) -> str:
    lines = []
    for raw in section.splitlines():
        line = re.sub(r"^\s*(?:[-*•]\s*|\d+[.)、]\s*)", "", raw).replace("**", "").strip()
        if line:
            lines.append(line)
    if not lines:
        return ""
    return "您好，我想确认这件商品的几个问题：\n" + "\n".join(f"{index}. {line}" for index, line in enumerate(lines, 1)) + "\n谢谢！"


def show_puzzle_feedback(analysis: str, evidence_notes: str) -> None:
    sections = split_analysis(analysis)
    notes = evidence_notes.strip()
    if notes and not notes.startswith("规则扫描未发现"):
        sections["缺失或矛盾"] = "程序检查：\n" + notes + "\n\n模型分析：\n" + sections.get("缺失或矛盾", "")
    questions = seller_message(sections.get("建议向卖家核实", ""))
    tiles = [
        ("已知信息", "🔎", "01", "把商品说清楚"),
        ("缺失或矛盾", "🧩", "02", "先找证据缺口"),
        ("建议向卖家核实", "💬", "03", "一键复制给卖家"),
        ("验货清单", "🧰", "04", "收货时逐项检查"),
        ("初步风险提示", "🚦", "05", "看清这次判断"),
        ("判断边界", "🛡️", "06", "保留最后一道关"),
    ]
    if "回复后的变化" in sections:
        tiles.insert(0, ("回复后的变化", "🔁", "00", "对照上轮疑点看进展"))
    tile_count = len(tiles)
    rendered = []
    for index, (title, icon, _number, subtitle) in enumerate(tiles, 1):
        body = sections.get(title, "这一项没有形成单独的分析内容，可结合其他拼图查看。")
        plain = re.sub(r"\s+", " ", body.replace("**", "")).strip()
        preview = plain[:95] + ("…" if len(plain) > 95 else "")
        question_button = '<button class="pz-copy" id="copySeller" type="button">📋 一键复制给卖家</button><span id="copyStatus" class="pz-copy-status" aria-live="polite"></span>' if title == "建议向卖家核实" and questions else ""
        rendered.append(
            f'<article class="pz-tile {"pz-question" if title == "建议向卖家核实" else ""}">'
            f'<div class="pz-num">拼图 {index:02d} / {tile_count:02d}</div>'
            f'<div class="pz-icon">{icon}</div>'
            f'<h3>{escape(title)}</h3><div class="pz-sub">{escape(subtitle)}</div>'
            f'<p class="pz-preview">{escape(preview)}</p>'
            f'{question_button}'
            '<button class="pz-expand" type="button" aria-expanded="false">展开详细内容 ↓</button>'
            f'<div class="pz-details" hidden>{escape(body.replace("**", ""))}</div>'
            '</article>'
        )
    html = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#caebed;color:#174b60;font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif}
.pz-shell{padding:24px;border:2px solid #63bad9;border-radius:26px;background:linear-gradient(150deg,#caebed,#cce7d9 48%,#B5dae9);min-height:680px}
.pz-head{display:flex;align-items:end;justify-content:space-between;gap:15px;margin-bottom:21px}.pz-kicker{font-weight:900;font-size:12px;letter-spacing:2px;color:#277b99}.pz-head h2{font-size:26px;margin:4px 0 0;color:#174b60}.pz-head p{font-size:13px;margin:0;color:#315d6c}
.pz-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.pz-tile{--tile:#caebed;position:relative;min-height:240px;border-radius:22px;padding:17px 19px 15px;background:var(--tile);border:2px solid #63bad9;color:#174b60;box-shadow:0 8px 0 #63bad93b,0 15px 23px #63bad926;animation:pz-enter .48s both;transition:transform .2s,box-shadow .2s}
.pz-tile:hover{transform:translateY(-3px);box-shadow:0 11px 0 #63bad940,0 20px 26px #63bad92b}
.pz-tile:nth-child(2),.pz-tile:nth-child(6){--tile:#B5dae9}.pz-tile:nth-child(3),.pz-tile:nth-child(4){--tile:#cce7d9}.pz-tile:nth-child(5){--tile:#63bad9}
.pz-tile:nth-child(2){animation-delay:.07s}.pz-tile:nth-child(3){animation-delay:.14s}.pz-tile:nth-child(4){animation-delay:.21s}.pz-tile:nth-child(5){animation-delay:.28s}.pz-tile:nth-child(6){animation-delay:.35s}
.pz-tile:after{content:"";position:absolute;top:48%;right:-17px;width:28px;height:28px;border-radius:50%;background:var(--tile);border:2px solid #63bad9;z-index:3}.pz-tile:nth-child(3n):after{top:auto;right:42%;bottom:-17px}.pz-tile:nth-child(6):after{display:none}
.pz-question{border-width:3px;box-shadow:0 9px 0 #63bad961,0 15px 26px #63bad938}
.pz-num{display:inline-block;border-radius:999px;background:#caebed;border:1px solid #63bad9;padding:4px 9px;font-size:11px;font-weight:900;letter-spacing:1px}.pz-icon{font-size:28px;margin-top:8px}.pz-tile h3{margin:2px 0 0;font-size:20px}.pz-sub{font-size:12px;font-weight:750;color:#286782;margin-top:3px}.pz-preview{font-size:13px;line-height:1.55;min-height:59px;max-height:62px;overflow:hidden;margin:12px 0 6px;word-break:break-word}
.pz-expand,.pz-copy{cursor:pointer;border-radius:10px;font-size:12px;font-weight:900;padding:8px 10px}.pz-expand{border:1px solid #63bad9;background:#caebed;color:#1b6178}.pz-copy{border:0;background:#63bad9;color:#123e50;margin-right:6px}.pz-expand:hover,.pz-copy:hover{filter:brightness(1.08)}.pz-copy-status{font-size:12px;font-weight:800;color:#1b6379}.pz-details{white-space:pre-wrap;font-size:13px;line-height:1.65;margin-top:10px;padding:10px;border-radius:12px;background:#caebed;max-height:205px;overflow:auto;word-break:break-word}
.pz-foot{font-size:12px;margin-top:20px;color:#315d6c}.pz-hidden{position:absolute;left:-99999px;top:-99999px}
@keyframes pz-enter{from{opacity:0;transform:translateY(13px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
@media(max-width:960px){.pz-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pz-tile:nth-child(3n):after{top:48%;right:-17px;bottom:auto}.pz-tile:nth-child(2n):after{top:auto;right:42%;bottom:-17px}}
@media(max-width:600px){.pz-grid{grid-template-columns:1fr}.pz-tile{min-height:205px}.pz-tile:after,.pz-tile:nth-child(2n):after{top:auto;right:42%;bottom:-17px}.pz-head{display:block}.pz-head p{margin-top:8px}}
@media(prefers-reduced-motion:reduce){.pz-tile{animation:none;transition:none}}
</style></head><body><div class="pz-shell"><div class="pz-head"><div><div class="pz-kicker">REVIEW PUZZLE · 让信息拼起来</div><h2>🧩 商品核验拼图</h2></div><p>先看每块重点，点开可读完整内容。</p></div>
<div class="pz-grid">__TILES__</div><div class="pz-foot">这些拼图来自用户提供的信息和模型分析；购买前请核验实物与凭证。</div>
<textarea id="sellerMessage" class="pz-hidden" aria-hidden="true">__COPY_TEXT__</textarea></div>
<script>
document.querySelectorAll('.pz-expand').forEach(function(button){button.addEventListener('click',function(){const detail=button.nextElementSibling;const open=detail.hasAttribute('hidden');if(open){detail.removeAttribute('hidden')}else{detail.setAttribute('hidden','')}button.textContent=open?'收起详细内容 ↑':'展开详细内容 ↓';button.setAttribute('aria-expanded',String(open))})});
const copy=document.getElementById('copySeller');if(copy){copy.addEventListener('click',async function(){const input=document.getElementById('sellerMessage');const status=document.getElementById('copyStatus');let copied=false;try{if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(input.value);copied=true}}catch(e){}if(!copied){input.style.left='0';input.style.top='0';input.style.display='block';input.focus();input.select();try{copied=document.execCommand('copy')}catch(e){}input.style.display='none';input.style.left='-99999px';input.style.top='-99999px'}status.textContent=copied?'已复制，可粘贴给卖家 ✓':'复制未成功，请展开后手动复制'})}
</script></body></html>"""
    html = html.replace("__COPY_TEXT__", escape(questions)).replace("__TILES__", "".join(rendered))
    components.html(html, height=760, scrolling=True)
