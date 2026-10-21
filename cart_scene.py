"""Interactive product toss scene. Only escaped display text enters the HTML."""

from html import escape
import json
from pathlib import Path

import streamlit.components.v1 as components


def product_icon(category: str) -> str:
    common = 'fill="none" stroke="#1b6077" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'
    if category == "手机":
        parts = '<rect x="54" y="12" width="72" height="136" rx="15"/><path d="M81 25h18M82 136h16"/>'
    elif category == "平板":
        parts = '<rect x="22" y="28" width="136" height="104" rx="12"/><circle cx="147" cy="80" r="3"/>'
    elif category == "笔记本电脑":
        parts = '<rect x="28" y="25" width="124" height="88" rx="7"/><path d="M14 127h152l-15 12H29z"/>'
    elif category == "台式电脑/配件":
        parts = '<rect x="24" y="30" width="132" height="83" rx="7"/><path d="M90 114v22M65 138h50"/>'
    elif category == "相机（单反/微单/CCD）":
        parts = '<path d="M24 55h28l8-14h51l8 14h37v75H24z"/><circle cx="90" cy="91" r="27"/><circle cx="139" cy="69" r="4"/>'
    elif category == "耳机":
        parts = '<path d="M35 90V74a55 55 0 0 1 110 0v16"/><rect x="29" y="83" width="23" height="43" rx="9"/><rect x="128" y="83" width="23" height="43" rx="9"/><path d="M145 125c0 14-13 23-39 23"/>'
    elif category == "智能手表/手环":
        parts = '<path d="M69 23l5-13h32l5 13M69 137l5 13h32l5-13"/><rect x="50" y="26" width="80" height="108" rx="24"/><circle cx="90" cy="80" r="22"/>'
    elif category == "游戏机":
        parts = '<path d="M49 59h82c12 0 20 8 23 21l8 39c2 12-7 20-17 15l-25-15H60l-25 15c-10 5-19-3-17-15l8-39c3-13 11-21 23-21z"/><path d="M57 78v26M44 91h26"/><circle cx="119" cy="84" r="4"/><circle cx="134" cy="99" r="4"/>'
    else:
        parts = '<path d="M24 50l66-30 66 30v83l-66 29-66-29z"/><path d="M24 50l66 30 66-30M90 80v82"/>'
    return f'<svg viewBox="0 0 180 170" role="img" aria-label="{escape(category, quote=True)}示意图"><g {common}>{parts}</g></svg>'


