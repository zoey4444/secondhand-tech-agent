"""Live product card shown while a user fills the review form."""

from html import escape

import streamlit as st
from mascot_ui import asset_data_uri, device_icon_data_uri


def show_product_preview(category: str, model: str, platform: str, price: str, listing: str) -> None:
    """Show the same product card as the toss scene, building it in form order."""
    values = [bool(platform.strip()), bool(model.strip()), bool(price.strip()), bool(listing.strip())]
    count = sum(values)
    category_label = escape((category or "数码商品")[:30])
    model_label = escape((model or "等小鸡挑选装备型号")[:52])
    platform_label = escape((platform or "先找商品摊位")[:24])
    price_text = (price or "").strip()
    price_badge = f'<span class="pv-ticket">{escape(price_text[:20])}</span>' if price_text else ""
    icon_label = escape(category or "商品", quote=True)
    icon_markup = f'<div class="pv-device-icon"><img src="{device_icon_data_uri(category)}" alt="{icon_label}像素图标"></div>'
    progress = "".join(
        f'<span class="pv-dot {"pv-on" if filled else ""}"></span>' for filled in values
    )
    template = """
<style>
.pv-wrap{position:relative;overflow:hidden;min-height:430px;border-radius:24px;padding:20px;background:radial-gradient(circle at 74% 16%,#caebed 0,#B5dae9 43%,#cce7d9 100%);border:2px solid #63bad9;color:#174b5b;box-shadow:0 15px 32px #63bad933}
.pv-title{font-size:14px;letter-spacing:1px;font-weight:900}.pv-hint{font-size:13px;color:#315b6b;margin-top:4px}
.pv-spark{position:absolute;color:#63bad9;font-size:22px;animation:pv-twinkle 1.8s ease-in-out infinite alternate}.pv-s1{left:18%;top:29%}.pv-s2{right:17%;top:45%;animation-delay:.7s}.pv-s3{right:26%;top:16%;animation-delay:1.2s}
.pv-card{position:relative;width:256px;height:270px;margin:22px auto 0;border-radius:27px;background:linear-gradient(145deg,#63bad9,#B5dae9);border:2px solid #caebed;box-shadow:0 18px 0 #63bad955,0 24px 43px #63bad94d;display:flex;flex-direction:column;align-items:center;padding:12px 14px;animation:pv-appear .5s ease-out both;transition:transform .25s,box-shadow .25s}
.pv-card.has-model:hover{transform:translateY(-4px) rotate(-1deg);box-shadow:0 21px 0 #63bad955,0 28px 46px #63bad955}
.pv-device-icon{width:150px;height:145px;flex:0 0 145px;display:flex;align-items:center;justify-content:center;font-size:92px;line-height:1;filter:drop-shadow(0 8px 9px #174b5b22)}
.pv-device-icon span{display:block;transform:translateY(-2px)}
.pv-name{width:100%;font-size:17px;font-weight:900;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:-4px;color:#174b60}
.pv-meta{font-size:13px;color:#215c71;text-align:center;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
.pv-ticket{position:absolute;right:-18px;top:18px;transform:rotate(13deg);background:#cce7d9;color:#174b60;border-radius:10px;padding:7px 11px;font-size:15px;font-weight:900;box-shadow:0 7px 12px #174b5b44;animation:pv-appear .3s ease-out both}
.pv-card-foot{font-size:11px;color:#286782;margin-top:8px;opacity:.85}
.pv-bottom{display:flex;align-items:center;justify-content:space-between;margin-top:24px;font-size:12px;font-weight:800}.pv-dots{display:flex;gap:5px}.pv-dot{width:16px;height:9px;border-radius:999px;background:#B5dae9;border:1px solid #63bad9}.pv-dot.pv-on{background:#63bad9}
@keyframes pv-appear{from{opacity:0;transform:translateY(10px) scale(.96)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes pv-twinkle{to{opacity:.35;transform:scale(.65)}}
@media(max-width:650px){.pv-wrap{min-height:400px}.pv-card{width:220px;height:250px}.pv-device-icon{width:128px;height:128px;flex-basis:128px;font-size:80px}}
@media(prefers-reduced-motion:reduce){.pv-card,.pv-ticket,.pv-spark{animation:none}}
.pv-wrap{border:4px solid #643820;border-radius:6px;background-image:linear-gradient(180deg,#4b7fcb 0%,#f9c49d 62%,transparent 62%),url('__GRASS_URI__');background-size:auto,64px 64px;box-shadow:0 6px 0 #ba7a50;color:#491c17;image-rendering:pixelated}
.pv-title,.pv-hint{position:relative;display:table;background:#ffe0a1e8;padding:3px 6px}.pv-title{color:#491c17}.pv-hint{color:#643820}.pv-spark{color:#f7be4f}.pv-card{border:4px solid #643820;border-radius:4px;background:#ffe0a1;box-shadow:6px 6px 0 #643820,0 13px 0 #4c725c}.pv-card.has-model:hover{box-shadow:8px 8px 0 #643820,0 15px 0 #4c725c}
.pv-name{color:#491c17}.pv-meta,.pv-card-foot{color:#643820}.pv-ticket{border:2px solid #643820;border-radius:2px;background:#f7be4f;color:#491c17;box-shadow:3px 3px 0 #643820}.pv-dot{border:2px solid #4c725c;border-radius:2px;background:#f5ce87;height:12px}.pv-dot.pv-on{background:#4c725c}.pv-bottom{color:#643820;background:#ffe0a1e8;padding:4px 6px}
.pv-device-icon img{width:128px;height:128px;object-fit:contain;image-rendering:pixelated;filter:drop-shadow(4px 5px 0 #64382066)}
</style>
<div class="pv-wrap"><div class="pv-title">🐥 小鸡的集市清单正在成形</div><div class="pv-hint">选好摊位、型号、标价和商品描述，线索就会逐格点亮。</div>
<div class="pv-spark pv-s1">✦</div><div class="pv-spark pv-s2">✧</div><div class="pv-spark pv-s3">✦</div>
<div class="pv-card __CARD_CLASS__">__PRICE_BADGE__ __ICON__<div class="pv-name">__MODEL__</div><div class="pv-meta">__CATEGORY__ · __PLATFORM__</div><div class="pv-card-foot">__LISTING_STATE__</div></div>
<div class="pv-bottom"><span>集市线索 __COUNT__ / 4</span><span class="pv-dots">__DOTS__</span></div></div>
"""
    html = (template.replace("__CARD_CLASS__", "has-model" if model.strip() else "")
            .replace("__PRICE_BADGE__", price_badge)
            .replace("__ICON__", icon_markup)
            .replace("__MODEL__", model_label)
            .replace("__CATEGORY__", category_label)
            .replace("__PLATFORM__", platform_label)
            .replace("__LISTING_STATE__", "商品描述已装进背包" if listing.strip() else "背包里还缺商品描述")
            .replace("__COUNT__", str(count))
            .replace("__DOTS__", progress)
            .replace("__GRASS_URI__", asset_data_uri("pixel_grass_64.png")))
    st.html(html)
