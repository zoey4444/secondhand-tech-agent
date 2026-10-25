"""Local platform prompts and device checklists; no live platform lookup."""
import re

PLATFORMS = ["闲鱼", "转转", "小红书", "淘宝", "京东", "微信/社交平台", "线下交易", "其他平台"]
CATEGORIES = ["手机", "平板", "笔记本电脑", "台式电脑/配件", "相机（单反/微单/CCD）", "耳机", "智能手表/手环", "游戏机", "其他数码产品"]
MODEL_OPTIONS = {
    "手机": ["Apple iPhone 13", "Apple iPhone 14", "Apple iPhone 15", "Apple iPhone 16", "Samsung Galaxy S 系列", "小米数字系列", "其他型号（手动填写）"],
    "平板": ["Apple iPad 第9代", "Apple iPad 第10代", "Apple iPad Air 第5代", "Apple iPad mini 第6代", "Samsung Galaxy Tab S9", "小米平板 6", "其他型号（手动填写）"],
    "笔记本电脑": ["Apple MacBook Air M1（2020）", "Apple MacBook Air M2（2022）", "Apple MacBook Pro 14英寸 M1 Pro（2021）", "Lenovo ThinkPad X1 Carbon（需填写代际）", "Dell XPS 13（需填写具体型号）", "其他型号（手动填写）"],
    "台式电脑/配件": ["整机（需填写配置）", "NVIDIA GeForce RTX 3060", "NVIDIA GeForce RTX 4060", "AMD Ryzen 5 5600", "Intel Core i5-12400F", "其他型号（手动填写）"],
    "相机（单反/微单/CCD）": ["Canon EOS R50", "Sony α6400", "Nikon Z50", "Fujifilm X-T30 II", "Canon IXUS 95 IS（CCD）", "Sony Cyber-shot DSC-W830（CCD）", "其他型号（手动填写）"],
    "耳机": ["Apple AirPods 4 标准版", "Apple AirPods 4 主动降噪版", "Apple AirPods Pro 第2代", "Sony WH-1000XM4", "Sony WH-1000XM5", "Bose QuietComfort Ultra Headphones", "其他型号（手动填写）"],
    "智能手表/手环": ["Apple Watch Series 9", "Apple Watch SE 第2代", "Huawei Watch GT 4", "小米手环 8", "其他型号（手动填写）"],
    "游戏机": ["Nintendo Switch 标准版", "Nintendo Switch OLED", "Nintendo Switch Lite", "PlayStation 5 光驱版", "PlayStation 5 数字版", "Xbox Series X", "Xbox Series S", "其他型号（手动填写）"],
    "其他数码产品": ["其他型号（手动填写）"],
}

PLATFORM_GUIDANCE = {
    "闲鱼": "核对商品页面、聊天记录和订单是否对应；优先在平台内沟通、付款并留存记录，具体保障以当前平台规则为准。",
    "转转": "确认是否使用平台验机或售后服务，并核实服务范围、费用和适用条件；保留平台内沟通与订单记录。",
    "小红书": "区分内容展示平台和实际成交平台；确认最终在哪个平台下单、付款及售后，分别核对对应规则。",
    "淘宝": "核对商品链接、店铺主体、订单承诺与售后条件是否一致，具体保障以订单页面规则为准。",
    "京东": "核对商品链接、店铺主体、订单承诺与售后条件是否一致，具体保障以订单页面规则为准。",
    "微信/社交平台": "平台内交易保障可能有限；书面确认商品状态、付款与退货约定，谨慎处理私下转账。",
    "线下交易": "选择安全的公共场所，付款前当面检查主要功能、配件和序列信息；不要只凭口头承诺。",
    "其他平台": "先确认实际成交渠道及其付款、退货和争议处理规则，并保留商品页面、沟通和订单凭证。",
}

CATEGORY_CHECKLIST = {
    "手机": "核对准确型号/存储/版本、序列号或 IMEI（勿公开完整号码）、账号锁与网络限制；测试屏幕、摄像头、扬声器、麦克风、按键、充电、电池健康及维修记录。",
    "平板": "核对型号/存储/网络版本、账号锁、屏幕触控与边缘、摄像头、扬声器、充电、电池和配件；检查是否有维修或弯曲。",
    "笔记本电脑": "核对完整型号、CPU/内存/硬盘配置和序列信息；测试屏幕、键盘、接口、摄像头、无线网络、电池循环/健康、散热与系统锁。",
    "台式电脑/配件": "逐项核对 CPU、主板、显卡、内存、硬盘、电源等准确型号；要求可验证的运行测试，检查接口、温度、噪声和保修凭证。",
    "相机（单反/微单/CCD）": "核对机身与镜头具体型号、快门/闪光/对焦/变焦/存储卡槽；检查镜头霉斑、传感器污点、屏幕、接口、电池及配件。",
    "耳机": "核对具体代际/型号；分体耳机核对左右耳和充电盒，头戴耳机核对头梁、耳罩和线材；只测试该型号具备的配对、降噪/通透、麦克风、触控/按键、充电功能，并核实维修更换和保修承诺。",
    "智能手表/手环": "核对具体型号/尺寸/蜂窝版本与账号解绑；检查屏幕、传感器、按键、充电和电池，询问进水及维修历史；不要用浸水测试验证二手设备的防水能力。",
    "游戏机": "核对型号/版本/账号解绑与区域限制；测试读盘或卡槽、手柄摇杆、接口、散热、网络与存储，并确认游戏/账号是否可转移。",
    "其他数码产品": "先明确准确型号、关键配置、配件和可现场验证的核心功能，再按该品类查官方说明与售后条件。",
}


def checklist_for_case(case: dict) -> str:
    """Use a component checklist when the selected product is a graphics card."""
    category = str(case.get("category", ""))
    model = str(case.get("model", ""))
    if (category == "台式电脑/配件"
            and not re.search(r"整机|主机|台式机|台式电脑", model)
            and re.search(r"geforce|rtx|gtx|radeon|显卡", model, re.IGNORECASE)):
        return (
            "核对显卡品牌、完整型号、显存与接口；在实机核对识别信息并运行游戏或测试程序，"
            "观察花屏、黑屏、温度、风扇和异常噪声；询问拆修、更换零件和使用记录，核对凭证及配件。"
            "螺丝、防拆贴照片仅供参考，不能证明从未拆修；一次点亮或单段视频不能保证长期稳定，收货后需复查。"
        )
    return CATEGORY_CHECKLIST.get(category, CATEGORY_CHECKLIST["其他数码产品"])


def transaction_guidance(case: dict) -> str:
    channel = case.get("payment_channel")
    return PLATFORM_GUIDANCE.get(channel, {
        "当面付款": PLATFORM_GUIDANCE["线下交易"],
        "个人转账": "实际付款选为个人转账；核对是否能改走有订单记录的渠道，不将展示平台的保障套用到个人收款。"
    }.get(channel, "先确认实际下单付款方式；正文已有明确说法时提取该陈述，不根据展示平台推断交易保障。"))


