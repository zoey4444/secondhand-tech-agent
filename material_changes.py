"""Traceable round comparisons. Disappearance is never treated as resolution."""

def compare_rounds(previous, current, new_material):
    old = {i['id']: i for i in previous.get('issues', []) if i.get('id')}
    new = {i['id']: i for i in current.get('issues', []) if i.get('id')}
    changes = []
    matched_old = set()
    def normalized(item):
        return ''.join(str(item.get('summary', '')).split())
    for key, item in new.items():
        previous_key = key if key in old else next((old_key for old_key, value in old.items()
                         if normalized(item) and normalized(value) == normalized(item)), None)
        if previous_key is not None:
            matched_old.add(previous_key)
        status = item.get('status', '')
        label = ('本轮新增疑问' if previous_key is None else
                 '有回复但尚未核实' if status == 'answered_claim_only' else
                 '发现说法矛盾' if status == 'contradicted' else '仍待核实')
        changes.append(dict(id=key, label=label, summary=item.get('summary', ''),
                            evidence=item.get('evidence', [])))
    for key, item in old.items():
        if key not in matched_old:
            changes.append(dict(id=key, label='本轮未再次列出，不代表已解决',
                                summary=item.get('summary', ''), evidence=item.get('evidence', [])))
    return dict(new_material=new_material, before=previous.get('decision', 'wait'),
                after=current.get('decision', 'wait'), changes=changes,
                boundary='新增材料及卖家解释不自动视为独立证据；未自动认定任何疑问已解决。')


def show_material_changes(change):
    import streamlit as st
    labels = {'allow':'当前材料未见明显异常', 'wait':'仍需补充核对', 'reject':'先处理停止交易原因'}
    added = sum(item['label'] == '本轮新增疑问' for item in change.get('changes', []))
    total = len(change.get('changes', []))
    st.caption(f'本轮变化：新增疑问{added}项；其余待核对记录{total-added}项。详细材料按需展开。')
    with st.expander('本轮补充了什么，判断有什么变化？', expanded=False):
        st.write(f"上轮：{labels.get(change['before'], change['before'])} → 本轮：{labels.get(change['after'], change['after'])}")
        st.caption(change['boundary'])
        st.text('本轮新增材料：\n' + change['new_material'])
        for item in change['changes']:
            st.write(f"{item['label']}：{item['summary']}")
            for evidence in item.get('evidence', []):
                from review_policy import source_label
                st.text(f"引用{source_label(evidence.get('source', ''))}：{evidence.get('quote', '')}")
        if not change['changes']:
            st.write('本轮未生成具体疑问记录，不代表已完成实物核验。')
