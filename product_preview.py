"""Live cartoon preview shown while a user builds a product."""

from html import escape

import streamlit as st

from cart_scene import product_icon


def show_product_preview(category: str, model: str, platform: str, price: str, listing: str) -> None:
    bits = [bool(platform), bool(model), bool(price.strip()), bool(listing.strip())]
    count = sum(bits)
    label = escape((model or "等待型号加入")[:52])
    platform_label = escape((platform or "待选平台")[:24])
    price_label = escape((price or "待贴价格")[:20])
    progress = "".join(
        f'<span class="pv-dot {"pv-on" if filled else ""}"></span>' for filled in bits
    )
    st.html(
        """
<style>
.pv-wrap{position:relative;overflow:hidden;min-height:298px;border-radius:24px;padding:20px;background:radial-gradient(circle at 74% 16%,#caebed 0,#B5dae9 43%,#cce7d9 100%);border:2px solid #63bad9;color:#174b5b;box-shadow:0 15px 32px #63bad933}
.pv-title{font-size:14px;letter-spacing:1px;font-weight:900}.pv-hint{font-size:13px;color:#315b6b;margin-top:4px}
.pv-device{width:158px;height:160px;margin:8px auto 0;display:flex;align-items:center;justify-content:center;animation:pv-float 3s ease-in-out infinite;filter:drop-shadow(0 14px 12px #63bad955)}
.pv-device svg{width:148px;height:146px}.pv-device svg g{stroke:#1c6783}
.pv-spark{position:absolute;color:#63bad9;font-size:22px;animation:pv-twinkle 1.8s ease-in-out infinite alternate}.pv-s1{left:18%;top:29%}.pv-s2{right:17%;top:45%;animation-delay:.7s}.pv-s3{right:26%;top:16%;animation-delay:1.2s}
.pv-name{font-size:17px;font-weight:900;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.pv-tags{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:10px}.pv-tag{background:#caebed;border:1px solid #63bad9;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:750}
.pv-bottom{display:flex;align-items:center;justify-content:space-between;margin-top:14px;font-size:12px;font-weight:800}.pv-dots{display:flex;gap:5px}.pv-dot{width:16px;height:9px;border-radius:999px;background:#B5dae9;border:1px solid #63bad9}.pv-dot.pv-on{background:#63bad9}
@keyframes pv-float{50%{transform:translateY(-10px) rotate(3deg)}}@keyframes pv-twinkle{to{opacity:.35;transform:scale(.65)}}
@media(prefers-reduced-motion:reduce){.pv-device,.pv-spark{animation:none}}
</style>
<div class="pv-wrap"><div class="pv-title">✨ 你的商品正在成形</div><div class="pv-hint">每填一项，就为商品贴上一块线索。</div>
<div class="pv-spark pv-s1">✦</div><div class="pv-spark pv-s2">✧</div><div class="pv-spark pv-s3">✦</div>
<div class="pv-device">__ICON__</div><div class="pv-name">__MODEL__</div>
<div class="pv-tags"><span class="pv-tag">📍 __PLATFORM__</span><span class="pv-tag">🏷️ __PRICE__</span></div>
<div class="pv-bottom"><span>商品线索 __COUNT__ / 4</span><span class="pv-dots">__DOTS__</span></div></div>
"""
        .replace("__ICON__", product_icon(category))
        .replace("__MODEL__", label)
        .replace("__PLATFORM__", platform_label)
        .replace("__PRICE__", price_label)
        .replace("__COUNT__", str(count))
        .replace("__DOTS__", progress)
    )
