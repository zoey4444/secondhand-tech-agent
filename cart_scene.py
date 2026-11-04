"""Interactive product toss scene. Only escaped display text enters the HTML."""

from html import escape
import json
from pathlib import Path

import streamlit.components.v1 as components
from mascot_ui import asset_data_uri, chick_sprite_data_uri, device_icon_data_uri


def product_icon(category: str) -> str:
    """Return the same original pixel icon used by the growing product card."""
    label = escape(category or "数码商品", quote=True)
    return f'<img class="device-icon" src="{device_icon_data_uri(category)}" alt="{label}像素图标">'


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
        "__CHICK_URI__": chick_sprite_data_uri(),
        "__GRASS_URI__": asset_data_uri("pixel_grass_64.png"),
        "__SOIL_URI__": asset_data_uri("pixel_soil_64.png"),
        "__FLOWER_URI__": asset_data_uri("pixel_flower_64.png"),
        "__CRATE_URI__": asset_data_uri("pixel_crate_64.png"),
        "__TOKEN_JSON__": json.dumps(token).replace("<", "\\u003c"),
        "__REASON_JSON__": json.dumps(reason, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"),
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
@media(max-width:720px){.shell{padding:16px;min-height:580px}.title{font-size:20px}.badge{display:none}.scene{height:365px}.product{left:5%;top:109px;width:145px;height:178px;padding:9px}.product svg{width:94px;height:94px}.product .device{font-size:12px}.cartzone{right:1%;top:105px;width:185px;height:170px}.cartlabel{top:292px;right:2%;font-size:11px}.floor{left:6%;font-size:11px}.trail{display:none}.product .ticket{right:-8px;font-size:11px}.product .device-icon{width:94px;height:94px}}
@media(prefers-reduced-motion:reduce){.cloud,.spark,.trail,.confetti{animation:none}.product{transition-duration:.01s}}
body{background:#caebed;color:#174b60}
.shell{border-color:#63bad9;background:radial-gradient(circle at 24% 7%,#caebed 0%,transparent 36%),linear-gradient(135deg,#B5dae9,#cce7d9 55%,#caebed);color:#174b60}
.eyebrow{color:#267895}.title{color:#174b60}.badge{background:#cce7d9;border-color:#63bad9;color:#174b60}
.scene{background:linear-gradient(180deg,#caebed,#B5dae9 63%,#cce7d9 63%)}.scene:before{background:#63bad9}.cloud{background:#caebed;opacity:.72}.spark,.trail{color:#318aaa}
.product{background:linear-gradient(145deg,#63bad9,#B5dae9);border-color:#caebed;color:#174b60;box-shadow:0 16px 0 #63bad955,0 24px 43px #63bad94d}.product .meta{color:#215c71}.product .ticket{background:#cce7d9;color:#174b60}
.cartzone svg path[stroke]{stroke:#1b6077}.cartzone svg circle{fill:#63bad9}.cartlabel,.floor{color:#174b60}
.throw{background:linear-gradient(90deg,#63bad9,#B5dae9);color:#143f53;box-shadow:0 7px 14px #63bad955}.again{background:#cce7d9;border-color:#63bad9;color:#174b60}.tip{color:#315e70}
.feedback{background:#caebed;border-color:#63bad9;color:#174b60}.feedback.allow{background:#cce7d9;border-color:#63bad9}.feedback.reject{background:#B5dae9;border-color:#63bad9}.feedback.wait{background:#caebed;border-color:#63bad9}
.chick-puppet{position:absolute;left:45%;bottom:4px;width:108px;aspect-ratio:272/364;z-index:3;pointer-events:none;background-image:url("__CHICK_URI__");background-size:400% 100%;background-repeat:no-repeat;background-position:33.333% 0;filter:drop-shadow(0 9px 7px #27576d55);transform-origin:50% 88%;animation:chick-idle 2s ease-in-out infinite}
.chick-puppet[data-mood="neutral"]{background-position:0% 0}.chick-puppet[data-mood="expect"]{background-position:33.333% 0}.chick-puppet[data-mood="denied"]{background-position:66.667% 0}.chick-puppet[data-mood="aha"]{background-position:100% 0}
.chick-puppet.react[data-mood="denied"]{animation:chick-denied .72s ease-in-out 2}.chick-puppet.react[data-mood="aha"]{animation:chick-aha .68s cubic-bezier(.18,.8,.24,1.2) 2}
@keyframes chick-idle{50%{transform:translateY(-7px) rotate(-2deg)}}@keyframes chick-denied{25%{transform:translateY(5px) rotate(-9deg)}65%{transform:translateY(7px) rotate(7deg)}}@keyframes chick-aha{40%{transform:translateY(-18px) scale(1.07)}75%{transform:translateY(2px) scale(.98)}}
@media(max-width:720px){.chick-puppet{left:43%;bottom:8px;width:72px}}
@media(prefers-reduced-motion:reduce){.chick-puppet,.chick-puppet.react{animation:none}}
/* Original pixel-farm scene; the decision text and interaction remain explicit. */
body{background:#f5ce87;color:#491c17}
.shell{border:4px solid #643820;border-radius:7px;background:#ffe0a1;box-shadow:inset 0 0 0 4px #ba7a50;color:#491c17;padding:22px}
.eyebrow{color:#4c725c;letter-spacing:1.5px}.title{color:#491c17;text-shadow:2px 2px #ffe0a1}.badge{background:#f5ce87;border:2px solid #643820;border-radius:3px;color:#491c17}
.scene{border:3px solid #4c725c;border-radius:4px;background-image:url('__FLOWER_URI__'),linear-gradient(180deg,#4b7fcb 0%,#f9c49d 62%,transparent 62%),url('__GRASS_URI__');background-size:64px 64px,auto,64px 64px;background-repeat:no-repeat,no-repeat,repeat;background-position:7% 83%,0 0,0 0;box-shadow:inset 0 0 0 4px #ffe0a1;image-rendering:pixelated}
.scene:before{top:62%;height:8px;background:#4c725c;opacity:1}.scene:after{content:"";position:absolute;right:1%;bottom:9px;width:64px;height:64px;background:url('__CRATE_URI__') center/contain no-repeat;image-rendering:pixelated;opacity:.95}
.cloud{background:#ffe0a1;border-radius:4px;opacity:.78;filter:none;box-shadow:9px -7px 0 #ffe0a1,28px 0 0 #ffe0a1}.spark,.trail{color:#f7be4f}
.product .device-icon{width:125px;height:118px;object-fit:contain;image-rendering:pixelated;filter:drop-shadow(4px 5px 0 #64382066)}.product{background:#ffe0a1;border:4px solid #643820;border-radius:5px;color:#491c17;box-shadow:6px 6px 0 #805f43,0 13px 0 #5e774f;transform-origin:center center}.product .meta{color:#643820}.product .ticket{background:#f7be4f;border:2px solid #643820;border-radius:2px;color:#491c17;box-shadow:3px 3px 0 #88694e}
.cartzone svg path[stroke]{stroke:#6c4e38}.cartzone svg circle{fill:#a6794f}.cartzone svg{filter:drop-shadow(5px 8px 0 #5d6f4a77)}.cartlabel,.floor{color:#491c17;background:#ffe0a1d9;padding:4px 7px;border:1px solid #643820}.floor{bottom:18px}
.throw{background:#4b7fcb;color:#f6f4fc;border:3px solid #3a47a0;border-radius:3px;box-shadow:0 5px 0 #3a47a0}.throw:hover{filter:brightness(1.06)}.again{background:#f5ce87;border:2px solid #643820;border-radius:3px;color:#491c17}.tip{color:#643820}
.feedback{background:#ffe0a1;border:3px solid #643820;border-radius:3px;color:#491c17;box-shadow:3px 3px 0 #cdbb95}.feedback.allow{background:#f5ce87;border-color:#1c7e1b}.feedback.reject{background:#f9c49d;border-color:#970138}.feedback.wait{background:#f5ce87;border-color:#ec7a43}
.chick-puppet{filter:drop-shadow(5px 5px 0 #4f6d4d55)}
@media(max-width:720px){.shell{padding:12px}.scene:after{width:42px;height:42px}.floor{max-width:180px}.cartlabel{max-width:115px;text-align:center}.chick-puppet{left:42%}}
</style></head>
<body data-decision="__DECISION__"><div class="shell"><div class="top"><div><div class="eyebrow">叽有数——买不买心里有数</div><div class="title">叽有数将这件装备投进购物车</div></div><div class="badge">拖动商品，或点击“投掷”</div></div>
<div class="scene" id="scene"><div class="cloud a"></div><div class="cloud b"></div><div class="spark">✦</div>
<div class="product" id="product" tabindex="0" role="button" aria-label="拖动商品到购物车"><span class="ticket">__PRICE__</span>__ICON__<div class="device">__MODEL__</div><div class="meta">__CATEGORY__ · __PLATFORM__</div></div>
<div class="trail">➜</div><div class="chick-puppet" id="chick" data-mood="expect" aria-hidden="true"></div><div class="cartzone" id="cartZone"><svg viewBox="0 0 300 230" aria-label="购物车图案" role="img"><defs><linearGradient id="cartGrad" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ba7a50"/><stop offset="1" stop-color="#f5ce87"/></linearGradient></defs><path d="M28 45h33l27 112h153l29-82H78" stroke="#643820" stroke-width="10" stroke-linejoin="round" fill="none" stroke-linecap="round"/><path d="M84 78h185l-28 79H102z" fill="url(#cartGrad)" opacity=".84"/><path d="M95 168h146" stroke="#643820" stroke-width="10" stroke-linecap="round"/><circle cx="117" cy="195" r="15" fill="#ba7a50"/><circle cx="220" cy="195" r="15" fill="#ba7a50"/></svg></div>
<div class="cartlabel">叽有数的候选购物车</div><div class="floor">↗ 把装备拖到购物车上方松开</div><div class="confetti" id="confetti">✦ ✧ ✦ ✧</div></div>
<div class="controls"><button class="throw" id="throw" type="button">🐥 帮叽有数投掷</button><button class="again" id="again" type="button">再看一次</button><span class="tip">投掷动画只展示分析结论；交易前仍需实物核验。</span></div>
<div class="feedback" id="feedback" role="status" aria-live="polite">叽有数带着商品线索来到购物车。拖动装备，或点击“帮叽有数投掷”，查看分析结论。</div>
</div>
<script>
(function(){
 const product=document.getElementById('product'); const cart=document.getElementById('cartZone');
 const feedback=document.getElementById('feedback'); const throwButton=document.getElementById('throw'); const chick=document.getElementById('chick');
 const again=document.getElementById('again'); const confetti=document.getElementById('confetti');
 const decision=document.body.dataset.decision; const reason=__REASON_JSON__;
 again.disabled=decision==='pending';
 let dragging=false, attempted=false, startX=0, startY=0, dragX=0, dragY=0;
 function setFeedback(title,detail,kind){feedback.className='feedback '+kind;feedback.textContent='';const strong=document.createElement('strong');strong.textContent=title;feedback.appendChild(strong);feedback.appendChild(document.createElement('br'));feedback.appendChild(document.createTextNode(detail));}
 function setChickMood(mood){chick.dataset.mood=mood;chick.classList.remove('react');void chick.offsetWidth;chick.classList.add('react');}
 function toss(){
  if(attempted)return; attempted=true; dragging=false; throwButton.disabled=true; product.classList.remove('dragging');
  if(decision==='pending'){
   again.disabled=true;
   setChickMood('expect');
   product.style.transform='translate(90px,-50px) rotate(-15deg)';
   setFeedback('正在核对提交的材料……','分析完成后，这里会显示投掷结果，下方会整理出线索手账。','wait');
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
    setTimeout(function(){product.style.opacity='0';confetti.classList.add('on');setChickMood('aha');setFeedback('✅ 当前材料未见明显阻断项',reason,'allow');},550);
   } else {
    product.style.transform='translate('+dx+'px,'+(dy-25)+'px) rotate(-18deg) scale(.84)';
    setTimeout(function(){cart.classList.add('shake');product.style.transform='translate(0,0) rotate(-8deg)';setTimeout(function(){product.style.transform='';},420);if(decision==='reject'){setChickMood('denied');setFeedback('⛔ 被购物车弹回：暂不建议购买',reason,'reject');}else{setChickMood('aha');setFeedback('🟡 先核对商品信息，再决定',reason,'wait');}},550);
   }
  },380);
 }
 function reset(){attempted=false;dragging=false;dragX=0;dragY=0;throwButton.disabled=false;cart.classList.remove('shake');confetti.classList.remove('on');product.style.transition='';product.style.opacity='1';product.style.transform='';setChickMood('expect');feedback.className='feedback';feedback.textContent='正在重播本次分析结果……';if(decision!=='pending'){toss();}}
 product.addEventListener('pointerdown',function(e){if(attempted)return;dragging=true;startX=e.clientX;startY=e.clientY;dragX=0;dragY=0;product.classList.add('dragging');product.setPointerCapture(e.pointerId);});
 product.addEventListener('pointermove',function(e){if(!dragging)return;dragX=e.clientX-startX;dragY=e.clientY-startY;product.style.transform='translate('+dragX+'px,'+dragY+'px) rotate(-5deg)';});
 product.addEventListener('pointerup',function(){if(!dragging)return;dragging=false;const p=product.getBoundingClientRect(),c=cart.getBoundingClientRect();const overlap=p.right>c.left&&p.left<c.right&&p.bottom>c.top&&p.top<c.bottom;if(overlap){toss();}else{product.classList.remove('dragging');product.style.transform='';dragX=0;dragY=0;setFeedback('再靠近一点','把商品拖到购物车上方再松开，或点击“帮叽有数投掷”。','wait');}});
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
