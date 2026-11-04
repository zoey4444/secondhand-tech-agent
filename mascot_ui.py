"""Local, transparent shopping-chick artwork for the Streamlit UI."""

import base64
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=8)
def asset_data_uri(filename: str) -> str:
    """Return an approved local UI asset as an inlined data URI."""
    allowed = {
        "shopping_chick_states.webp": "image/webp",
        "pixel_grass_64.png": "image/png",
        "pixel_soil_64.png": "image/png",
        "pixel_flower_64.png": "image/png",
        "pixel_crate_64.png": "image/png",
        **{f"device_{name}.png": "image/png" for name in (
            "phone", "tablet", "laptop", "desktop", "camera", "headphones",
            "watch", "console", "box",
        )},
    }
    mime = allowed[filename]
    path = Path(__file__).with_name("assets") / filename
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def chick_sprite_data_uri() -> str:
    """Return a small self-contained sprite; no remote asset request is needed."""
    return asset_data_uri("shopping_chick_states.webp")


def device_icon_data_uri(category: str) -> str:
    """Use a consistent original pixel icon in both product scenes."""
    categories = {
        "手机": "phone", "平板": "tablet", "笔记本电脑": "laptop",
        "台式电脑/配件": "desktop", "相机（单反/微单/CCD）": "camera",
        "耳机": "headphones", "智能手表/手环": "watch", "游戏机": "console",
    }
    return asset_data_uri(f"device_{categories.get(category, 'box')}.png")
