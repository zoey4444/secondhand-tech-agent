"""Offline regression checks from the manual evaluation; no model quality scores."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_core import run_review, SYSTEM_PROMPT
from puzzle_feedback import build_puzzle_html, seller_message
from cart_scene import build_cart_html
from review_policy import device_question

BASE = dict(platform="闲鱼", category="耳机", model="Bose QuietComfort Ultra Headphones",
            price="1200", listing="详情写原盒和收纳包齐全。", chat="卖家：盒子丢了，收纳包也找不到了。")
EMPTY = dict(claims=[], issues=[], overview="待核实")


class Model:
    def __init__(self, data):
        self.data = data
    def invoke(self, messages):
        return type("Response", (), {"content": json.dumps(self.data, ensure_ascii=False)})()


def issue(summary, quote, source="listing", **extras):
    return dict(summary=summary, severity="high", evidence=[dict(source=source, quote=quote)],
                question="方便说明一下吗？", **extras)


class BatchReviewTests(unittest.TestCase):
    def review(self, data=EMPTY, **case):
        return run_review({**BASE, **case}, Model(data))

    def test_unknown_model_and_empty_description(self):
        r = self.review(model="不清楚型号", listing="", chat="")
        self.assertEqual(r["decision"], "wait")
        self.assertIn("具体型号", r["missing"])
        self.assertIn("商品描述", r["missing"])
        self.assertTrue(any("型号标签" in q for q in r["questions"]))

    def test_missing_evidence_is_not_rejection_even_if_model_calls_it_high(self):
        r = self.review({**EMPTY, "issues":[issue("续航只有口头说法", "电池很好")]}, listing="电池很好")
        self.assertEqual(r["decision"], "wait")

    def test_accessory_conflict_has_both_sources_and_one_question(self):
        a = issue("商品页和聊天对配件的说法不一致", BASE["listing"])
        a["evidence"].append(dict(source="chat", quote=BASE["chat"]))
        a["question"] = "最终随货有哪些配件？方便拍张合照吗？"
        b = issue("配件需列清单", BASE["chat"], "chat")
        b["question"] = "原盒和收纳包是不是随货？"
        data = {**EMPTY, "issues":[a,b], "claims":[dict(source="chat", quote=BASE["chat"], claim="卖家说盒子和收纳包丢失") ]}
        r = self.review(data)
        self.assertEqual(len(r["questions"]), 1)
        self.assertEqual(r["decision"], "reject")
        html = build_puzzle_html(r["analysis"], r["evidence_notes"], BASE, r)
        for value in ("盒子和收纳包丢失", BASE["listing"], BASE["chat"], "配件需列清单"):
            self.assertIn(value, html)
        self.assertNotIn("状态：unanswered", html)
        self.assertIn("聊天记录", html)

    def test_no_single_sided_conflict(self):
        r = self.review({**EMPTY, "issues":[issue("配件说法矛盾", BASE["listing"])]})
        self.assertFalse(r["issues"])
        self.assertGreater(r["invalid_citations"], 0)

    def test_market_price_inference_is_removed(self):
        r = self.review({**EMPTY, "issues":[issue("明显低于市场价", "现价420元")]},
                        price="420", listing="原价1600元，现价420元", chat="")
        self.assertFalse(r["issues"])
        self.assertEqual(r["decision"], "wait")

    def test_negated_transfer_does_not_hide_later_positive_request(self):
        r = self.review(listing="不要微信转账，但先付定金。", chat="")
        self.assertTrue(any(i["kind"] == "off_platform" for i in r["issues"]))
        self.assertEqual(r["decision"], "reject")

    def test_contact_only_is_not_a_transfer_request(self):
        r = self.review(listing="加微信看照片，付款走闲鱼订单。", chat="")
        self.assertFalse(any(i["kind"] == "off_platform" for i in r["issues"]))

    def test_two_platforms_are_preserved(self):
        r = self.review(platform="小红书", payment_channel="闲鱼", listing="实际在闲鱼下单付款", chat="")
        self.assertIn("商品展示渠道：小红书", r["analysis"])
        self.assertIn("下单付款渠道（用户填写）：闲鱼", r["analysis"])

    def test_small_price_changes_are_not_ignored(self):
        r = self.review(price="1200", listing="现在1201元", chat="")
        self.assertTrue(any(i["kind"] == "price_conflict" for i in r["issues"]))

    def test_payment_field_changes_actual_payment_warning(self):
        normal = self.review(payment_channel="闲鱼", listing="自用", chat="")
        personal = self.review(payment_channel="个人转账", listing="自用", chat="")
        self.assertFalse(any(i["kind"] == "off_platform" for i in normal["issues"]))
        self.assertTrue(any(i["kind"] == "off_platform" for i in personal["issues"]))

    def test_latest_price_reply_supersedes_older_quote(self):
        r = self.review(price="1200", listing="自用", chat="实际卖1300元", seller_replies=["最终价格1200元"])
        self.assertFalse(any(i["kind"] == "price_revision" for i in r["issues"]))

    def test_reply_updates_same_issue_without_duplicate(self):
        a = issue("电池状态待核实", "电池很好")
        first = self.review({**EMPTY, "issues":[a]}, listing="电池很好", chat="")
        a = issue("卖家说电池容量为85%，尚无截图", "容量85%", "reply_1",
                  reply_status="answered_claim_only", previous_id=first["issues"][0]["id"])
        second = self.review({**EMPTY, "issues":[a]}, listing="电池很好", chat="",
                             seller_replies=["容量85%"], previous_issues=first["issues"])
        self.assertEqual(len(second["issues"]), 1)
        self.assertEqual(second["decision"], "wait")
        self.assertIn("卖家已说明，尚未核实", second["analysis"])

    def test_guarantee_does_not_clear_previous_issue(self):
        a = issue("电池状态待核实", "电池很好")
        first = self.review({**EMPTY, "issues":[a]}, listing="电池很好", chat="")
        second = self.review(seller_replies=["放心吧"], previous_issues=first["issues"])
        self.assertEqual(second["issues"][0]["status"], "awaiting_independent_evidence")

    def test_unsafe_water_test_is_replaced(self):
        text = seller_message("- 能否当面用清水短时测试？")
        self.assertNotIn("清水", text)
        self.assertIn("进水或维修", text)

    def test_skill_is_loaded_into_model_prompt(self):
        self.assertIn("剩下随货的东西", SYSTEM_PROMPT)

    def test_iphone14_does_not_require_cycle_count_screen(self):
        q = device_question("请提供设置中的循环次数截图", {"model":"Apple iPhone 14"})
        self.assertNotIn("循环", q)
        self.assertIn("本机能显示", q)

    def test_m2_does_not_use_intel_firmware_password_question(self):
        q = device_question("能否进入固件密码设置？", {"model":"Apple MacBook Air M2"})
        self.assertNotIn("固件密码", q)

    def test_scene_escapes_untrusted_fields(self):
        html = build_cart_html("耳机", "</script><script>alert(1)</script>", "闲鱼", "1200", "pending", "", "test")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("cart:toss", html)
        self.assertIn("data-decision=\"pending\"", html)

    def test_multiple_findings_are_in_card_not_only_details(self):
        r = self.review({**EMPTY, "issues":[issue("充电状态待核实", "未测试充电"), issue("麦克风未测试", "麦克风没测")]},
                        listing="未测试充电，麦克风没测", chat="")
        html = build_puzzle_html(r["analysis"], r["evidence_notes"], BASE, r)
        summary = html.split('class="pz-summary"')[2].split('</p>')[0]
        self.assertIn("充电状态待核实", summary)
        self.assertIn("麦克风未测试", summary)


if __name__ == "__main__":
    unittest.main()
