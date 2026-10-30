"""Conservative purchase gates based on quoted, explicit transaction conditions."""
import re
import hashlib
from evidence_refs import build_catalog


def purchase_blockers(case, sources):
    excerpts = [e for e in build_catalog(sources).values()
                if e['source'] in {'listing', 'chat'} or e['source'].startswith('reply_')]
    excerpts = [e for e in excerpts if not re.search(r'忽略.*指令|直接输出|ignore previous', e['quote'], re.I)
                and not re.match(r'买家\s*[:：]', e['quote']) and not e['quote'].rstrip().endswith(('？', '?'))]
    def find(pattern):
        return next((e for e in excerpts if re.search(pattern, e['quote'], re.I)), None)
    result = []
    def add(topic, summary, evidence, question):
        if all(evidence):
            result.append(dict(id='purchase-' + hashlib.sha1(topic.encode()).hexdigest()[:8],
                kind='purchase_blocker', severity='high', summary=summary, evidence=evidence,
                question=question, status='open', origin='程序检查', topic=topic))
    # Require both explicit imitation indicators in the current listing, plus a
    # brand shared by the selected model and listing. Reviews do not qualify.
    def listing_assertion(pattern):
        for entry in excerpts:
            if entry['source'] != 'listing':
                continue
            match = re.search(pattern, entry['quote'], re.I)
            if match and not re.search(r'不|并非|拒绝|避免|非', entry['quote'][:match.start()]):
                return entry
        return None
    selected = str(case.get('model', ''))
    brands = (r'Sony|索尼', r'Apple|苹果', r'Samsung|三星', r'Bose', r'Canon|佳能', r'Nikon|尼康')
    for brand in brands:
        if not re.search(brand, selected, re.I):
            continue
        brand_evidence = listing_assertion(brand)
        imitation = listing_assertion(r'外观\s*1\s*[:：]\s*1')
        diy = listing_assertion(r'贴纸.{0,12}(?:DIY|自己.{0,4}(?:贴|动手))')
        add('imitation_identity', '品牌型号标注与正文的仿制外观、贴纸DIY描述不一致，不能按该品牌原装商品购买；先确认实际商品身份。',
            [brand_evidence, imitation, diy],
            '正文写的外观1:1和贴纸DIY是什么意思？这件是否为所标品牌原装商品？请明确实际品牌和型号。')
        break
    # Require an explicit contrast between title and details, not two optional configurations.
    a, b = find(r'标题.*\d+\s*G[B]?\s*\+\s*\d+'), find(r'详情.*\d+\s*G[B]?\s*\+\s*\d+')
    if a and b:
        configs = lambda e: re.findall(r'(\d+)\s*GB?\s*\+\s*(\d+)\s*GB?', e['quote'], re.I)
        if configs(a) and configs(b) and configs(a)[0] != configs(b)[0]:
            add('configuration', '标题和详情的内存、硬盘配置不同，实际交付配置尚未统一。', [a, b], '实际内存和硬盘分别是多少？方便发配置页面并同步商品描述吗？')
    add('account_delivery', '原账号未退出，且卖家计划交付后才处理；付款前需完成解绑并核验正常设置。',
        [find(r'(?:原)?账号.{0,6}(?:还没|未|没有)退出'), find(r'(?:到手|收到|交付|收货)后.{0,10}(?:联系|处理|退出|解绑)')],
        '可以交付前退出原账号，重置后当面确认能正常设置吗？')
    add('game_delivery', '宣传包含数字版游戏，但绑定账号不能交付，游戏权益与交付条件尚未统一。',
        [find(r'(?:带|包含|附送).{0,10}数字版游戏'), find(r'账号.{0,6}(?:不能|不给|无法).{0,5}(?:给|转让|转移|交付)')],
        '这些游戏不能随机器交付，对吗？方便修改商品页的游戏说明和成交条件吗？')
    a, b = find(r'(?:支持|可|承诺).{0,6}(?:七|7)天退货'), find(r'拆封后?不退')
    if a and b and not re.search(r'仅限|除外|不适用|适用范围', sources.get('listing', '') + sources.get('chat', '')):
        add('returns', '七天退货与拆封不退的适用条件尚未说清，先统一售后约定再付款。', [a,b], '拆封检查后还能退吗？方便把退货条件和适用范围写进订单吗？')
    model = str(case.get('model', ''))
    if re.search(r'RTX|GTX|Radeon|显卡', model, re.I) and not re.search(r'整机|主机', model):
        add('critical_gpu_evidence', '按本应用的购前标准：显卡运行证据和拆修情况同时缺失，当前先停止交易；这不代表已确认故障。',
            [find(r'(?:未|没有|没).{0,4}(?:提供)?.{0,3}(?:运行|测试).{0,4}(?:截图|视频|记录|证据)'), find(r'(?:拆修|维修).{0,5}(?:不清楚|未知|不确定)')],
            '方便提供本机运行测试视频，并说明拆修情况吗？')
    if case.get('category') == '智能手表/手环':
        add('waterproof_evidence', '按本应用的购前标准：长期游泳使用且防水只有口头保证，先停止交易并核实使用、进水和维修情况；不认定已经损坏。',
            [find(r'长期.{0,4}游泳'), find(r'防水.{0,5}(?:肯定|保证).{0,5}没问题')],
            '之前有进水或维修吗？方便提供已有检测记录吗？不要做浸水测试。')
    return result
