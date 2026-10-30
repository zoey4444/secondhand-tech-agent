"""Explain how each submitted field contributes, with traceable findings."""
from domain_knowledge import checklist_for_case, transaction_guidance
from market_comparison import compare_prices


def build_input_feedback(case, review):
    rows = []
    def add(key, label, role):
        value = str(case.get(key) or '').strip()
        related = [i['summary'] for i in review.get('issues', [])
                   if any(e.get('source') == key for e in i.get('evidence', []))]
        claims = [c['claim'] for c in review.get('claims', []) if c.get('source') == key
                  and key in {'listing', 'chat', 'seller_profile'} or c.get('source') == key and key.startswith('reply_')]
        feedback = '；'.join(dict.fromkeys(related or claims))
        if not value:
            feedback = '未填写，本轮没有将此项作为判断依据。'
        elif not feedback:
            feedback = '已纳入本轮对照，但没有形成单独可引用的发现；不代表内容已获核实。'
        rows.append({'field': key, 'label': label, 'value': value or '未填写',
                     'role': role, 'feedback': feedback})
    platform = str(case.get('platform') or '未填写')
    payment = str(case.get('payment_channel') or '尚未确定')
    channel_note = (f'展示于{platform}，计划通过{payment}付款；需要核对两处商品、配件、价格及订单是否一致。'
                    if payment not in {'尚未确定', platform} else
                    '用于核对商品信息的出处；展示渠道本身不能证明交易有保障。')
    add('platform', '商品展示渠道', channel_note)
    add('payment_channel', '下单付款渠道', transaction_guidance(case) + ' 所填渠道是计划安排，尚未核实订单。')
    add('category', '商品类别', '据此生成验货重点：' + checklist_for_case(case))
    add('model', '型号、版本与配置', '用于确定核验对象、对照描述和聊天中的型号配置，并核对参考报价是否为同款。简称不等于型号错误。')
    price = compare_prices(case)
    add('price', '商品标价', '用于对照描述、聊天中的成交价。' + price['summary'])
    add('listing', '商品描述', '提取成色、功能、维修、配件和售后承诺，逐项与聊天核对；卖家描述仍是待核实陈述。')
    add('chat', '聊天与截图识别文字', '用于发现补充说明、改口或未回答的问题；截图须先识别并核对文字，未经识别的图片未进入本次分析。')
    if case.get('seller_profile'):
        add('seller_profile', '卖家主页与评价', '核对账号对应关系与评价背景；评价不等于成交，好评不证明本件商品安全，其他交易评价不直接证明本件故障。')
    add('price_samples', '同款参考报价', price['summary'])
    add('price_source', '参考来源及查看日期', '用于标记参考报价出处和查看时间；内容由用户提供，未联网核实。' + price['summary'])
    for index, reply in enumerate(case.get('seller_replies') or [], 1):
        key = f'reply_{index}'
        related = [i['summary'] for i in review.get('issues', []) if any(e.get('source') == key for e in i.get('evidence', []))]
        rows.append(dict(field=key, label=f'第 {index} 次卖家回复', value=str(reply),
                         role='与上轮疑点对照；卖家解释不等于独立证据。',
                         feedback='；'.join(related) or '该回复尚未形成单独可引用的结论，不能视为疑点已解决。'))
    return rows


def feedback_text(rows):
    return '\n\n'.join(f"{r['label']}\n你填写的：{r['value']}\n用于：{r['role']}" +
                       (f"\n本轮反馈：{r['feedback']}" if r['feedback'] else '') for r in rows)
