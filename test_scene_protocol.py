import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cart_scene import build_cart_html

payload = dict(pending=build_cart_html("耳机", "Bose", "闲鱼", "1200", "pending", "", "test-token"),
               finished=build_cart_html("耳机", "Bose", "闲鱼", "1200", "wait", "先补信息", "test-token"),
               wrapper=(ROOT / "cart_component/index.html").read_text(encoding="utf-8"))
subprocess.run(["node", str(ROOT / "tests/test_scene_protocol.cjs")],
               input=json.dumps(payload), text=True, check=True)
