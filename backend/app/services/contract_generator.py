"""IP 授权合同自动生成服务."""

from datetime import datetime


def generate_contract_text(license_data: dict) -> str:
    """根据授权数据生成标准合同文本."""
    licensor = license_data.get("licensor_name", "甲方")
    licensee = license_data.get("licensee_name", "乙方")
    work_title = license_data.get("work_title", "作品")
    license_type = license_data.get("license_type", "非独占")
    territory = license_data.get("territory", "中国大陆")
    start_date = license_data.get("start_date", "未知")
    end_date = license_data.get("end_date", "未知")
    channels = license_data.get("channels", ["网络"])
    payment_type = license_data.get("payment_type", "一次性")
    amount = license_data.get("amount_yuan", 0)

    channels_str = "、".join(channels) if isinstance(channels, list) else channels

    contract = f"""IP 授权协议

甲方（授权方）：{licensor}
乙方（被授权方）：{licensee}

第一条 授权标的
甲方授权乙方使用作品《{work_title}》。

第二条 授权类型
本授权为【{license_type}】授权。

第三条 授权地域
本授权适用于【{territory}】地区。

第四条 授权期限
自 {start_date} 起至 {end_date} 止。

第五条 授权渠道
乙方可在以下渠道使用本作品：{channels_str}

第六条 授权费用
授权费用为人民币 {amount} 元整。
付费方式：{payment_type}。

第七条 其他约定
1. 乙方不得将授权超出本协议约定的范围使用。
2. 本协议未尽事宜，双方协商解决。

签署日期：{datetime.now().strftime('%Y年%m月%d日')}
"""
    return contract
