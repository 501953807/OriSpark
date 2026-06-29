"""中国 POD 平台模板 — P2.5.13.

包含 印鸽、云打、定制链、闪印 四个中文 POD 平台的：
- 平台元数据 (名称、网址、模式、地区)
- 产品类别映射
- 设计规格要求
- API 端点描述 (如可用)
"""

# ---------------------------------------------------------------------------
# 中国 POD 平台元数据
# ---------------------------------------------------------------------------
CHINESE_POD_PLATFORMS = [
    {
        "id": "yingge",
        "name": "印鸽",
        "name_en": "YinGe",
        "mode": "pod",
        "region": "china",
        "url": "https://www.yinxiangmao.com",
        "description": "国内领先的POD按需打印平台，支持服装、手机壳、杯子等多品类",
        "supports_bulk_order": True,
        "api_available": True,
        "api_type": "rest",
        "shipping_regions": ["中国大陆", "港澳台"],
        "payment_methods": ["支付宝", "微信支付"],
        "integration_method": "api_rest",
        "key_features": [
            "一件代发", "API对接", "白牌包装", "48小时发货",
            "支持自有品牌", "品质检验",
        ],
    },
    {
        "id": "yunda",
        "name": "云打",
        "name_en": "YunDa",
        "mode": "pod",
        "region": "china",
        "url": "https://www.yundayin.com",
        "description": "专注服装品类的POD按需打印平台，T恤/卫衣品类齐全",
        "supports_bulk_order": True,
        "api_available": True,
        "api_type": "rest",
        "shipping_regions": ["中国大陆"],
        "payment_methods": ["支付宝", "微信支付"],
        "integration_method": "api_rest",
        "key_features": [
            "服装品类齐全", "面料选择丰富", "DTG数码直喷",
            "绣花工艺", "批量优惠",
        ],
    },
    {
        "id": "dingzhilian",
        "name": "定制链",
        "name_en": "DingZhiLian",
        "mode": "pod",
        "region": "china",
        "url": "https://www.dingzhilian.com",
        "description": "企业定制+POD混合平台，支持批量定制、企业礼品等场景",
        "supports_bulk_order": True,
        "api_available": False,
        "api_type": None,
        "shipping_regions": ["中国大陆"],
        "payment_methods": ["支付宝", "微信支付", "对公转账"],
        "integration_method": "manual",
        "key_features": [
            "企业礼品定制", "批量订单", "多种材质",
            "设计模板库", "售后服务完善",
        ],
    },
    {
        "id": "shanyin",
        "name": "闪印",
        "name_en": "ShanYin",
        "mode": "pod",
        "region": "china",
        "url": "https://www.shanyin.net",
        "description": "主打快速交付的POD平台，同城2小时极速达",
        "supports_bulk_order": False,
        "api_available": False,
        "api_type": None,
        "shipping_regions": ["中国大陆"],
        "payment_methods": ["支付宝", "微信支付"],
        "integration_method": "manual",
        "key_features": [
            "极速交付", "同城配送", "手机壳/杯子/照片书",
            "简单操作", "即时预览",
        ],
    },
]


