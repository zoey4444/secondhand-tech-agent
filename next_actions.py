"""Prioritize actionable risks before literature-weighted coverage gaps."""
from review_policy import unique_questions

def next_actions(review, progress):
    issues=[i for i in review.get('issues',[]) if i.get('kind')!='injection']
    blockers={'price_conflict','price_revision','model_conflict','purchase_blocker'}
    def rank(i):
        stop=i.get('kind') in blockers or (i.get('kind')=='off_platform' and i.get('severity')=='high')
        return (not stop,{'high':0,'medium':1,'low':2}.get(i.get('severity'),2))
    actions=[];seen=set()
    def add(text,reason):
        key=''.join(str(text).split())
        if key and key not in seen:
            seen.add(key);actions.append({'action':str(text),'reason':reason})
    for issue in sorted(issues,key=rank):
        add(issue.get('question') or issue.get('summary',''),'对应本轮疑问：'+issue.get('summary',''))
    for problem in progress.get('problems',[]):
        add('补充核对材料：'+problem['title'],'用户记录发现问题或矛盾：'+(problem.get('note') or '需补充依据'))
    # Do not displace unresolved issues with a higher completeness weight.
    for q in unique_questions(review.get('questions',[])): add(q,'本轮分析提出的补充问题')
    for item in progress.get('next_checks',[]): add(item['title'],'仍未完成的核验项，按初始参考权重排序')
    return actions[:3]

def show_next_actions(review,progress):
    import streamlit as st
    items=next_actions(review,progress)
    with st.expander(f'优先处理：共{len(items)}项（查看动作与原因）'):
        if review.get('decision')=='reject':st.warning('先处理停止交易原因；核验完成度和好评率不能抵消。')
        for index,item in enumerate(items,1):
            st.write(f"{index}. {item['action']}")
            st.caption(item['reason'])
        if not items:st.caption('当前没有单独生成后续动作，仍需结合实物检查。')
