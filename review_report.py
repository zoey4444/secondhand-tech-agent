"""A single portable snapshot of the displayed analysis and user checklist."""
from copy import deepcopy
from review_record import APP_VERSION, INPUT_FIELDS, OUTPUT_FIELDS
from review_policy import source_label, STATUS_LABELS
from verification_progress import case_fingerprint, STATUSES

DECISIONS = {'allow': '当前材料未见明显异常，仍需实物核验',
             'wait': '暂缓付款，先补充或核对信息',
             'reject': '先处理停止交易原因，不应据此付款'}
LABELS = {'platform':'展示平台', 'payment_channel':'下单付款渠道', 'category':'产品类别',
          'model':'型号与配置', 'price':'当前标价', 'listing':'商品描述', 'chat':'初始沟通内容',
          'price_samples':'参考报价', 'price_source':'参考来源', 'seller_profile':'卖家主页材料'}


def build_report(case, review, progress, history=()):
    """Match history by input fingerprint; failed retries cannot replace success."""
    fingerprint = case_fingerprint(case)
    matched = next((r for r in reversed(history)
                    if not r.get('output', {}).get('error')
                    and case_fingerprint(r.get('input', {})) == fingerprint
                    and r.get('output', {}).get('decision') == review.get('decision')), {})
    snapshot = deepcopy(dict(schema_version=1, app_version=APP_VERSION,
                    case_fingerprint=fingerprint, analysis_run_id=matched.get('run_id'),
                    analysis_round=matched.get('round'),
                    input={k:case[k] for k in INPUT_FIELDS if k in case and k != 'previous_issues'},
                    output={k:review[k] for k in OUTPUT_FIELDS if k in review},
                    verification=progress))
    lines = ['二手数码购前核验报告', f'应用版本：{APP_VERSION}',
             f'关联分析记录：{snapshot["analysis_run_id"] or "当前会话结果，未匹配到历史编号"}',
             '', '一、本轮判断', DECISIONS.get(review.get('decision'), '本轮判断不可用'),
             str(review.get('decision_reason') or '未生成单独说明。')]
    if review.get('error') or review.get('analysis_notice'):
        lines.append('分析限制：' + str(review.get('error') or review['analysis_notice']))
    if progress.get('problems'):
        lines.append('用户核对记录中另有问题或未解决矛盾；需补充材料重新分析，不能因完成度高而付款。')
    lines += ['', '二、提交的商品与卖家材料']
    for key,label in LABELS.items():
        lines.append(f'{label}：{case.get(key) or "未提供"}')
    for index,reply in enumerate(case.get('seller_replies') or [],1):
        lines.append(f'第{index}次补充材料：{reply}')
    lines += ['', '三、待核实问题与引用']
    issues=review.get('issues') or []
    if not issues:
        lines.append('当前未列出具体问题；不代表实物已核实或交易安全。')
    for index,issue in enumerate(issues,1):
        priority='优先核实' if issue.get('severity')=='high' else '待核实'
        lines.append(f"{index}. [{priority}] {issue.get('summary','')}")
        lines.append('状态：' + STATUS_LABELS.get(issue.get('status'), '待核实'))
        for e in issue.get('evidence',[]):
            lines.append(f"引用{source_label(e.get('source',''))}：{e.get('quote','')}")
        if issue.get('question'):lines.append('建议动作：'+issue['question'])
    lines += ['', '四、核验完成度（用户记录，不是安全分）',
              f"完成度：{progress.get('score',0):.1f}%",
              '权重来自外部文献的探索性适配；维度内检查项等权属于项目设计，未经过本项目交易结果验证。']
    for row in progress.get('dimensions',[]):
        lines.append(f"{row['label']}：{row['fraction']:.0%}，参考权重{row['weight']:.2%}")
        for item in row['items']:
            lines.append(f"- {item['title']}：{STATUSES.get(item['status'],'待核验')}；记录：{item['note'] or '未填写'}")
    if progress.get('reference'):lines.append('权重参考：'+progress['reference'])
    changes=review.get('material_changes')
    lines += ['', '五、本轮补充前后变化']
    if changes:
        lines.append(f"判断：{changes.get('before','未知')} → {changes.get('after','未知')}")
        lines.append('本轮新增材料：'+changes.get('new_material',''))
        lines += [f"{item['label']}：{item['summary']}" for item in changes.get('changes',[])]
    else:lines.append('本轮没有可对照的补充材料变化记录。')
    lines += ['', '六、下一步行动']
    if review.get('decision')=='reject':lines.append('先处理停止交易原因，不用其他维度高分抵消。')
    questions=review.get('questions') or []
    if questions:lines += [f'{i}. {q}' for i,q in enumerate(questions[:3],1)]
    else:lines += [f"- {item['title']}" for item in progress.get('next_checks',[])]
    lines += ['', '七、填写信息的作用']
    for row in review.get('input_feedback') or []:
        lines.append(f"{row['label']}：{row.get('role','')} 本轮反馈：{row.get('feedback','未生成单独反馈')}")
    lines += ['', '判断边界：只分析用户提交材料，不鉴定真伪，不保证交易安全。评价数不等于成交数；'
              '历史购买订单的售后不自动适用于本次二手交易；卖家陈述、问题消失或核验完成度高均不等于风险已解除。']
    return snapshot, '\n'.join(lines)


def show_report_download(case, review, progress, history):
    import json
    import streamlit as st
    snapshot, text = build_report(case,review,progress,history)
    name=snapshot['case_fingerprint'][:8]
    with st.expander('保存完整核验报告'):
        st.caption('汇总当前分析、引用、卖家材料、已保存核验记录及补充前后变化。未保存的表单草稿不会包含在报告内。')
        st.download_button('下载完整报告（文本）',text,file_name=f'review-report-{name}.txt',
                           mime='text/plain',key='complete_report_text')
        st.download_button('下载完整报告（结构化记录）',json.dumps(snapshot,ensure_ascii=False,indent=2),
                           file_name=f'review-report-{name}.json',mime='application/json',key='complete_report_json')