# ---------------------------------------------------------------------------
# 中国 POD 平台 - 品类映射表
# ---------------------------------------------------------------------------
CHINESE_POD_CATEGORY_MAPPING = {
    "yingge": {
        "t_shirt": {"name_zh": "T恤", "available": True, "base_price_cny": 39},
        "hoodie": {"name_zh": "卫衣", "available": True, "base_price_cny": 89},
        "phone_case": {"name_zh": "手机壳", "available": True, "base_price_cny": 19},
        "mug": {"name_zh": "马克杯", "available": True, "base_price_cny": 25},
        "poster": {"name_zh": "海报", "available": True, "base_price_cny": 15},
        "canvas": {"name_zh": "帆布画", "available": True, "base_price_cny": 49},
        "pillow": {"name_zh": "抱枕", "available": True, "base_price_cny": 35},
        "tote_bag": {"name_zh": "帆布袋", "available": True, "base_price_cny": 29},
        "mouse_pad": {"name_zh": "鼠标垫", "available": True, "base_price_cny": 15},
        "puzzle": {"name_zh": "拼图", "available": True, "base_price_cny": 39},
    },
    "yunda": {
        "t_shirt": {"name_zh": "T恤", "available": True, "base_price_cny": 35},
        "hoodie": {"name_zh": "卫衣", "available": True, "base_price_cny": 79},
        "sweatshirt": {"name_zh": "运动衫", "available": True, "base_price_cny": 69},
        "polo": {"name_zh": "Polo衫", "available": True, "base_price_cny": 49},
        "tank_top": {"name_zh": "背心", "available": True, "base_price_cny": 29},
        "long_sleeve": {"name_zh": "长袖T恤", "available": True, "base_price_cny": 45},
        "kids_tee": {"name_zh": "儿童T恤", "available": True, "base_price_cny": 29},
    },
    "dingzhilian": {
        "t_shirt": {"name_zh": "T恤", "available": True, "base_price_cny": 45},
        "hoodie": {"name_zh": "卫衣", "available": True, "base_price_cny": 99},
        "mug": {"name_zh": "马克杯", "available": True, "base_price_cny": 28},
        "umbrella": {"name_zh": "雨伞", "available": True, "base_price_cny": 39},
        "power_bank": {"name_zh": "充电宝", "available": True, "base_price_cny": 69},
        "pen": {"name_zh": "签字笔", "available": True, "base_price_cny": 9},
        "notebook": {"name_zh": "笔记本", "available": True, "base_price_cny": 19},
        "calendar": {"name_zh": "日历", "available": True, "base_price_cny": 29},
        "keychain": {"name_zh": "钥匙扣", "available": True, "base_price_cny": 12},
        "gift_box": {"name_zh": "礼盒", "available": True, "base_price_cny": 59},
    },
    "shanyin": {
        "phone_case": {"name_zh": "手机壳", "available": True, "base_price_cny": 22},
        "mug": {"name_zh": "马克杯", "available": True, "base_price_cny": 28},
        "photo_book": {"name_zh": "照片书", "available": True, "base_price_cny": 49},
        "poster": {"name_zh": "海报", "available": True, "base_price_cny": 18},
        "postcard": {"name_zh": "明信片", "available": True, "base_price_cny": 8},
        "lomo_card": {"name_zh": "Lomo卡", "available": True, "base_price_cny": 5},
        "canvas": {"name_zh": "帆布画", "available": True, "base_price_cny": 55},
    },
}


# ---------------------------------------------------------------------------
# 中国 POD 平台 - 设计规格要求
# ---------------------------------------------------------------------------
CHINESE_POD_SPECS = {
    "yingge": {
        "default_dpi": 300,
        "accepted_formats": ["PNG", "JPG", "PSD", "AI"],
        "max_file_size_mb": 50,
        "color_mode": "sRGB",
        "require_transparency": True,
        "bleed_mm": 3,
    },
    "yunda": {
        "default_dpi": 200,
        "accepted_formats": ["PNG", "JPG", "PSD"],
        "max_file_size_mb": 30,
        "color_mode": "sRGB",
        "require_transparency": True,
        "bleed_mm": 0,
    },
    "dingzhilian": {
        "default_dpi": 300,
        "accepted_formats": ["PNG", "JPG", "AI", "CDR", "PDF"],
        "max_file_size_mb": 100,
        "color_mode": "CMYK",
        "require_transparency": False,
        "bleed_mm": 3,
    },
    "shanyin": {
        "default_dpi": 300,
        "accepted_formats": ["PNG", "JPG"],
        "max_file_size_mb": 20,
        "color_mode": "sRGB",
        "require_transparency": False,
        "bleed_mm": 0,
    },
}


def get_chinese_pod_platform(platform_id: str) -> dict | None:
    """获取中国 POD 平台元数据。"""
    for p in CHINESE_POD_PLATFORMS:
        if p["id"] == platform_id:
            return p
    return None


def get_chinese_pod_categories(platform_id: str) -> dict:
    """获取平台支持的品类。"""
    return CHINESE_POD_CATEGORY_MAPPING.get(platform_id, {})


def get_chinese_pod_specs(platform_id: str) -> dict:
    """获取平台设计规格要求。"""
    return CHINESE_POD_SPECS.get(platform_id, {})
