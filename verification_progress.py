"""Literature-informed, user-recorded verification coverage; never a risk score."""
import hashlib
import json
import re

METHOD_VERSION = '1.0'
REFERENCE = 'https://iiardjournals.org/get/IJSSMR/VOL.%2012%20NO.%201%202026/Identifying%20and%20Quantifying%20Weights%2048-60.pdf'
# Parent * local weights, Tables 3–4. Selecting this subset is our prototype design.
DIMENSIONS = (
    ('product', '商品信息一致性', .1911 * .2275, (
        ('identity', '核对型号、代际与配置是否对应同一件实物'),
        ('condition', '核对成色、功能和维修记录是否与描述一致'))),
    ('seller', '卖家信息披露', .2283 * .1648, (
        ('account', '核对商品页、聊天与主页是否为同一账号'),
        ('reviews', '核对评价数量、买卖角色和相关评价内容'))),
    ('payment', '交易安全', .2283 * .2266, (
        ('order', '核对展示商品与下单页面的商品、配件及价格'),
        ('payment_terms', '核对付款对象、付款方式和交付条件'))),
    ('inspection', '独立第三方商品评估', .2060 * .2177, (
        ('report_identity', '核对独立检测材料来源、日期和对应商品'),
        ('report_scope', '核对检测范围、检测结果与未覆盖的项目'))),
    ('aftersales', '卖家售后服务', .2008 * .2206, (
        ('return_terms', '核对本次二手交易的退换条件和期限'),
        ('responsibility', '核对问题责任、运费承担和约定记录'))),
)
STATUSES = {'pending': '待核验', 'claim': '仅有陈述', 'conflict': '存在未解决的矛盾',
            'checked': '已核对并记录结果', 'problem': '已核对，发现问题'}
CASE_KEYS = ('platform', 'payment_channel', 'category', 'model', 'price', 'listing', 'chat',
             'price_samples', 'price_source', 'seller_replies', 'seller_profile')


def case_fingerprint(case):
    payload = {key: case.get(key, [] if key == 'seller_replies' else '') for key in CASE_KEYS}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def calculate_progress(entries=None):
    """No text/LLM heuristics: completed checks require an explicit supporting note.

    Equal weights within each dimension are a prototype convention, not from AHP.
    Unknowns stay in the denominator; there is no N/A bypass in this first release.
    """
    entries = entries or {}
    total_weight = sum(d[2] for d in DIMENSIONS)
    rows, suggestions, problems = [], [], []
    for dim_id, label, raw_weight, checks in DIMENSIONS:
        weight = raw_weight / total_weight
        items = []
        for item_id, title in checks:
            entry = entries.get(item_id, {})
            status = entry.get('status', 'pending')
            if status not in STATUSES:
                status = 'pending'
            note = str(entry.get('note') or '').strip()
            completed = status in {'checked', 'problem'} and bool(note)
            item = dict(id=item_id, title=title, status=status, note=note, completed=completed)
            items.append(item)
            if status in {'problem', 'conflict'}:
                problems.append(item)
            if not completed:
                suggestions.append(dict(dimension=label, title=title, weight=weight / len(checks)))
        fraction = sum(item['completed'] for item in items) / len(items)
        rows.append(dict(id=dim_id, label=label, weight=weight, fraction=fraction, items=items))
    suggestions.sort(key=lambda item: -item['weight'])
    return dict(method_version=METHOD_VERSION, reference=REFERENCE,
                recorded_by='user', score=100 * sum(d['weight'] * d['fraction'] for d in rows),
                dimensions=rows, next_checks=suggestions[:3], problems=problems)