def build_cart_html(category: str, model: str, platform: str, price: str, decision: str, reason: str, token: str = "") -> str:
    if decision not in {"allow", "reject", "wait", "pending"}:
        decision = "wait"
    values = {
        "__ICON__": product_icon(category),
        "__CATEGORY__": escape(category[:30]),
        "__MODEL__": escape((model or "型号待确认")[:60]),
        "__PLATFORM__": escape(platform[:30]),
        "__PRICE__": escape((price or "价格待确认")[:30]),
        "__DECISION__": decision,
        "__TOKEN_JSON__": json.dumps(token).replace("<", "\\u003c"),
        "__REASON_JSON__": json.dumps(reason[:180], ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"),
    }
    html = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;background:#11182b;color:#f6f8ff}
.shell{min-height:625px;border-radius:25px;overflow:hidden;border:1px solid #526487;background:radial-gradient(circle at 23% 7%,#395888 0%,transparent 35%),radial-gradient(circle at 75% 20%,#394a80 0%,transparent 37%),linear-gradient(#18253f,#101a31 65%,#162b39);position:relative;padding:24px}
.top{display:flex;justify-content:space-between;gap:12px;align-items:center;position:relative;z-index:3}.eyebrow{color:#99ead8;font-size:13px;font-weight:800;letter-spacing:2px}.title{font-weight:900;font-size:25px;margin:5px 0 0}.badge{background:#26385c;border:1px solid #557196;padding:9px 14px;border-radius:999px;color:#b9dbf8;font-size:13px}
.scene{position:relative;height:385px;margin:12px 0 0;border-radius:20px;background:linear-gradient(180deg,rgba(117,173,220,.1),rgba(44,77,110,.11) 62%,rgba(58,80,72,.52) 63%);overflow:hidden}
.scene:before{content:"";position:absolute;left:0;right:0;top:63%;height:3px;background:#7898a3;opacity:.55}.cloud{position:absolute;width:90px;height:28px;border-radius:50px;background:#d1e6fd;opacity:.14;filter:blur(1px);animation:cloud 9s ease-in-out infinite alternate}.cloud.a{top:55px;left:20%}.cloud.b{top:90px;left:68%;animation-delay:-4s}.spark{position:absolute;top:8%;right:36%;font-size:30px;animation:twinkle 2s infinite alternate;color:#f7da8d}
.product{position:absolute;left:12%;top:92px;width:205px;height:216px;z-index:5;border-radius:24px;background:linear-gradient(145deg,#5d74d3,#6d50b2);border:2px solid #bbc7ff;box-shadow:0 20px 0 rgba(0,0,0,.13),0 25px 55px #090f26;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:11px 12px;cursor:grab;touch-action:none;user-select:none;transition:transform .65s cubic-bezier(.2,.8,.2,1),opacity .65s;}
.product:active{cursor:grabbing}.product.dragging{transition:none}.product svg{width:125px;height:118px;filter:drop-shadow(0 8px 9px rgba(17,23,62,.2))}.product .device{max-width:100%;font-weight:800;font-size:14px;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:-5px}.product .meta{font-size:12px;color:#e1e8ff;text-align:center;margin-top:4px}.product .ticket{position:absolute;right:-20px;top:14px;transform:rotate(13deg);background:#ffdc89;color:#402f46;border-radius:9px;padding:5px 8px;font-size:13px;font-weight:900;box-shadow:0 7px 12px #1118}
.cartzone{position:absolute;right:6%;top:86px;width:282px;height:232px;z-index:4}.cartzone svg{width:100%;height:100%;filter:drop-shadow(0 15px 10px #090d1e)}.cartzone.shake{animation:shake .45s ease-in-out}.cartlabel{position:absolute;right:7%;top:328px;color:#d5e9fc;font-size:13px;letter-spacing:1px}
.floor{position:absolute;left:10%;bottom:24px;color:#d7e6f5;font-size:13px;opacity:.85}.trail{position:absolute;left:49%;top:50%;font-size:28px;color:#93e7d6;animation:twinkle 1.5s infinite alternate;pointer-events:none}
.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:11px}.throw{border:0;border-radius:12px;padding:12px 22px;background:linear-gradient(90deg,#54e2c6,#bbefac);color:#17354a;font-size:15px;font-weight:900;cursor:pointer;box-shadow:0 8px 18px #071322}.throw:hover{filter:brightness(1.12)}.throw:disabled{opacity:.5;cursor:default}.again{border:1px solid #829abc;border-radius:12px;padding:11px 15px;background:#21314e;color:#e0e9f7;font-size:14px;cursor:pointer}.tip{color:#bbcae3;font-size:13px}
.feedback{margin-top:12px;min-height:69px;border:1px solid #435674;border-radius:13px;padding:12px 16px;background:#172741;color:#deecfc;line-height:1.65;font-size:14px}.feedback.allow{border-color:#4cceab;background:#163c3e}.feedback.reject{border-color:#ee857e;background:#462839}.feedback.wait{border-color:#efca82;background:#483e34}.feedback strong{font-size:17px}.confetti{position:absolute;right:25%;top:98px;opacity:0;pointer-events:none;font-size:25px;z-index:8}.confetti.on{animation:pop 1s ease-out forwards}
@keyframes cloud{to{transform:translateX(55px)}}@keyframes twinkle{to{opacity:.25;transform:scale(.85)}}@keyframes shake{20%{transform:translateX(-8px)}40%{transform:translateX(9px)}60%{transform:translateX(-6px)}80%{transform:translateX(4px)}}@keyframes pop{20%{opacity:1;transform:translateY(-32px) rotate(20deg)}80%{opacity:1}100%{opacity:0;transform:translateY(75px) rotate(70deg)}}
@media(max-width:720px){.shell{padding:16px;min-height:580px}.title{font-size:20px}.badge{display:none}.scene{height:365px}.product{left:5%;top:109px;width:145px;height:178px;padding:9px}.product svg{width:94px;height:94px}.product .device{font-size:12px}.cartzone{right:1%;top:105px;width:185px;height:170px}.cartlabel{top:292px;right:2%;font-size:11px}.floor{left:6%;font-size:11px}.trail{display:none}.product .ticket{right:-8px;font-size:11px}}
@media(prefers-reduced-motion:reduce){.cloud,.spark,.trail,.confetti{animation:none}.product{transition-duration:.01s}}
body{background:#caebed;color:#174b60}
.shell{border-color:#63bad9;background:radial-gradient(circle at 24% 7%,#caebed 0%,transparent 36%),linear-gradient(135deg,#B5dae9,#cce7d9 55%,#caebed);color:#174b60}
.eyebrow{color:#267895}.title{color:#174b60}.badge{background:#cce7d9;border-color:#63bad9;color:#174b60}
.scene{background:linear-gradient(180deg,#caebed,#B5dae9 63%,#cce7d9 63%)}.scene:before{background:#63bad9}.cloud{background:#caebed;opacity:.72}.spark,.trail{color:#318aaa}
.product{background:linear-gradient(145deg,#63bad9,#B5dae9);border-color:#caebed;color:#174b60;box-shadow:0 16px 0 #63bad955,0 24px 43px #63bad94d}.product .meta{color:#215c71}.product .ticket{background:#cce7d9;color:#174b60}
.cartzone svg path[stroke]{stroke:#1b6077}.cartzone svg circle{fill:#63bad9}.cartlabel,.floor{color:#174b60}
.throw{background:linear-gradient(90deg,#63bad9,#B5dae9);color:#143f53;box-shadow:0 7px 14px #63bad955}.again{background:#cce7d9;border-color:#63bad9;color:#174b60}.tip{color:#315e70}
.feedback{background:#caebed;border-color:#63bad9;color:#174b60}.feedback.allow{background:#cce7d9;border-color:#63bad9}.feedback.reject{background:#B5dae9;border-color:#63bad9}.feedback.wait{background:#caebed;border-color:#63bad9}
</style></head>
<body data-decision="__DECISION__"><div class="shell"><div class="top"><div><div class="eyebrow">TOSS TO CART · 二手数码实验室</div><div class="title">把这件商品投进购物车</div></div><div class="badge">拖动商品，或点击“投掷”</div></div>
<div class="scene" id="scene"><div class="cloud a"></div><div class="cloud b"></div><div class="spark">✦</div>
<div class="product" id="product" tabindex="0" role="button" aria-label="拖动商品到购物车"><span class="ticket">__PRICE__</span>__ICON__<div class="device">__MODEL__</div><div class="meta">__CATEGORY__ · __PLATFORM__</div></div>
<div class="trail">➜</div><div class="cartzone" id="cartZone"><svg viewBox="0 0 300 230" aria-label="购物车图案" role="img"><defs><linearGradient id="cartGrad" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#63bad9"/><stop offset="1" stop-color="#B5dae9"/></linearGradient></defs><path d="M28 45h33l27 112h153l29-82H78" stroke="#1b6077" stroke-width="10" stroke-linejoin="round" fill="none" stroke-linecap="round"/><path d="M84 78h185l-28 79H102z" fill="url(#cartGrad)" opacity=".84"/><path d="M95 168h146" stroke="#1b6077" stroke-width="10" stroke-linecap="round"/><circle cx="117" cy="195" r="15" fill="#63bad9"/><circle cx="220" cy="195" r="15" fill="#63bad9"/></svg></div>
<div class="cartlabel">核验候选购物车</div><div class="floor">↗ 将商品拖到购物车上方松开</div><div class="confetti" id="confetti">✦ ✧ ✦ ✧</div></div>
<div class="controls"><button class="throw" id="throw" type="button">🎯 一键投掷</button><button class="again" id="again" type="button">再试一次</button><span class="tip">投掷动画只展示分析结论；交易前仍需实物核验。</span></div>
<div class="feedback" id="feedback" role="status" aria-live="polite">商品已生成。拖动它碰到购物车，或者点击“一键投掷”，查看分析结论。</div>
</div>
<script>
(function(){
 const product=document.getElementById('product'); const cart=document.getElementById('cartZone');
 const feedback=document.getElementById('feedback'); const throwButton=document.getElementById('throw');
 const again=document.getElementById('again'); const confetti=document.getElementById('confetti');
 const decision=document.body.dataset.decision; const reason=__REASON_JSON__;
 let dragging=false, attempted=false, startX=0, startY=0, dragX=0, dragY=0;
 function setFeedback(title,detail,kind){feedback.className='feedback '+kind;feedback.textContent='';const strong=document.createElement('strong');strong.textContent=title;feedback.appendChild(strong);feedback.appendChild(document.createElement('br'));feedback.appendChild(document.createTextNode(detail));}
 function toss(){
  if(attempted)return; attempted=true; dragging=false; throwButton.disabled=true; product.classList.remove('dragging');
  if(decision==='pending'){
   again.disabled=true;
   product.style.transform='translate(90px,-50px) rotate(-15deg)';
   setFeedback('正在核对提交的材料……','分析完成后，这里会显示投掷结果，下方会一起出现核验拼图。','wait');
   setTimeout(function(){window.parent.postMessage({type:'cart:toss',token:__TOKEN_JSON__},'*');},380);
   return;
  }
  const p=product.getBoundingClientRect(), c=cart.getBoundingClientRect();
  const dx=c.left+c.width*.48-(p.left+p.width*.5)+dragX;
  const dy=c.top+c.height*.48-(p.top+p.height*.5)+dragY;
  product.style.transition='transform .38s ease-out, opacity .5s';
  product.style.transform='translate('+(dragX+dx*.5)+'px,'+(dragY+dy*.5-105)+'px) rotate(-15deg) scale(.92)';
  setTimeout(function(){
   product.style.transition='transform .54s ease-in, opacity .5s';
   if(decision==='allow'){
    product.style.transform='translate('+dx+'px,'+dy+'px) rotate(15deg) scale(.42)';
    setTimeout(function(){product.style.opacity='0';confetti.classList.add('on');setFeedback('✅ 进入候选购物车：仍需验货',reason,'allow');},550);
   } else {
    product.style.transform='translate('+dx+'px,'+(dy-25)+'px) rotate(-18deg) scale(.84)';
    setTimeout(function(){cart.classList.add('shake');product.style.transform='translate(0,0) rotate(-8deg)';setTimeout(function(){product.style.transform='';},420);if(decision==='reject'){setFeedback('⛔ 被购物车弹回：暂不建议购买',reason,'reject');}else{setFeedback('🟡 停在购物车外：先补充证据',reason,'wait');}},550);
   }
  },380);
 }
 function reset(){attempted=false;dragging=false;dragX=0;dragY=0;throwButton.disabled=false;cart.classList.remove('shake');confetti.classList.remove('on');product.style.transition='';product.style.opacity='1';product.style.transform='';feedback.className='feedback';feedback.textContent='商品已准备好，再投一次看看分析结论。';}
 product.addEventListener('pointerdown',function(e){if(attempted)return;dragging=true;startX=e.clientX;startY=e.clientY;dragX=0;dragY=0;product.classList.add('dragging');product.setPointerCapture(e.pointerId);});
 product.addEventListener('pointermove',function(e){if(!dragging)return;dragX=e.clientX-startX;dragY=e.clientY-startY;product.style.transform='translate('+dragX+'px,'+dragY+'px) rotate(-5deg)';});
 product.addEventListener('pointerup',function(){if(!dragging)return;dragging=false;const p=product.getBoundingClientRect(),c=cart.getBoundingClientRect();const overlap=p.right>c.left&&p.left<c.right&&p.bottom>c.top&&p.top<c.bottom;if(overlap){toss();}else{product.classList.remove('dragging');product.style.transform='';dragX=0;dragY=0;setFeedback('再靠近一点','把商品拖到购物车上方再松开，或点击“一键投掷”。','wait');}});
 product.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();toss();}});
 throwButton.addEventListener('click',toss);again.addEventListener('click',reset);
 if(decision!=='pending'){toss();}
})();
</script></body></html>"""
    for marker, value in values.items():
        html = html.replace(marker, value)
    return html


def show_cart_scene(category: str, model: str, platform: str, price: str, decision: str, reason: str, token: str = ""):
    component = components.declare_component("cart_toss", path=str(Path(__file__).with_name("cart_component")))
    return component(html=build_cart_html(category, model, platform, price, decision, reason, token),
                     token=token, key=f"cart_scene_{token}", default=None)
