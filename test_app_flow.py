"""Streamlit state-flow checks with a stubbed model and component event."""
import os
import faulthandler
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest
import streamlit as st


class FlowTests(unittest.TestCase):
    def test_throw_gates_model_and_result_and_edit_clears_scene(self):
        faulthandler.dump_traceback_later(45)
        self.addCleanup(faulthandler.cancel_dump_traceback_later)
        controller = {"toss":False}
        def scene(*args):
            controller["decision"] = args[4]
            return {"action":"toss", "token":args[-1]} if controller["toss"] else None
        result = dict(decision="wait", decision_reason="先补资料", analysis="## 🔎 缺失或矛盾\n型号未知",
                      issues=[], claims=[], questions=[], evidence_notes="")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY":"offline-test-placeholder"}), \
             patch("cart_scene.show_cart_scene", side_effect=scene), \
             patch("agent_core.run_review", return_value=result) as model:
            at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
            def button(label):
                return next(b for b in at.button if b.label == label)
            button("记下摊位，去看装备 →").click().run()
            at.selectbox[1].select("不清楚型号").run()
            button("记下型号，去收集线索 →").click().run()
            at.radio[0].set_value("未标价").run()
            button("线索装进背包，去购物车 →").click().run()
            button("🛒 叽有数带着线索去购物车").click().run()
            self.assertFalse(at.exception)
            self.assertEqual(model.call_count, 0)
            self.assertEqual(controller["decision"], "pending")
            self.assertNotIn("review_result", at.session_state)
            controller["toss"] = True
            at.run()
            self.assertFalse(at.exception)
            self.assertEqual(model.call_count, 1)
            self.assertIn("review_result", at.session_state)
            at.run()
            self.assertEqual(model.call_count, 1)
            button("返回整理线索／补充截图").click().run()
            self.assertNotIn("review_result", at.session_state)
            self.assertNotIn("scene_token", at.session_state)
            controller["toss"] = False
            button("线索装进背包，去购物车 →").click().run()
            self.assertNotIn("review_result", at.session_state)
            self.assertEqual(model.call_count, 1)


if __name__ == "__main__":
    unittest.main()