def _show_manual_verification(case, review):
    import streamlit as st
    fingerprint = case_fingerprint(case)
    prefix = f'verify_{fingerprint}_'
    st.markdown('### 🧩 五部分核验进度')
    st.caption('按你的核对记录计算，不是安全分。已有卖家陈述不会自动计为完成；完成度不改变上方模型判断。')
    store = st.session_state.setdefault('verification_records', {})
    saved = store.get(fingerprint, {})
    with st.expander('填写或更新核对记录'):
        st.write('有材料或实际检查结果时再标记已核对，并记录来源和结果。发现问题也算查清一项，但仍须处理问题。')
        st.caption('评价数不等于成交数；原购买订单的售后政策不自动适用于本次二手交易。缺少第三方报告仅表示该部分未核验，不单独决定是否停止交易。')
        with st.form(prefix + 'form'):
            draft = {}
            for _, label, _, checks in DIMENSIONS:
                st.markdown(f'**{label}**')
                for item_id, title in checks:
                    previous = saved.get(item_id, {})
                    options = list(STATUSES)
                    old_status = previous.get('status', 'pending')
                    status = st.selectbox(title, options, index=options.index(old_status) if old_status in options else 0,
                                          format_func=lambda value: STATUSES[value], key=prefix + item_id)
                    note = st.text_input('材料来源与核对结果', value=previous.get('note', ''),
                                         placeholder='例如：当前商品实物视频与型号标签已对照；仍未确认维修史',
                                         key=prefix + item_id + '_note')
                    draft[item_id] = dict(status=status, note=note.strip())
            submitted = st.form_submit_button('保存核对记录并更新进度')
        if submitted:
            incomplete = [key for key, entry in draft.items()
                          if entry['status'] in {'checked', 'problem'} and not entry['note']]
            if incomplete:
                st.warning('标记已核对的项目须填写材料来源和结果。本次尚未保存，请补充后再提交。')
            else:
                store[fingerprint] = draft
                saved = draft
                st.success('已保存。这是你的核对记录；若发现新问题，请同时提交到下方补充材料区进行重新分析。')
    result = calculate_progress(saved)
    st.progress(result['score'] / 100, text=f"用户记录的核验完成度：{result['score']:.1f}%")
    for row in result['dimensions']:
        done = sum(item['completed'] for item in row['items'])
        st.write(f"{row['label']}：{done} / {len(row['items'])} 项 · 参考权重 {row['weight']:.2%}")
    if result['problems']:
        st.warning('核对记录中有问题或未解决矛盾；即使完成度高，也不能据此付款。请把相关材料补充到下方重新分析。')
        for item in result['problems']:
            st.write(f"• {item['title']}：{item['note'] or '尚未记录依据'}")
    if review.get('decision') == 'reject':
        st.warning('优先处理上方停止交易的原因，完成度不会抵消该判断。')
    with st.expander('计算方法与适用边界'):
        st.write('从闲鱼满意度研究选取五项指标，按上层权重乘下层权重后重新归一化。它们是探索性的核验参考权重，不是风险概率。每部分的两项检查暂按等权处理，这是项目设计，未经过问卷验证。')
        st.write('没有材料、仅有陈述和未解决矛盾不计完成。没有报告仍保留在分母中。补充回复或修改商品资料后，需针对新材料重新记录进度，避免沿用旧结论；已下载的历史记录可保留对照。')
        st.markdown(f'[权重参考文献（表3—4）]({REFERENCE})')
    export = dict(result, case_fingerprint=fingerprint, case=case,
                  model_decision=review.get('decision'), model_reason=review.get('decision_reason'))
    st.download_button('下载五部分核验记录', json.dumps(export, ensure_ascii=False, indent=2),
                       file_name=f'verification-{fingerprint[:8]}.json', mime='application/json', key=prefix + 'download')
    return result


def material_score(case, entries=None):
    """Material presence score, not verification or predictive risk probability."""
    entries = entries or {}
    known = lambda value: bool(str(value or '').strip()) and not any(x in str(value) for x in ('不清楚','未提供','尚未确定','未知'))
    profile = str(case.get('seller_profile') or '')
    # Only explicit material availability is automated, not factual correctness.
    signals = {
        'identity': (known(case.get('model')), '已提供具体型号文字，尚未证明型号真实'),
        'condition': (bool(str(case.get('listing') or '').strip()), '已提供商品描述，尚未证明成色与功能'),
        'account': ('对应关系（用户填写）：已对照为同一账号' in profile, '用户已记录账号对应关系'),
        'reviews': (bool(re.search(r'(?:评价总数|来自买家的评价数|明确标注的卖出成交数)：\d', profile)), '已提供评价或成交数量，未向平台核实'),
        'order': (known(case.get('platform')), '已提供展示渠道，尚未核实订单对应关系'),
        'payment_terms': (known(case.get('payment_channel')), '已提供付款渠道，尚未核实付款条件'),
    }
    total=sum(d[2] for d in DIMENSIONS)
    rows=[]
    for _, label, raw, checks in DIMENSIONS:
        items=[]
        for key,title in checks:
            entry=entries.get(key,{})
            manual=entry.get('status') in {'checked','problem'} and bool(str(entry.get('note') or '').strip())
            present, explanation=signals.get(key,(False,'尚无可计入的核对记录'))
            items.append(dict(title=title,present=bool(present or manual),
                              reason=('用户保存的核对记录：'+str(entry['note'])) if manual else explanation if present else '资料不足／尚未记录核对依据'))
        fraction=sum(i['present'] for i in items)/len(items)
        rows.append(dict(label=label,weight=raw/total,fraction=fraction,items=items))
    return dict(score=100*sum(x['weight']*x['fraction'] for x in rows),dimensions=rows,
                meaning='资料覆盖评分，不是交易安全分。自动填入的文字也计作资料，未证明真实性。')


def show_verification_progress(case, review):
    import streamlit as st
    fingerprint=case_fingerprint(case)
    entries=st.session_state.get('verification_records',{}).get(fingerprint,{})
    # Render the form first so a save updates this run's score and report together.
    with st.expander('拼图评分明细与核对记录（点击展开）',expanded=False):
        result=_show_manual_verification(case,review)
    entries=st.session_state.get('verification_records',{}).get(fingerprint,{})
    score=material_score(case,entries)
    st.metric('拼图资料评分', f"{score['score']:.1f} / 100")
    st.caption('已提交的资料会自动计分；检测与售后等部分需保存核对依据。分数反映资料覆盖，不代表安全或真伪。')
    with st.expander('查看评分依据',expanded=False):
        st.caption('沿用文献参考权重；资料映射与维度内等权是本项目原型规则，未经实证校准。没有材料不猜测，发现问题仍可能有资料分。')
        for row in score['dimensions']:
            st.write(f"{row['label']}：{row['fraction']*100:.0f}分，权重{row['weight']:.2%}")
            for item in row['items']:
                st.caption(item['title']+'：'+item['reason'])
    result['material_score']=score
    return result
