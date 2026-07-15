"""IP 登记指引 API 路由 — 对应: docs/modules-v3/03-ip-registration.md
Phase 0.2: 合规改造(多推荐+置信度+免责声明+律师审核步骤)
端点: 24 (ipr)"""
import logging


from datetime import date, datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.ipr import (
    IPRegistration, TrademarkClass, CopyrightRegistration,
    TrademarkRegistration, NiceClassification, ApplicationTemplate,
)
from app.models.work import Work, WorkTag
from app.models.notary import NotaryRecord
from app.schemas.common import ApiResponse
from app.deps import require_auth
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter()


class CreateIPRegistrationPayload(BaseModel):
    work_id: Optional[str] = None
    ip_type: str = "copyright"
    jurisdiction: str = "cn"
    application_no: Optional[str] = None
    registration_no: Optional[str] = None
    filing_date: Optional[str] = None
    registration_date: Optional[str] = None
    expiration_date: Optional[str] = None
    next_action_date: Optional[str] = None
    next_action_type: Optional[str] = None
    status: str = "draft"
    category_info: Optional[dict] = None
    official_fee: float = 0
    total_cost: float = 0
    agent_name: Optional[str] = None
    agent_fee: float = 0
    official_url: Optional[str] = None
    notes: Optional[str] = None


class UpdateIPRegistrationPayload(BaseModel):
    work_id: Optional[str] = None
    ip_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    application_no: Optional[str] = None
    registration_no: Optional[str] = None
    filing_date: Optional[str] = None
    registration_date: Optional[str] = None
    expiration_date: Optional[str] = None
    next_action_date: Optional[str] = None
    next_action_type: Optional[str] = None
    status: Optional[str] = None
    category_info: Optional[dict] = None
    official_fee: Optional[float] = None
    total_cost: Optional[float] = None
    agent_name: Optional[str] = None
    agent_fee: Optional[float] = None
    official_url: Optional[str] = None
    notes: Optional[str] = None
    reminder_date: Optional[str] = None


class RecommendClassesPayload(BaseModel):
    tags: list[str] = []
    description: str = ""
    creator_type: Optional[str] = None


class PrefillApplicationPayload(BaseModel):
    work_id: str
    ip_type: str = "copyright"
    jurisdiction: str = "cn"


class ValidateApplicationPayload(BaseModel):
    ip_type: str = "copyright"
    fields: dict = {}


class GenerateApplicationPayload(BaseModel):
    ip_type: str = "copyright"
    jurisdiction: str = "cn"
    fields: dict = {}


class ExportApplicationPayload(BaseModel):
    ip_type: str = "copyright"
    jurisdiction: str = "cn"
    lawyer_consulted: str


class FeeCalculatorPayload(BaseModel):
    ip_type: str = "trademark"
    jurisdictions: list[str] = []
    classes: list[int] = []
    design_count: int = 1
    wipo_designations: list[str] = []
    is_color: bool = False


def _get_ip_types(db: Session) -> list[str]:
    """Get IP types from dictStore (P1.7.13), fallback to hardcoded."""
    try:
        from app.routers.system import get_dict_values
        dict_types = get_dict_values("ip_types", db)
        if dict_types:
            return dict_types
    except Exception as e:
        logging.getLogger(__name__).exception("Error in _get_ip_types: %s", str(e))
    return ["copyright", "trademark", "design_patent", "utility_patent", "invention_patent"]


# ─── 预定义数据 ───────────────────────────────────────────────

# 推荐类别 (文化创意) — 通用映射
COMMON_CATEGORIES = {
    "16": "办公用品、文具、印刷品、美术用品",
    "25": "服装、鞋、帽",
    "28": "游戏器具、玩具、体育用品",
    "35": "广告、商业管理、替他人推销",
    "41": "教育、培训、娱乐、出版",
    "42": "科技服务、设计、软件开发",
}

# 文创常用尼斯类别完整数据 — P1.4.4 + P2.4.7 种子数据 (全45类)
NICE_CLASSES_SEED = [
    {
        "class_no": 1, "class_name_zh": "化学原料",
        "class_name_en": "Chemicals",
        "is_creative_relevant": False,
        "goods_services": [
            "工业用化学品", "摄影用化学品", "未加工合成树脂", "工业用粘合剂",
            "肥料", "灭火制剂", "淬火和焊接用制剂", "食品防腐用化学品",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 2, "class_name_zh": "颜料油漆",
        "class_name_en": "Paints and coatings",
        "is_creative_relevant": True,
        "goods_services": [
            "颜料", "油漆", "清漆", "防锈制剂", "着色剂",
            "印刷油墨", "绘画用丙烯颜料", "水彩颜料", "油画颜料",
        ],
        "common_for_creators": ["绘画颜料", "印刷油墨", "艺术涂料", "喷漆"],
    },
    {
        "class_no": 3, "class_name_zh": "日化用品",
        "class_name_en": "Cosmetics and cleaning",
        "is_creative_relevant": False,
        "goods_services": [
            "化妆品", "香水", "牙膏", "洗发水", "肥皂",
            "洗衣剂", "清洁制剂", "精油",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 4, "class_name_zh": "燃料油脂",
        "class_name_en": "Fuels and lubricants",
        "is_creative_relevant": False,
        "goods_services": [
            "工业用油", "润滑油", "燃料", "蜡烛", "除尘制剂",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 5, "class_name_zh": "医药制品",
        "class_name_en": "Pharmaceuticals",
        "is_creative_relevant": False,
        "goods_services": [
            "药品", "医用营养品", "卫生制剂", "婴儿食品", "消毒剂",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 6, "class_name_zh": "金属材料",
        "class_name_en": "Metal products",
        "is_creative_relevant": True,
        "goods_services": [
            "普通金属及其合金", "金属建筑材料", "金属艺术品",
            "五金器具", "金属钥匙链", "金属纪念章",
        ],
        "common_for_creators": ["金属艺术品", "金属钥匙扣", "徽章", "金属文创"],
    },
    {
        "class_no": 7, "class_name_zh": "机械设备",
        "class_name_en": "Machinery",
        "is_creative_relevant": False,
        "goods_services": [
            "机器和机床", "马达和引擎", "非手动农业器具", "3D打印机",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 8, "class_name_zh": "手工器械",
        "class_name_en": "Hand tools",
        "is_creative_relevant": False,
        "goods_services": [
            "手工用具和器械", "刀叉餐具", "剃刀", "电动理发器",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 9, "class_name_zh": "科学仪器、软件",
        "class_name_en": "Scientific and electronic apparatus",
        "is_creative_relevant": True,
        "goods_services": [
            "计算机软件(已录制)", "可下载的应用程序", "动画片(已录制)",
            "电子出版物(可下载)", "移动电源", "耳机", "手机壳",
            "照相机", "可下载的数字音乐", "可下载的表情符号",
            "可下载的图像文件", "可下载的电子游戏程序",
        ],
        "common_for_creators": ["软件APP", "数字内容", "数字艺术", "虚拟形象", "NFT数字藏品", "表情包"],
    },
    {
        "class_no": 10, "class_name_zh": "医疗器械",
        "class_name_en": "Medical devices",
        "is_creative_relevant": False,
        "goods_services": [
            "医疗器械和仪器", "矫形用品", "缝合材料", "助听器",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 11, "class_name_zh": "照明、空调",
        "class_name_en": "Environmental control",
        "is_creative_relevant": False,
        "goods_services": [
            "照明设备", "烹饪用炉", "冰箱", "空调", "加热设备",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 12, "class_name_zh": "运输工具",
        "class_name_en": "Vehicles",
        "is_creative_relevant": False,
        "goods_services": [
            "汽车", "自行车", "婴儿车", "轮椅", "机车",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 13, "class_name_zh": "军火烟火",
        "class_name_en": "Firearms and fireworks",
        "is_creative_relevant": False,
        "goods_services": [
            "火器", "弹药", "炸药", "烟火爆竹",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 14, "class_name_zh": "珠宝钟表",
        "class_name_en": "Jewelry and watches",
        "is_creative_relevant": True,
        "goods_services": [
            "珠宝首饰", "贵金属及其合金", "钟表", "项链",
            "手镯", "戒指", "耳环", "胸针", "钥匙扣(贵金属制)",
        ],
        "common_for_creators": ["IP联名首饰", "设计师饰品", "文创珠宝", "角色项链"],
    },
    {
        "class_no": 15, "class_name_zh": "乐器",
        "class_name_en": "Musical instruments",
        "is_creative_relevant": True,
        "goods_services": [
            "乐器", "吉他", "钢琴", "电子乐器", "音乐合成器",
        ],
        "common_for_creators": ["音乐IP联名乐器", "定制乐器外观"],
    },
    {
        "class_no": 16, "class_name_zh": "印刷品、文具用品",
        "class_name_en": "Paper and printed goods",
        "is_creative_relevant": True,
        "goods_services": [
            "贴纸、贴画", "海报、招贴画", "印刷出版物", "连环画、漫画书",
            "绘画材料", "美术用品", "文具", "笔记本", "明信片", "书签",
            "包装用纸", "印刷的艺术复制品", "照片、印刷品",
        ],
        "common_for_creators": ["插画贴纸", "海报设计", "漫画出版", "艺术印刷品", "文创文具"],
    },
    {
        "class_no": 17, "class_name_zh": "橡胶制品",
        "class_name_en": "Rubber products",
        "is_creative_relevant": False,
        "goods_services": [
            "绝缘材料", "橡胶", "塑料制品(半加工)", "密封垫",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 18, "class_name_zh": "皮革皮具",
        "class_name_en": "Leather goods",
        "is_creative_relevant": True,
        "goods_services": [
            "皮包", "背包", "手提袋", "钱包", "雨伞", "行李箱",
            "动物皮", "人造革包",
        ],
        "common_for_creators": ["IP联名包袋", "文创帆布袋", "角色背包", "周边手提袋"],
    },
    {
        "class_no": 19, "class_name_zh": "非金属建材",
        "class_name_en": "Building materials (non-metallic)",
        "is_creative_relevant": False,
        "goods_services": [
            "非金属建筑材料", "石头、混凝土、大理石艺术品", "瓷砖",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 20, "class_name_zh": "家具",
        "class_name_en": "Furniture",
        "is_creative_relevant": True,
        "goods_services": [
            "家具", "镜子", "画框", "枕头", "展示架",
            "木制艺术品", "塑料艺术品", "非金属钥匙链",
        ],
        "common_for_creators": ["文创家具", "IP主题家具", "装饰画框", "展示架"],
    },
    {
        "class_no": 21, "class_name_zh": "厨房洁具",
        "class_name_en": "Kitchen utensils",
        "is_creative_relevant": True,
        "goods_services": [
            "家用或厨房用容器", "杯具", "餐具(刀叉除外)", "玻璃器皿",
            "瓷器", "陶器", "保温杯", "水瓶",
        ],
        "common_for_creators": ["联名杯具", "文创餐具", "IP主题水杯", "角色马克杯"],
    },
    {
        "class_no": 22, "class_name_zh": "绳网帐篷",
        "class_name_en": "Ropes and tents",
        "is_creative_relevant": False,
        "goods_services": [
            "绳索", "帐篷", "帆布", "编织袋",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 23, "class_name_zh": "纺织纱线",
        "class_name_en": "Yarns and threads",
        "is_creative_relevant": False,
        "goods_services": [
            "纺织用纱和线",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 24, "class_name_zh": "布料床单",
        "class_name_en": "Textiles and fabrics",
        "is_creative_relevant": True,
        "goods_services": [
            "织物", "床单", "桌布", "毛巾", "纺织品制墙纸",
            "纺织品挂毯", "手帕",
        ],
        "common_for_creators": ["联名床品", "文创毛巾", "IP桌布", "艺术墙布"],
    },
    {
        "class_no": 25, "class_name_zh": "服装、鞋、帽",
        "class_name_en": "Clothing, footwear, headgear",
        "is_creative_relevant": True,
        "goods_services": [
            "服装", "鞋", "帽子", "T恤衫", "卫衣", "围巾",
            "手套", "腰带", "袜子", "婴儿服装", "内衣",
        ],
        "common_for_creators": ["IP联名T恤", "角色印花卫衣", "原创图案服饰", "潮牌设计"],
    },
    {
        "class_no": 26, "class_name_zh": "花边拉链",
        "class_name_en": "Lace and fastenings",
        "is_creative_relevant": True,
        "goods_services": [
            "花边饰品", "刺绣品", "假发", "纽扣", "拉链",
        ],
        "common_for_creators": ["刺绣文创", "徽章", "布贴"],
    },
    {
        "class_no": 27, "class_name_zh": "地毯地垫",
        "class_name_en": "Carpets and mats",
        "is_creative_relevant": True,
        "goods_services": [
            "地毯", "地垫", "席", "墙纸(非纺织品)",
        ],
        "common_for_creators": ["创意地垫", "艺术地毯", "壁纸图案"],
    },
    {
        "class_no": 28, "class_name_zh": "游戏器具、玩具",
        "class_name_en": "Games and playthings",
        "is_creative_relevant": True,
        "goods_services": [
            "玩具", "游戏器具", "玩偶、公仔", "手办模型", "拼图玩具",
            "积木", "纸牌", "棋类", "电子游戏机", "玩具娃娃",
        ],
        "common_for_creators": ["角色手办", "盲盒玩具", "桌游设计", "IP玩偶", "潮玩"],
    },
    {
        "class_no": 29, "class_name_zh": "食品肉蛋",
        "class_name_en": "Meat and food products",
        "is_creative_relevant": False,
        "goods_services": [
            "肉", "鱼", "食用油", "牛奶制品", "果冻",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 30, "class_name_zh": "咖啡、糕点",
        "class_name_en": "Coffee and baked goods",
        "is_creative_relevant": True,
        "goods_services": [
            "咖啡", "茶", "糖", "蜂蜜", "糕点", "面包",
            "饼干", "巧克力", "冰淇淋", "调味品",
        ],
        "common_for_creators": ["联名零食", "IP主题糕点", "文创食品礼盒", "联名茶饮"],
    },
    {
        "class_no": 31, "class_name_zh": "农产品",
        "class_name_en": "Agricultural products",
        "is_creative_relevant": False,
        "goods_services": [
            "农产品", "新鲜水果", "新鲜蔬菜", "花卉", "饲料",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 32, "class_name_zh": "啤酒饮料",
        "class_name_en": "Beverages",
        "is_creative_relevant": True,
        "goods_services": [
            "啤酒", "矿泉水", "汽水", "果汁", "不含酒精的饮料",
        ],
        "common_for_creators": ["联名饮料", "IP主题饮品", "文创矿泉水"],
    },
    {
        "class_no": 33, "class_name_zh": "酒类",
        "class_name_en": "Alcoholic beverages",
        "is_creative_relevant": False,
        "goods_services": [
            "含酒精的饮料(啤酒除外)", "白酒", "葡萄酒", "威士忌",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 34, "class_name_zh": "烟草烟具",
        "class_name_en": "Tobacco products",
        "is_creative_relevant": False,
        "goods_services": [
            "烟草", "香烟", "烟具", "火柴", "电子烟",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 35, "class_name_zh": "广告、商业管理",
        "class_name_en": "Advertising and business",
        "is_creative_relevant": True,
        "goods_services": [
            "广告", "替他人推销", "商业管理咨询", "市场营销",
            "在线零售服务", "为商品和服务的买卖提供在线市场",
            "特许经营的商业管理", "商业中介服务",
        ],
        "common_for_creators": ["IP授权管理", "在线文创商店", "品牌运营", "衍生品销售"],
    },
    {
        "class_no": 36, "class_name_zh": "金融保险",
        "class_name_en": "Financial services",
        "is_creative_relevant": False,
        "goods_services": [
            "保险", "金融事务", "不动产事务", "艺术品估价",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 37, "class_name_zh": "建筑维修",
        "class_name_en": "Construction and repair",
        "is_creative_relevant": False,
        "goods_services": [
            "建筑", "室内装修", "安装服务", "维修",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 38, "class_name_zh": "通讯服务",
        "class_name_en": "Telecommunications",
        "is_creative_relevant": True,
        "goods_services": [
            "电信", "通讯服务", "电视播放", "视频点播传输",
            "提供在线论坛", "互联网广播", "流媒体传输",
        ],
        "common_for_creators": ["直播平台", "创作社区", "虚拟偶像通讯", "在线广播"],
    },
    {
        "class_no": 39, "class_name_zh": "运输仓储",
        "class_name_en": "Transport and storage",
        "is_creative_relevant": False,
        "goods_services": [
            "运输", "商品包装", "旅行安排", "快递服务",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 40, "class_name_zh": "材料加工",
        "class_name_en": "Material treatment",
        "is_creative_relevant": True,
        "goods_services": [
            "材料处理", "印刷", "服装定制", "照片冲印",
            "3D打印定制", "艺术品装裱",
        ],
        "common_for_creators": ["按需印刷", "定制制造", "丝网印刷", "艺术品装裱"],
    },
    {
        "class_no": 41, "class_name_zh": "教育、娱乐、出版",
        "class_name_en": "Education and entertainment",
        "is_creative_relevant": True,
        "goods_services": [
            "教育", "培训", "娱乐服务", "出版服务",
            "在线电子出版物(不可下载)", "组织文化或教育展览",
            "提供不可下载的在线视频", "摄影", "翻译",
        ],
        "common_for_creators": ["在线课程", "内容创作", "直播娱乐", "艺术展览", "出版发行"],
    },
    {
        "class_no": 42, "class_name_zh": "科技服务、设计",
        "class_name_en": "Scientific and technological services",
        "is_creative_relevant": True,
        "goods_services": [
            "计算机软件设计", "平面设计", "工业设计", "包装设计",
            "服装设计", "艺术品鉴定", "网站设计", "科学研究",
            "把有形的数据或文件转换成电子媒体",
        ],
        "common_for_creators": ["插画设计", "UI/UX设计", "品牌设计", "AIGC开发", "软件工具"],
    },
    {
        "class_no": 43, "class_name_zh": "餐饮住宿",
        "class_name_en": "Food and beverage services",
        "is_creative_relevant": True,
        "goods_services": [
            "餐馆", "咖啡馆", "茶馆", "酒店", "临时住宿", "酒吧服务",
        ],
        "common_for_creators": ["主题餐厅", "IP联名咖啡馆", "文创酒店"],
    },
    {
        "class_no": 44, "class_name_zh": "医疗美容",
        "class_name_en": "Medical and beauty services",
        "is_creative_relevant": False,
        "goods_services": [
            "医疗服务", "美容服务", "园艺", "农业服务",
        ],
        "common_for_creators": [],
    },
    {
        "class_no": 45, "class_name_zh": "社会服务",
        "class_name_en": "Legal and social services",
        "is_creative_relevant": True,
        "goods_services": [
            "法律服务", "知识产权许可", "在线社交网络服务",
            "版权管理", "知识产权咨询",
        ],
        "common_for_creators": ["IP维权", "版权管理服务", "IP授权法律咨询"],
    },
]

# 标签 -> 类别映射表 (P1.4.3 类别推荐引擎)
TAG_TO_CLASS_MAP = {
    "插画": [16, 41, 42],
    "角色": [16, 25, 28, 41],
    "漫画": [16, 41],
    "国风": [16, 25, 41],
    "文创": [16, 25, 28, 35, 41],
    "服装": [25, 35],
    "潮牌": [25, 35],
    "玩具": [28, 35],
    "盲盒": [28, 35],
    "手办": [28],
    "游戏": [9, 28, 41, 42],
    "桌游": [28, 41],
    "文具": [16, 35],
    "贴纸": [16],
    "海报": [16, 35],
    "IP": [16, 25, 28, 35, 41],
    "表情包": [16, 41],
    "虚拟偶像": [9, 28, 35, 41, 42],
    "Vtuber": [9, 28, 35, 41],
    "音乐": [9, 41],
    "摄影": [16, 41],
    "出版": [16, 41],
    "设计": [42],
    "软件": [9, 42],
    "AIGC": [9, 41, 42],
    "数字艺术": [9, 16, 41, 42],
    "动画": [9, 16, 28, 41],
    "影视": [9, 41],
    "品牌": [35, 42],
    "网站": [42],
    "印刷品": [16],
}

# 创作者类型 -> 商标类别组合策略 (key 与前端 creator_type 一致)
CREATOR_STRATEGIES = {
    # Illustration / AIGC — 核心支持
    "illustrator": {
        "label": "插画师 / AIGC艺术家",
        "classes": [16, 25, 28, 35, 41],
        "note": "保护平面作品+衍生品+品牌零售+娱乐服务",
    },
    # Photography — v2 规划
    "photographer": {
        "label": "摄影师",
        "classes": [16, 35, 41],
        "note": "印刷品+在线销售+摄影服务",
    },
    # Video — v3 规划
    "video_creator": {
        "label": "视频创作者",
        "classes": [9, 28, 35, 41, 42],
        "note": "视频内容+周边衍生品+娱乐+技术服务",
    },
    # Crafts — v3 规划
    "crafter": {
        "label": "手工艺人",
        "classes": [21, 25, 35, 40],
        "note": "家居用品+服饰+零售+材料加工",
    },
    # Music — v4 规划
    "musician": {
        "label": "音乐人",
        "classes": [9, 35, 41],
        "note": "录音制品+在线零售+娱乐服务",
    },
    # Writing — v4 规划
    "writer": {
        "label": "文字作者",
        "classes": [16, 35, 41],
        "note": "出版物+在线销售+娱乐服务",
    },
    # Legacy aliases (backward compat)
    "illustrator_flat": {
        "label": "插画师(平面)",
        "classes": [16, 35, 41],
        "note": "保护平面作品和品牌, 建议至少覆盖文具和在线零售",
    },
    "illustrator_product": {
        "label": "插画师(产品化)",
        "classes": [16, 25, 28, 35],
        "note": "产品化IP保护, 覆盖衍生品全链路",
    },
    "gamedev": {
        "label": "独立游戏开发者",
        "classes": [9, 28, 41, 42],
        "note": "游戏软件+衍生品+娱乐服务",
    },
    "aigc_creator": {
        "label": "AIGC创作者",
        "classes": [9, 35, 41, 42],
        "note": "数字作品+在线服务+技术工具",
    },
    "vtuber": {
        "label": "Vtuber/虚拟偶像",
        "classes": [9, 28, 35, 38, 41],
        "note": "虚拟形象+衍生品+直播娱乐+通讯服务",
    },
}

# 中国版权登记指引详细内容
COPYRIGHT_GUIDELINES_CN = {
    "title": "中国著作权登记指引",
    "description": "根据《中华人民共和国著作权法》，作品创作完成即自动获得著作权。登记可提供维权证据。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有申请须由权利人自行向中国版权保护中心提交。",
    "legal_basis": "《中华人民共和国著作权法》及《作品自愿登记试行办法》",
    "institution": "中国版权保护中心",
    "platform_url": "https://www.ccopyright.com.cn",
    "fee": {
        "artwork": "¥0-300/件 (美术作品)",
        "text": "¥0-300/件 (文字作品)",
        "music": "¥0-300/件 (音乐作品)",
        "software": "¥0-300/件 (计算机软件)",
    },
    "estimated_duration": "约30个工作日",
    "validity": "公民: 终身+死后50年; 法人: 发表后50年",
    "materials": [
        {
            "name": "作品登记申请表",
            "required": True,
            "description": "系统可自动预填, 用户确认后导出",
            "can_prefill": True,
        },
        {
            "name": "作品样本",
            "required": True,
            "description": "图片JPG/PNG格式, 大小≤50MB; 或音频MP3≤50MB; 视频MP4≤200MB",
            "can_prefill": True,
        },
        {
            "name": "作品创作说明书",
            "required": True,
            "description": "50-500字, 说明创作过程、独创性、完成日期等",
            "can_prefill": True,
        },
        {
            "name": "申请人身份证明",
            "required": True,
            "description": "自然人: 身份证/护照复印件; 法人: 营业执照复印件",
            "can_prefill": False,
        },
        {
            "name": "权利归属证明",
            "required": False,
            "description": "如为委托作品、职务作品等, 需提供合同或声明",
            "can_prefill": False,
        },
        {
            "name": "代理人委托书",
            "required": False,
            "description": "如委托代理机构办理, 需提供委托书",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "准备材料", "description": "按材料清单准备齐全", "duration": "自行安排"},
        {"step": 2, "name": "系统预填申请表", "description": "使用智能助手从作品数据自动填充申请信息", "duration": "即时"},
        {"step": 3, "name": "在线提交", "description": "通过中国版权保护中心官网在线提交", "duration": "约30分钟"},
        {"step": 4, "name": "形式审查", "description": "版权保护中心对申请材料进行形式审查", "duration": "约15工作日"},
        {"step": 5, "name": "缴费", "description": "收到缴费通知后在线缴纳费用", "duration": "即时"},
        {"step": 6, "name": "登记完成", "description": "发放作品登记证书", "duration": "约15工作日"},
    ],
}

TRADEMARK_GUIDELINES_CN = {
    "title": "中国商标注册指引",
    "description": "商标须经注册方获得专用权。通过国家知识产权局商标局办理。",
    "disclaimer": "本工具不提供商标代理服务，仅提供信息指引，不构成法律建议。所有申请费用由用户直接支付给国家平台。",
    "legal_basis": "《中华人民共和国商标法》及其实施条例",
    "institution": "国家知识产权局商标局",
    "platform_url": "https://sbj.cnipa.gov.cn",
    "fee": "¥300/类 (电子申请, 10个商品项目以内), 超过10个项目每项加收¥30",
    "estimated_duration": "6-12个月 (含3个月公告期)",
    "validity": "有效期10年, 每次续展10年 (续展费¥450/类电子)",
    "materials": [
        {
            "name": "商标注册申请书",
            "required": True,
            "description": "含申请人信息、商标图样、指定类别和商品/服务项目",
            "can_prefill": True,
        },
        {
            "name": "商标图样",
            "required": True,
            "description": "JPG格式, 分辨率300dpi以上, 黑白或彩色, 不大于10cm×10cm",
            "can_prefill": False,
        },
        {
            "name": "申请人身份证明",
            "required": True,
            "description": "个体工商户: 个体工商户营业执照+经营者身份证; 企业: 营业执照复印件",
            "can_prefill": False,
        },
        {
            "name": "代理委托书",
            "required": False,
            "description": "如委托代理机构办理, 需提供委托书",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "商标检索", "description": "建议通过商标网上检索系统查询是否已有相同/近似商标", "duration": "自行安排"},
        {"step": 2, "name": "选择类别", "description": "使用类别推荐引擎选定需要注册的商品/服务类别", "duration": "即时"},
        {"step": 3, "name": "准备申请材料", "description": "按材料清单准备齐全", "duration": "自行安排"},
        {"step": 4, "name": "在线提交", "description": "通过商标网上服务系统提交申请", "duration": "约30分钟"},
        {"step": 5, "name": "形式审查", "description": "商标局进行形式审查", "duration": "约1个月"},
        {"step": 6, "name": "实质审查", "description": "审查是否符合商标法规定", "duration": "约4-6个月"},
        {"step": 7, "name": "初审公告", "description": "公告期3个月, 任何人均可提出异议", "duration": "3个月"},
        {"step": 8, "name": "注册公告", "description": "无人异议或异议不成立, 颁发商标注册证", "duration": "约1个月"},
    ],
    "note_personal": "⚠️ 自然人(个人)申请商标需要个体工商户营业执照。如无执照, 需以企业名义申请或申请个体工商户注册。",
}

# ─── P2.4.1-P2.4.5: 全球 IP 指引数据 ──────────────────────────

# 美国版权登记指引 (P2.4.1)
COPYRIGHT_GUIDELINES_US = {
    "title": "美国版权登记指引 (U.S. Copyright Registration)",
    "description": "美国版权局(USCO)提供版权登记服务。虽然版权自动产生，登记是提起侵权诉讼的前提条件。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有申请须由权利人自行向美国版权局(U.S. Copyright Office)提交。",
    "legal_basis": "U.S. Copyright Act (Title 17, U.S. Code)",
    "institution": "U.S. Copyright Office (美国版权局)",
    "platform_url": "https://www.copyright.gov",
    "fee": {
        "standard_electronic": "$45 (标准电子申请, 单一作者/作品)",
        "standard_paper": "$125 (纸质申请)",
        "group_photographs": "$55 (照片组注册, ≤750张)",
        "group_unpublished": "$85 (未发表作品组, ≤10件)",
        "preregistration": "$200 (预登记, 特定作品类型)",
    },
    "estimated_duration": "电子申请: 约1-3个月; 纸质申请: 约5-7个月",
    "validity": "自然人: 终身+死后70年; 法人/职务作品: 发表后95年或创作后120年(以较短者为准)",
    "forms": {
        "CO": "标准电子申请表格 (推荐)",
        "VA": "视觉艺术作品 (Visual Arts)",
        "PA": "表演艺术作品 (Performing Arts)",
        "SR": "录音作品 (Sound Recording)",
        "TX": "文字作品 (Literary Work)",
    },
    "materials": [
        {
            "name": "申请表 (Form CO/VA/PA/SR/TX)",
            "required": True,
            "description": "在线填写eCO系统表格, 选择对应作品类型的表格",
            "can_prefill": True,
        },
        {
            "name": "作品副本 (Deposit Copy)",
            "required": True,
            "description": "未发表: 1份完整副本; 已发表: 2份最佳版本副本。电子文件可在线提交",
            "can_prefill": True,
        },
        {
            "name": "申请费支付",
            "required": True,
            "description": "信用卡或ACH电子支付, 不可退款",
            "can_prefill": False,
        },
        {
            "name": "申请人声明",
            "required": True,
            "description": "确认申请信息真实准确的声明",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "注册eCO账号", "description": "在美国版权局官网注册电子版权办公室(eCO)账号", "duration": "约10分钟"},
        {"step": 2, "name": "选择表格类型", "description": "根据作品类型选择CO/VA/PA/SR/TX表格", "duration": "即时"},
        {"step": 3, "name": "填写申请信息", "description": "填写作品标题、作者信息、创作完成日期等", "duration": "约30分钟"},
        {"step": 4, "name": "上传作品副本", "description": "上传满足格式要求的作品文件", "duration": "约10分钟"},
        {"step": 5, "name": "支付费用", "description": "在线信用卡支付 $45-$125 (电子申请$45起)", "duration": "即时"},
        {"step": 6, "name": "审查等待", "description": "版权局审查员审核材料, 可能要求补正", "duration": "1-7个月"},
        {"step": 7, "name": "获得登记证书", "description": "审查通过后颁发版权登记证书(PDF)", "duration": "—"},
    ],
}

# 欧盟商标指引 (P2.4.2)
TRADEMARK_GUIDELINES_EU = {
    "title": "欧盟商标注册指引 (EUTM - European Union Trade Mark)",
    "description": "欧盟商标(EUTM)通过欧盟知识产权局(EUIPO)注册, 一次申请覆盖27个欧盟成员国, 费用€850起。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有申请须由权利人自行向EUIPO提交。",
    "legal_basis": "Regulation (EU) 2017/1001 on the European Union trade mark",
    "institution": "EUIPO (欧盟知识产权局)",
    "platform_url": "https://www.euipo.europa.eu",
    "fee": {
        "basic_1class": "€850 (电子申请, 1个类别)",
        "additional_class": "€50/额外类别 (第2类)",
        "third_plus_class": "€150/额外类别 (第3类起)",
        "renewal": "€850 (续展, 每10年)",
        "opposition": "€320 (异议费)",
    },
    "estimated_duration": "4-6个月 (如无异议)",
    "validity": "有效期10年, 每次续展10年, 覆盖27个欧盟成员国",
    "member_countries": [
        "奥地利", "比利时", "保加利亚", "克罗地亚", "塞浦路斯", "捷克", "丹麦", "爱沙尼亚",
        "芬兰", "法国", "德国", "希腊", "匈牙利", "爱尔兰", "意大利", "拉脱维亚",
        "立陶宛", "卢森堡", "马耳他", "荷兰", "波兰", "葡萄牙", "罗马尼亚", "斯洛伐克",
        "斯洛文尼亚", "西班牙", "瑞典",
    ],
    "fee_examples": [
        {"classes": 1, "total": "€850", "breakdown": "基础申请费: €850 (第1类)"},
        {"classes": 2, "total": "€900", "breakdown": "基础申请费: €850 + 第2类: €50"},
        {"classes": 3, "total": "€1,050", "breakdown": "基础申请费: €850 + 第2类: €50 + 第3类: €150"},
        {"classes": 4, "total": "€1,200", "breakdown": "基础申请费: €850 + 第2类: €50 + 第3+4类: €300"},
    ],
    "materials": [
        {
            "name": "EUTM申请表",
            "required": True,
            "description": "通过EUIPO电子申请系统填写, 含申请人信息、商标图样、类别/商品服务",
            "can_prefill": True,
        },
        {
            "name": "商标图样",
            "required": True,
            "description": "JPG/PNG格式, 清晰可辨, 建议≥200x200像素",
            "can_prefill": False,
        },
        {
            "name": "申请人身份信息",
            "required": True,
            "description": "个人/企业名称、地址、国籍等基本信息",
            "can_prefill": False,
        },
        {
            "name": "商品/服务清单",
            "required": True,
            "description": "按尼斯分类指定商品和服务项目, 须使用规范术语",
            "can_prefill": True,
        },
    ],
    "process": [
        {"step": 1, "name": "商标检索", "description": "通过eSearch plus检索现有EUTM和成员国商标", "duration": "自行安排"},
        {"step": 2, "name": "提交申请", "description": "通过EUIPO电子申请系统提交", "duration": "约30分钟"},
        {"step": 3, "name": "审查", "description": "EUIPO进行绝对理由审查和检索报告制作", "duration": "约1个月"},
        {"step": 4, "name": "公告异议", "description": "公告期3个月, 第三方可提出异议", "duration": "3个月"},
        {"step": 5, "name": "注册", "description": "无人异议或异议被驳回, 颁发注册证书", "duration": "约2-4周"},
    ],
    "note_language": "申请语言可选择英语、法语、德语、意大利语或西班牙语 (5种官方语言之一)。第二语言从前述5种中另外选择。",
}

# WIPO 马德里体系商标指引 (P2.4.3)
TRADEMARK_GUIDELINES_WIPO = {
    "title": "WIPO 马德里体系商标注册指引 (Madrid System)",
    "description": "马德里体系允许通过一次申请、一种语言、一套费用在多达130个国家/地区注册商标。须先有基础申请/注册。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有申请须通过原属国商标局转交WIPO。",
    "legal_basis": "Madrid Agreement Concerning the International Registration of Marks (1891) & Madrid Protocol (1989)",
    "institution": "WIPO (世界知识产权组织)",
    "platform_url": "https://www.wipo.int/madrid",
    "fee": {
        "basic": "CHF 653 (黑白图样) / CHF 903 (彩色图样)",
        "designation_individual": "CHF 100-900+/每个指定国 (因国家而异)",
        "designation_eu": "CHF 897 (欧盟指定, 作为整体)",
        "designation_us": "CHF 400 (美国指定)",
        "designation_jp": "CHF 282 (日本指定)",
        "designation_kr": "CHF 267 (韩国指定)",
        "supplementary": "CHF 100/每类超过3个类别",
    },
    "estimated_duration": "12-18个月 (各指定国审查时间不同)",
    "validity": "有效期10年, 每次续展10年, 可通过WIPO集中续展",
    "fee_examples": [
        {
            "scenario": "中国基础 + 欧盟 + 美国 + 日本 (1类, 黑白)",
            "total": "CHF 2,232",
            "breakdown": "基础费: CHF 653 + 欧盟: CHF 897 + 美国: CHF 400 + 日本: CHF 282",
        },
        {
            "scenario": "中国基础 + 欧盟 + 韩国 (3类, 黑白)",
            "total": "CHF 1,817",
            "breakdown": "基础费: CHF 653 + 欧盟: CHF 897 + 韩国: CHF 267",
        },
        {
            "scenario": "中国基础 + 欧盟 + 美国 + 日本 + 韩国 (1类, 黑白)",
            "total": "CHF 2,499",
            "breakdown": "基础费: CHF 653 + 欧盟: CHF 897 + 美国: CHF 400 + 日本: CHF 282 + 韩国: CHF 267",
        },
    ],
    "prerequisites": "必须在原属国(中国)已有商标申请或注册作为\"基础申请\"或\"基础注册\"",
    "materials": [
        {
            "name": "国际申请表格(MM2)",
            "required": True,
            "description": "马德里体系正式申请表, 含申请人、商标、指定国家、商品服务等信息",
            "can_prefill": True,
        },
        {
            "name": "基础申请/注册证明",
            "required": True,
            "description": "中国商标局已受理的申请或已注册的商标证明",
            "can_prefill": False,
        },
        {
            "name": "商标图样",
            "required": True,
            "description": "与基础申请/注册一致的商标图样, JPG格式",
            "can_prefill": False,
        },
        {
            "name": "商品/服务翻译",
            "required": False,
            "description": "如指定国要求特定语言翻译, 需提供英文/法文/西班牙文",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "获得基础申请/注册", "description": "先在中国商标局提交国内商标申请或已注册", "duration": "前提条件"},
        {"step": 2, "name": "准备国际申请", "description": "填写MM2表格, 选择指定国家, 列出商品服务", "duration": "约1小时"},
        {"step": 3, "name": "向原属局提交", "description": "通过中国商标局转交WIPO (原属局核证)", "duration": "约1-2个月"},
        {"step": 4, "name": "WIPO形式审查", "description": "WIPO审查形式要件, 录入国际注册簿", "duration": "约1-2个月"},
        {"step": 5, "name": "国际公告", "description": "在WIPO Gazette上公告国际注册", "duration": "即时"},
        {"step": 6, "name": "各指定国审查", "description": "各指定国按本国法律进行实质审查", "duration": "12-18个月"},
        {"step": 7, "name": "保护声明或驳回", "description": "各指定国发出保护声明或临时驳回通知", "duration": "—"},
    ],
    "central_attack_risk": "⚠️ 在注册之日起5年内, 国际注册依附于基础申请/注册。基础申请被驳回或基础注册被撤销/无效, 国际注册将随之失效(中心打击)。",
}

# WIPO 海牙体系外观设计指引 (P2.4.4)
DESIGN_GUIDELINES_WIPO_HAGUE = {
    "title": "WIPO 海牙体系外观设计注册指引 (Hague System)",
    "description": "海牙体系允许通过一次申请在79个缔约方(覆盖96个国家)注册最多100项外观设计。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有申请须由权利人自行提交或通过代理提交。",
    "legal_basis": "Hague Agreement Concerning the International Registration of Industrial Designs (1925, revised 1999 Geneva Act)",
    "institution": "WIPO (世界知识产权组织)",
    "platform_url": "https://www.wipo.int/hague",
    "fee": {
        "basic": "CHF 397 (1项设计)",
        "additional_design": "CHF 19/每项额外设计 (同一洛迦诺类别)",
        "publication": "CHF 17/每复制件 (可选延期公布费 CHF 47)",
        "designation_individual": "各缔约方标准指定费: CHF 42-387/缔约方",
        "designation_eu": "CHF 67 (欧盟指定费)",
        "designation_us": "CHF 557 (美国指定费)",
        "designation_jp": "CHF 577 (日本指定费)",
        "designation_kr": "CHF 210 (韩国指定费)",
    },
    "estimated_duration": "6-12个月 (国际注册阶段约1个月, 各指定国审查6-12个月)",
    "validity": "初始保护期5年, 可续展2次(每次5年), 最长15年",
    "member_count": 79,
    "fee_examples": [
        {
            "scenario": "1项设计 + 欧盟 (延期公布)",
            "total": "CHF 511",
            "breakdown": "基本费: CHF 397 + 欧盟指定: CHF 67 + 延期公布: CHF 47",
        },
        {
            "scenario": "3项设计 + 欧盟 + 美国",
            "total": "CHF 1,059",
            "breakdown": "基本费: CHF 397 + 设计2-3: CHF 38 + 欧盟: CHF 67 + 美国: CHF 557",
        },
        {
            "scenario": "1项设计 + 欧盟 + 韩国 + 日本",
            "total": "CHF 1,251",
            "breakdown": "基本费: CHF 397 + 欧盟: CHF 67 + 韩国: CHF 210 + 日本: CHF 577",
        },
    ],
    "materials": [
        {
            "name": "国际申请表(DM/1)",
            "required": True,
            "description": "海牙体系正式申请表格, 含申请人、设计数量、指定缔约方等",
            "can_prefill": True,
        },
        {
            "name": "外观设计图样",
            "required": True,
            "description": "每个设计提交至少1张图(最多7张), JPG或TIFF, 300dpi, 灰色背景",
            "can_prefill": True,
        },
        {
            "name": "设计说明",
            "required": False,
            "description": "每个设计最多100字说明, 可指明设计的特征",
            "can_prefill": True,
        },
        {
            "name": "洛迦诺分类",
            "required": True,
            "description": "每个设计的洛迦诺(Locarno)分类号",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "确定洛迦诺分类", "description": "为每项设计确定正确的洛迦诺分类号", "duration": "约30分钟"},
        {"step": 2, "name": "准备设计图样", "description": "按要求格式准备每个设计的图样(正投影视图/立体图)", "duration": "自行安排"},
        {"step": 3, "name": "提交国际申请", "description": "通过eHague系统在线提交或直接向WIPO提交", "duration": "约1小时"},
        {"step": 4, "name": "WIPO形式审查", "description": "WIPO审查形式要件, 不符合的发出补正通知", "duration": "约1个月"},
        {"step": 5, "name": "国际注册", "description": "形式审查合格, 录入国际注册簿并公告", "duration": "即时"},
        {"step": 6, "name": "各指定国实质审查", "description": "各指定缔约方按本国法进行实质审查", "duration": "6-12个月"},
        {"step": 7, "name": "保护声明或驳回", "description": "各指定缔约方发出保护声明或驳回通知", "duration": "—"},
    ],
}

# 日本商标指引 (P2.4.5)
TRADEMARK_GUIDELINES_JP = {
    "title": "日本商标注册指引 (JPO Trademark)",
    "description": "日本特许厅(JPO)负责商标注册。日本实行先申请原则, 商标保护须经注册。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有申请须由权利人自行或通过日本辨理士提交。",
    "legal_basis": "日本商标法 (商標法, Act No. 127 of 1959)",
    "institution": "JPO (日本特许厅)",
    "platform_url": "https://www.jpo.go.jp",
    "fee": {
        "application_1class": "¥3,400 + (¥8,600 × 分类数)",
        "application_example_1class": "¥12,000 (1类申请)",
        "application_example_3class": "¥29,200 (3类申请)",
        "registration": "¥28,200/每类 (注册费, 10年分期可选)",
        "renewal": "¥38,800/每类 (续展费, 10年)",
        "renewal_5year": "¥22,600/每类 (5年分期续展)",
    },
    "estimated_duration": "6-12个月 (无驳回情况)",
    "validity": "有效期10年, 每次续展10年 (或在续展时分5年+5年支付)",
    "materials": [
        {
            "name": "商标注册申请书",
            "required": True,
            "description": "日文填写, 含申请人信息、商标、指定商品/服务 (须使用日文尼斯分类术语)",
            "can_prefill": True,
        },
        {
            "name": "商标图样",
            "required": True,
            "description": "JPG/PNG格式, 8cm×8cm以内, 300dpi以上",
            "can_prefill": False,
        },
        {
            "name": "申请人信息",
            "required": True,
            "description": "个人: 姓名、地址、国籍; 企业: 公司名称、注册地址、代表人",
            "can_prefill": False,
        },
        {
            "name": "委托书(委任状)",
            "required": False,
            "description": "如委托日本辨理士(专利商标代理人)办理, 需提供委托书",
            "can_prefill": False,
        },
        {
            "name": "优先权证明",
            "required": False,
            "description": "如主张优先权(如中国在先申请), 需在申请日起3个月内提交证明文件",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "事前检索", "description": "通过J-PlatPat检索现有商标 (建议委托辨理士做专业检索)", "duration": "自行安排"},
        {"step": 2, "name": "准备日文申请文件", "description": "准备日文申请书和商品/服务清单", "duration": "约1小时"},
        {"step": 3, "name": "提交申请", "description": "在线提交或通过辨理士提交至JPO", "duration": "约30分钟"},
        {"step": 4, "name": "方式审查", "description": "JPO进行形式审查, 不符合要求的通知补正", "duration": "约1个月"},
        {"step": 5, "name": "实质审查", "description": "审查员审查商标显著性、在先权利、公共秩序等", "duration": "3-6个月"},
        {"step": 6, "name": "注册查定/驳回", "description": "发出注册决定或驳回理由通知, 可提出意见书或补正", "duration": "—"},
        {"step": 7, "name": "注册费缴纳", "description": "在注册查定后30天内缴纳注册费(可一次10年或5年分期)", "duration": "30天内"},
        {"step": 8, "name": "商标登录", "description": "缴费后JPO完成商标注册, 发布商标公报", "duration": "约2周"},
    ],
    "note_agent": "⚠️ 日本商标申请强烈建议委托日本辨理士(弁理士)办理。在日本无住所或营业所的外国申请人必须委托日本国内代理人。代理费一般为JPY 50,000-150,000。",
}

# 韩国商标指引 (P2.4.5)
TRADEMARK_GUIDELINES_KR = {
    "title": "韩国商标注册指引 (KIPO Trademark)",
    "description": "韩国特许厅(KIPO)负责商标注册。韩国同样实行先申请原则。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有申请须由权利人自行或通过韩国辨理士提交。",
    "legal_basis": "韩国商标法 (大韩民国商標法, Act No. 71 of 1949, as amended)",
    "institution": "KIPO (韩国特许厅)",
    "platform_url": "https://www.kipo.go.kr",
    "fee": {
        "application_electronic": "KRW 56,000/类 (电子申请)",
        "application_paper": "KRW 66,000/类 (纸质申请)",
        "application_example_1class": "KRW 56,000 (1类电子申请)",
        "application_example_3class": "KRW 168,000 (3类电子申请)",
        "registration": "KRW 201,000/类 (注册费, 10年, 含2次分期可选)",
        "renewal": "KRW 310,000/类 (续展费, 10年)",
    },
    "estimated_duration": "6-10个月 (无驳回/异议情况)",
    "validity": "有效期10年, 每次续展10年",
    "materials": [
        {
            "name": "商标注册申请书",
            "required": True,
            "description": "韩文填写, 含申请人信息、商标、指定商品/服务 (使用韩文尼斯分类术语)",
            "can_prefill": True,
        },
        {
            "name": "商标图样",
            "required": True,
            "description": "JPG/PNG格式, 清晰可辨, 不大于4MB",
            "can_prefill": False,
        },
        {
            "name": "申请人信息",
            "required": True,
            "description": "个人: 姓名、地址、国籍; 企业: 公司名称、代表人、注册地址",
            "can_prefill": False,
        },
        {
            "name": "委托书",
            "required": False,
            "description": "如委托韩国辨理士(弁理士)代理, 需提供签字的委托书",
            "can_prefill": False,
        },
        {
            "name": "优先权证明",
            "required": False,
            "description": "如主张优先权, 须在申请日起3个月内提交经认证的优先权证明文件及韩文翻译",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "事先检索", "description": "通过KIPRIS检索现有商标, 建议委托辨理士做专业检索", "duration": "自行安排"},
        {"step": 2, "name": "提交申请", "description": "通过KIPO电子系统(Patent Net)或委托辨理士提交", "duration": "约30分钟"},
        {"step": 3, "name": "方式审查", "description": "KIPO审查形式要件", "duration": "约1个月"},
        {"step": 4, "name": "实质审查", "description": "审查员审查商标显著性、在先权利等 (可请求加速审查)", "duration": "4-8个月"},
        {"step": 5, "name": "公告", "description": "审查通过后公告2个月, 第三方可提出异议", "duration": "2个月"},
        {"step": 6, "name": "注册决定/驳回", "description": "无异议或异议不成立, 发出注册决定", "duration": "—"},
        {"step": 7, "name": "注册费缴纳", "description": "收到注册决定后2个月内缴纳注册费(可一次或分期)", "duration": "2个月内"},
        {"step": 8, "name": "注册公告", "description": "缴费完成后KIPO进行注册公告", "duration": "约2-4周"},
    ],
    "note_agent": "⚠️ 韩国商标申请建议委托韩国辨理士(弁理士)办理。在韩国无住所或营业所的外国申请人必须委托韩国国内代理人。代理费约为KRW 400,000-800,000。",
}

# 外观设计指南 (中国, 补充完整)
DESIGN_GUIDELINES_CN = {
    "title": "中国外观设计专利指引",
    "description": "外观设计保护产品的外观造型, 如图案、形状或其结合。适合手办、盲盒、包装、UI等设计保护。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。",
    "legal_basis": "《中华人民共和国专利法》(2020修正) 第2条、第23条、第27条",
    "institution": "国家知识产权局 (CNIPA)",
    "platform_url": "https://www.cnipa.gov.cn",
    "fee": {
        "申请费": "¥500",
        "登记费": "¥600 (含印花税¥5 + 第1年年费¥600)",
        "第1-3年年费": "¥600/年",
        "第4-5年年费": "¥900/年",
        "第6-8年年费": "¥1,200/年",
        "第9-10年年费": "¥2,000/年",
        "第11-15年年费": "免费 (保护期15年, 无需续展)",
    },
    "estimated_duration": "4-8个月",
    "validity": "有效期15年 (2021年6月1日起施行), 需每年缴纳年费维持",
    "materials": [
        {
            "name": "外观设计专利请求书",
            "required": True,
            "description": "含设计名称、申请人、设计人、洛迦诺分类号",
            "can_prefill": True,
        },
        {
            "name": "外观设计图片或照片",
            "required": True,
            "description": "正投影六面视图+立体图, JPG/PNG, 灰度或彩色",
            "can_prefill": True,
        },
        {
            "name": "简要说明",
            "required": True,
            "description": "产品用途、设计要点、最能表明设计要点的图片",
            "can_prefill": True,
        },
        {
            "name": "申请人身份证明",
            "required": True,
            "description": "身份证/营业执照复印件",
            "can_prefill": False,
        },
    ],
    "process": [
        {"step": 1, "name": "新颖性检索", "description": "检索现有设计, 确保无相同/实质相同设计", "duration": "自行安排"},
        {"step": 2, "name": "准备图样", "description": "制作六面视图+立体图", "duration": "自行安排"},
        {"step": 3, "name": "提交申请", "description": "通过中国专利电子申请系统提交", "duration": "约30分钟"},
        {"step": 4, "name": "形式审查", "description": "审查文件是否齐全、格式是否合规", "duration": "约1个月"},
        {"step": 5, "name": "初步审查", "description": "审查是否明显不符合授权条件", "duration": "3-6个月"},
        {"step": 6, "name": "授权公告", "description": "审查合格, 发出授权通知, 缴纳登记费后公告", "duration": "约1个月"},
    ],
}

# ─── P2.4.6: EUIPO SME Fund ──────────────────────────────────────

EUIPO_SME_FUND_GUIDE = {
    "title": "EUIPO 中小企业基金 (SME Fund) 指引",
    "description": "EUIPO设立的SME Fund为欧盟中小企业在商标和外观设计申请方面提供75%费用补贴(最高€1,000-1,500)。",
    "disclaimer": "本工具仅提供信息指引，不构成法律建议。资助政策和额度以EUIPO官网最新公告为准。",
    "program_name": "Ideas Powered for Business SME Fund",
    "official_url": "https://www.euipo.europa.eu/en/sme-corner/sme-fund",
    "eligibility": {
        "definition": "欧盟中小企业(SME): 雇员少于250人、年营业额不超过€5,000万或资产负债表总额不超过€4,300万的企业",
        "requirements": [
            "在欧盟成员国注册并运营的企业",
            "满足SME定义标准",
            "拥有有效的欧盟增值税号(VAT)或成员国税务登记号",
            "未被排除在欧盟资助计划之外(如破产、严重职业过失等)",
        ],
        "not_eligible": [
            "大型企业 (雇员≥250人或年营业额>€5,000万)",
            "非欧盟注册企业",
            "自然人(非企业) — 但可先注册个体工商户(Sole Proprietor)",
            "已获得SME Fund同类资助的企业(同一资助周期内)",
        ],
    },
    "coverage": {
        "trademark": {
            "reimbursement_rate": "75%",
            "voucher_1": "€1,000 (商标和外观合计, 2025年版)",
            "voucher_2": "€1,500 (仅商标, 2025年版, 可能变动)",
            "covers": [
                "EUTM 申请费(基本费€850)",
                "EUIPO 审查/注册费",
                "成员国的国内商标申请费",
            ],
        },
        "design": {
            "reimbursement_rate": "75%",
            "voucher": "€1,000 (含商标合计)",
            "covers": [
                "注册式共同体外观设计(RCD)申请费",
                "成员国的国内外观设计注册费",
            ],
        },
    },
    "application_process": [
        {"step": 1, "name": "检查资格", "description": "确认企业满足SME定义(雇员<250, 营业额<€50M)", "duration": "即时"},
        {"step": 2, "name": "注册/登录EUIPO账户", "description": "在EUIPO官网创建或登录企业账户", "duration": "约10分钟"},
        {"step": 3, "name": "提交SME Fund申请", "description": "在EUIPO SME Fund页面提交资助申请, 上传企业证明文件", "duration": "约30分钟"},
        {"step": 4, "name": "获得资助券(Voucher)", "description": "EUIPO审核通过后发放资助券(一般在10个工作日内)", "duration": "10个工作日"},
        {"step": 5, "name": "提交IP申请并使用资助券", "description": "在EUIPO或成员国IP局提交商标/外观设计申请, 使用资助券抵扣75%费用", "duration": "即时"},
        {"step": 6, "name": "支付剩余25%", "description": "企业自行支付剩余的25%官费", "duration": "即时"},
    ],
    "key_dates": "SME Fund通常每年年初开放申请, 资金有限, 先到先得。建议每年1月关注EUIPO官网了解最新开放时间。",
    "example": {
        "scenario": "典型支出 (1个EUTM, 1类)",
        "total_fee": "€850",
        "sme_fund_covers": "€637.50 (75%)",
        "your_cost": "€212.50 (25%)",
        "savings": "€637.50",
    },
    "tips": [
        "每年预算有限, 建议在窗口开放首日提交申请",
        "资助券通常在发放后2-3个月内有效, 需及时使用",
        "已有EUTM的续展通常不在资助范围内",
        "通过代理的代理费不在资助范围内",
    ],
}

# ─── P2.4.10-P2.4.12: 费用计算器数据 ──────────────────────────

# 各辖区费用表 (用于费用计算器)
FEE_SCHEDULE = {
    "cn": {
        "trademark": {
            "label": "中国商标 (CNIPA)",
            "currency": "CNY",
            "application_fee_per_class": 300,
            "items_included": 10,
            "excess_item_fee": 30,
            "registration_fee_per_class": 0,
            "renewal_fee_per_class": 450,
            "notes": "电子申请, 含10个商品/服务项目",
        },
        "copyright": {
            "label": "中国版权 (CPSCC)",
            "currency": "CNY",
            "application_fee_per_class": 300,
            "notes": "美术/文字/音乐作品, 软件著作权登记费各不同",
        },
        "design_patent": {
            "label": "中国外观设计 (CNIPA)",
            "currency": "CNY",
            "application_fee_per_class": 500,
            "registration_fee_per_class": 600,
            "annual_fee": 600,
            "notes": "含第1年年费; 后续年费¥600-2000/年",
        },
    },
    "us": {
        "trademark": {
            "label": "美国商标 (USPTO TEAS Plus)",
            "currency": "USD",
            "application_fee_per_class": 250,
            "notes": "TEAS Plus申请, 须使用USPTO标准商品服务清单",
        },
        "copyright": {
            "label": "美国版权 (USCO)",
            "currency": "USD",
            "application_fee_per_class": 45,
            "notes": "标准电子申请 (单一作者/作品)",
        },
    },
    "eu": {
        "trademark": {
            "label": "欧盟商标 (EUIPO EUTM)",
            "currency": "EUR",
            "application_fee_per_class": 850,
            "second_class_fee": 50,
            "third_plus_class_fee": 150,
            "renewal_fee_per_class": 850,
            "notes": "基础费€850含1类, 第2类+€50, 第3类起每类+€150",
        },
        "design_patent": {
            "label": "欧盟外观设计 (RCD)",
            "currency": "EUR",
            "application_fee_per_class": 350,
            "additional_design_fee": 175,
            "renewal_fee": 90,
            "notes": "1项设计€350起, 第2-10项€175/项",
        },
    },
    "wipo": {
        "trademark": {
            "label": "WIPO 马德里商标",
            "currency": "CHF",
            "application_fee_per_class": 653,
            "color_surcharge": 250,
            "notes": "基础费CHF 653 (黑白), CHF 903 (彩色); 指定费另计",
            "designation_fees": {
                "eu": 897,
                "us": 400,
                "jp": 282,
                "kr": 267,
                "cn": 249,
            },
        },
        "design_patent": {
            "label": "WIPO 海牙外观设计",
            "currency": "CHF",
            "application_fee_per_class": 397,
            "additional_design_fee": 19,
            "publication_fee": 17,
            "deferred_publication_fee": 47,
            "notes": "基础费CHF 397含1项设计, 额外设计+CHF 19/项",
            "designation_fees": {
                "eu": 67,
                "us": 557,
                "jp": 577,
                "kr": 210,
            },
        },
    },
    "jp": {
        "trademark": {
            "label": "日本商标 (JPO)",
            "currency": "JPY",
            "application_fee_per_class": 12000,
            "registration_fee_per_class": 28200,
            "notes": "申请费: ¥3,400 + ¥8,600×类数 ≈ ¥12,000/类; 注册费¥28,200/类",
        },
    },
    "kr": {
        "trademark": {
            "label": "韩国商标 (KIPO)",
            "currency": "KRW",
            "application_fee_per_class": 56000,
            "registration_fee_per_class": 201000,
            "notes": "电子申请, 申请费KRW 56,000/类; 注册费KRW 201,000/类",
        },
    },
}


# ─── 种子数据初始化辅助函数 ──────────────────────────────────


def _seed_nice_classes(db: Session):
    """如果尼斯分类表为空, 插入种子数据."""
    existing = db.query(func.count(NiceClassification.id)).scalar()
    if existing == 0:
        for item in NICE_CLASSES_SEED:
            db.add(NiceClassification(
                class_no=item["class_no"],
                class_name_zh=item["class_name_zh"],
                class_name_en=item.get("class_name_en"),
                goods_services=item.get("goods_services", []),
                is_creative_relevant=item.get("is_creative_relevant", False),
                common_for_creators=item.get("common_for_creators", []),
                updated_year=item.get("updated_year", 2026),
            ))
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise


# ─── P2.4.8-P2.4.9: 申请模板数据 ──────────────────────────────

APPLICATION_TEMPLATES_SEED = [
    # 1. 美国版权 eCO 申请表
    {
        "ip_type": "copyright",
        "jurisdiction": "us",
        "template_name": "美国版权 eCO 申请表",
        "template_version": "2026.1",
        "form_schema": {
            "title": "U.S. Copyright Office eCO Application",
            "sections": [
                {
                    "section": "type_of_work",
                    "label": "作品类型",
                    "fields": [
                        {"name": "work_type", "label": "Work Type", "type": "select",
                         "options": ["Literary Work", "Visual Arts", "Performing Arts", "Sound Recording", "Motion Picture/Audiovisual"],
                         "required": True},
                        {"name": "form_type", "label": "Form Type", "type": "select",
                         "options": ["CO", "VA", "PA", "SR", "TX"], "required": True},
                    ],
                },
                {
                    "section": "title",
                    "label": "作品信息",
                    "fields": [
                        {"name": "title_of_work", "label": "Title of Work", "type": "text", "required": True},
                        {"name": "alternative_title", "label": "Alternative Title", "type": "text", "required": False},
                        {"name": "year_of_completion", "label": "Year of Completion", "type": "number", "required": True, "min": 1900, "max": 2026},
                        {"name": "date_of_first_publication", "label": "Date of First Publication", "type": "date", "required": False},
                        {"name": "nation_of_first_publication", "label": "Nation of First Publication", "type": "text", "required": False},
                    ],
                },
                {
                    "section": "author",
                    "label": "作者信息",
                    "fields": [
                        {"name": "author_name", "label": "Author Name (姓名)", "type": "text", "required": True},
                        {"name": "author_citizenship", "label": "Author Citizenship (国籍)", "type": "text", "required": True},
                        {"name": "author_domicile", "label": "Author Domicile (住所地)", "type": "text", "required": True},
                        {"name": "author_birth_year", "label": "Year of Birth", "type": "number", "required": False},
                        {"name": "is_anonymous", "label": "Anonymous/Pseudonymous", "type": "checkbox", "required": False},
                        {"name": "work_made_for_hire", "label": "Work Made for Hire", "type": "checkbox", "required": False},
                    ],
                },
                {
                    "section": "claimant",
                    "label": "版权申请人",
                    "fields": [
                        {"name": "claimant_name", "label": "Claimant Name", "type": "text", "required": True},
                        {"name": "claimant_address", "label": "Claimant Address", "type": "text", "required": True},
                        {"name": "transfer_statement", "label": "Transfer Statement", "type": "textarea", "required": False},
                    ],
                },
                {
                    "section": "deposit",
                    "label": "作品副本",
                    "fields": [
                        {"name": "deposit_type", "label": "Deposit Type", "type": "select",
                         "options": ["Electronic", "Physical"], "required": True},
                        {"name": "file_format", "label": "File Format", "type": "text", "required": False},
                    ],
                },
            ],
        },
        "field_mappings": {
            "title_of_work": {"source": "work.title"},
            "year_of_completion": {"source": "work.created_at", "transform": "year"},
            "date_of_first_publication": {"source": "work.created_at", "transform": "date"},
            "work_type": {"source": "work.file_type", "mapping": {"image": "Visual Arts", "video": "Motion Picture/Audiovisual", "audio": "Sound Recording", "document": "Literary Work", "code": "Literary Work"}},
            "deposit_type": {"source": "constant", "value": "Electronic"},
        },
        "validation_rules": {
            "year_of_completion": {"type": "integer", "min": 1900, "max": 2026},
            "author_name": {"type": "string", "min_length": 1},
        },
        "fee_schedule": {"standard_electronic": 45, "standard_paper": 125, "single_author_single_work": 45},
        "required_documents": ["作品副本(Deposit Copy)", "申请费支付凭证"],
        "official_submission_url": "https://www.copyright.gov/registration/",
        "official_guide_url": "https://www.copyright.gov/help/",
        "estimated_duration": "1-7个月",
        "legal_basis": "U.S. Copyright Act (Title 17, U.S. Code)",
    },
    # 2. EUIPO EUTM 商标申请表
    {
        "ip_type": "trademark",
        "jurisdiction": "eu",
        "template_name": "EUIPO EUTM 商标申请表",
        "template_version": "2026.1",
        "form_schema": {
            "title": "EUIPO EUTM Application Form",
            "sections": [
                {
                    "section": "applicant",
                    "label": "申请人信息",
                    "fields": [
                        {"name": "applicant_type", "label": "Applicant Type", "type": "select",
                         "options": ["Natural Person", "Legal Entity"], "required": True},
                        {"name": "applicant_name", "label": "Name/Company Name", "type": "text", "required": True},
                        {"name": "applicant_address", "label": "Address", "type": "text", "required": True},
                        {"name": "applicant_country", "label": "Country", "type": "text", "required": True},
                        {"name": "applicant_email", "label": "Email", "type": "email", "required": True},
                    ],
                },
                {
                    "section": "representation",
                    "label": "代理人信息(选填)",
                    "fields": [
                        {"name": "representative_name", "label": "Representative Name", "type": "text", "required": False},
                        {"name": "representative_id", "label": "Representative ID (EUIPO)", "type": "text", "required": False},
                    ],
                },
                {
                    "section": "mark",
                    "label": "商标信息",
                    "fields": [
                        {"name": "mark_type", "label": "Mark Type", "type": "select",
                         "options": ["Word Mark", "Figurative Mark", "Shape Mark", "Pattern Mark", "Colour Mark", "Sound Mark", "Motion Mark", "Multimedia Mark", "Hologram Mark"],
                         "required": True},
                        {"name": "mark_text", "label": "Mark Text (文字商标)", "type": "text", "required": False},
                        {"name": "mark_description", "label": "Mark Description", "type": "textarea", "required": False},
                        {"name": "colour_claimed", "label": "Colour Claimed", "type": "checkbox", "required": False},
                        {"name": "disclaimer", "label": "Disclaimer (放弃专用权声明)", "type": "textarea", "required": False},
                    ],
                },
                {
                    "section": "goods_services",
                    "label": "商品/服务 - 按尼斯分类",
                    "fields": [
                        {"name": "language", "label": "申请语言", "type": "select",
                         "options": ["English", "French", "German", "Italian", "Spanish"], "required": True},
                        {"name": "second_language", "label": "第二语言", "type": "select",
                         "options": ["English", "French", "German", "Italian", "Spanish"], "required": True},
                        {"name": "classes", "label": "Nice Classes", "type": "class_selector", "required": True,
                         "description": "选择尼斯分类类别并指定商品/服务项目, 使用EUIPO TMclass标准术语"},
                    ],
                },
                {
                    "section": "priority",
                    "label": "优先权(选填)",
                    "fields": [
                        {"name": "priority_claimed", "label": "Claim Priority", "type": "checkbox", "required": False},
                        {"name": "priority_country", "label": "Priority Country", "type": "text", "required": False},
                        {"name": "priority_date", "label": "Priority Date", "type": "date", "required": False},
                        {"name": "priority_number", "label": "Priority Application Number", "type": "text", "required": False},
                    ],
                },
            ],
        },
        "field_mappings": {
            "mark_text": {"source": "work.title"},
            "mark_type": {"source": "constant", "value": "Figurative Mark"},
            "language": {"source": "constant", "value": "English"},
            "second_language": {"source": "constant", "value": "French"},
        },
        "validation_rules": {
            "applicant_name": {"type": "string", "min_length": 1},
            "mark_type": {"type": "enum", "values": ["Word Mark", "Figurative Mark", "Shape Mark", "Pattern Mark", "Colour Mark", "Sound Mark", "Motion Mark", "Multimedia Mark", "Hologram Mark"]},
        },
        "fee_schedule": {"basic_1class": 850, "second_class": 50, "third_plus_class": 150},
        "required_documents": ["商标图样(JPG/PNG)", "申请人身份证明", "商品/服务清单"],
        "official_submission_url": "https://www.euipo.europa.eu/en/trademarks/apply",
        "official_guide_url": "https://www.euipo.europa.eu/en/trademarks/before-applying",
        "estimated_duration": "4-6个月",
        "legal_basis": "Regulation (EU) 2017/1001",
    },
    # 3. WIPO 马德里体系申请表
    {
        "ip_type": "trademark",
        "jurisdiction": "wipo",
        "template_name": "WIPO 马德里体系 MM2 申请表",
        "template_version": "2026.1",
        "form_schema": {
            "title": "WIPO Madrid System MM2 International Application",
            "sections": [
                {
                    "section": "basic_application",
                    "label": "基础申请/注册信息",
                    "fields": [
                        {"name": "basic_application_number", "label": "Basic Application Number (基础申请号)", "type": "text", "required": True},
                        {"name": "basic_registration_number", "label": "Basic Registration Number (基础注册号)", "type": "text", "required": False},
                        {"name": "basic_date", "label": "Basic Application/Registration Date", "type": "date", "required": True},
                        {"name": "office_of_origin", "label": "Office of Origin (原属局)", "type": "text", "required": True, "value": "CNIPA (China)"},
                    ],
                },
                {
                    "section": "applicant",
                    "label": "申请人信息",
                    "fields": [
                        {"name": "applicant_name", "label": "Name of Applicant", "type": "text", "required": True},
                        {"name": "applicant_address", "label": "Address", "type": "text", "required": True},
                        {"name": "applicant_nationality", "label": "Nationality", "type": "text", "required": True},
                        {"name": "applicant_email", "label": "Email", "type": "email", "required": True},
                        {"name": "entitlement", "label": "Entitlement Basis (资格依据)", "type": "select",
                         "options": ["National of China", "Domiciled in China", "Real and effective industrial/commercial establishment in China"],
                         "required": True},
                    ],
                },
                {
                    "section": "mark",
                    "label": "商标信息",
                    "fields": [
                        {"name": "mark_reproduction", "label": "Reproduction of Mark (是否与基础商标一致)", "type": "checkbox", "required": True},
                        {"name": "mark_type", "label": "Type of Mark", "type": "select",
                         "options": ["Standard Characters", "Figurative/Device", "Three-dimensional", "Colour"],
                         "required": True},
                        {"name": "colour_claimed", "label": "Colour Claimed", "type": "checkbox", "required": False},
                        {"name": "colour_description", "label": "Colour Description", "type": "text", "required": False},
                        {"name": "description_of_mark", "label": "Description of Mark", "type": "textarea", "required": False},
                        {"name": "translation", "label": "Translation (如商标含非英文/法文/西班牙文)", "type": "text", "required": False},
                        {"name": "transliteration", "label": "Transliteration (音译)", "type": "text", "required": False},
                    ],
                },
                {
                    "section": "goods_services",
                    "label": "商品/服务",
                    "fields": [
                        {"name": "language", "label": "申请语言", "type": "select",
                         "options": ["English", "French", "Spanish"], "required": True},
                        {"name": "classes", "label": "Nice Classes", "type": "class_selector", "required": True},
                        {"name": "goods_services_list", "label": "Goods and Services List", "type": "textarea", "required": True,
                         "description": "按尼斯分类列出所有商品/服务, 必须与基础申请一致或更窄"},
                    ],
                },
                {
                    "section": "designations",
                    "label": "指定缔约方",
                    "fields": [
                        {"name": "designations", "label": "Designated Contracting Parties", "type": "multiselect",
                         "options": ["EU", "US", "JP", "KR", "GB", "AU", "CA", "IN", "BR", "MX", "RU", "SG", "TH", "VN", "MY", "ID", "PH"],
                         "required": True},
                        {"name": "designation_fee_info", "label": "Designation Fee Notes", "type": "text", "required": False,
                         "description": "各指定国费用请参考WIPO Individual Fees"},
                    ],
                },
            ],
        },
        "field_mappings": {
            "mark_reproduction": {"source": "constant", "value": True},
            "entitlement": {"source": "constant", "value": "National of China"},
            "language": {"source": "constant", "value": "English"},
        },
        "validation_rules": {
            "basic_application_number": {"type": "string", "min_length": 1},
            "designations": {"type": "array", "min_items": 1},
        },
        "fee_schedule": {"basic_bw": 653, "basic_color": 903, "supplementary_per_class_gt_3": 100},
        "required_documents": ["基础申请/注册证明", "商标图样(与基础申请一致)"],
        "official_submission_url": "https://www.wipo.int/madrid/en/",
        "official_guide_url": "https://www.wipo.int/madrid/en/guide/",
        "estimated_duration": "12-18个月",
        "legal_basis": "Madrid Agreement & Madrid Protocol",
    },
    # 4. CNIPA 商标注册申请表
    {
        "ip_type": "trademark",
        "jurisdiction": "cn",
        "template_name": "中国商标注册申请书",
        "template_version": "2026.1",
        "form_schema": {
            "title": "商标注册申请书 (CNIPA)",
            "sections": [
                {
                    "section": "applicant",
                    "label": "申请人信息",
                    "fields": [
                        {"name": "applicant_type", "label": "申请人类型", "type": "select",
                         "options": ["企业", "个体工商户", "自然人(需个体执照)", "社会团体", "其他组织"],
                         "required": True},
                        {"name": "applicant_name", "label": "申请人名称(中文)", "type": "text", "required": True},
                        {"name": "applicant_name_en", "label": "申请人名称(英文)", "type": "text", "required": False},
                        {"name": "applicant_address", "label": "申请人地址(中文)", "type": "text", "required": True},
                        {"name": "applicant_address_en", "label": "申请人地址(英文)", "type": "text", "required": False},
                        {"name": "unified_social_credit_code", "label": "统一社会信用代码", "type": "text", "required": False},
                        {"name": "id_number", "label": "身份证号(个体)", "type": "text", "required": False},
                        {"name": "contact_person", "label": "联系人", "type": "text", "required": True},
                        {"name": "contact_phone", "label": "联系电话", "type": "text", "required": True},
                        {"name": "contact_email", "label": "电子邮箱", "type": "email", "required": False},
                    ],
                },
                {
                    "section": "mark",
                    "label": "商标信息",
                    "fields": [
                        {"name": "mark_type", "label": "商标类型", "type": "select",
                         "options": ["一般商标", "集体商标", "证明商标", "三维标志", "颜色组合"],
                         "required": True},
                        {"name": "mark_text", "label": "商标名称/文字", "type": "text", "required": False},
                        {"name": "is_color", "label": "指定颜色", "type": "checkbox", "required": False},
                        {"name": "mark_description", "label": "商标说明", "type": "textarea", "required": False,
                         "description": "如为外文商标或无含义字母组合, 须说明含义"},
                    ],
                },
                {
                    "section": "classes",
                    "label": "商标类别和商品/服务项目",
                    "fields": [
                        {"name": "classes", "label": "指定类别", "type": "class_selector", "required": True,
                         "description": "按尼斯分类选择类别并指定规范商品/服务项目, 使用中国商标局公布的标准术语"},
                        {"name": "category_note", "label": "类别说明", "type": "text", "required": False},
                    ],
                },
                {
                    "section": "priority",
                    "label": "优先权声明(选填)",
                    "fields": [
                        {"name": "priority_claimed", "label": "要求优先权", "type": "checkbox", "required": False},
                        {"name": "priority_country", "label": "优先权国家/地区", "type": "text", "required": False},
                        {"name": "priority_date", "label": "首次申请日期", "type": "date", "required": False},
                        {"name": "priority_number", "label": "首次申请号", "type": "text", "required": False},
                    ],
                },
                {
                    "section": "agent",
                    "label": "商标代理机构(选填)",
                    "fields": [
                        {"name": "agent_name", "label": "代理机构名称", "type": "text", "required": False},
                        {"name": "agent_code", "label": "代理机构备案号", "type": "text", "required": False},
                        {"name": "agent_person", "label": "代理人姓名", "type": "text", "required": False},
                    ],
                },
            ],
        },
        "field_mappings": {
            "mark_text": {"source": "work.title"},
            "is_color": {"source": "constant", "value": False},
            "mark_type": {"source": "constant", "value": "一般商标"},
            "contact_email": {"source": "user.email"},
        },
        "validation_rules": {
            "applicant_name": {"type": "string", "min_length": 1, "message": "申请人名称为必填"},
            "applicant_address": {"type": "string", "min_length": 1, "message": "申请人地址为必填"},
            "contact_person": {"type": "string", "min_length": 1},
        },
        "fee_schedule": {"per_class_electronic": 300, "excess_item_per_class": 30, "max_items_included": 10},
        "required_documents": ["商标图样(JPG/PNG, ≥300dpi)", "身份证明(营业执照/身份证)", "如委托代理: 商标代理委托书"],
        "official_submission_url": "https://sbj.cnipa.gov.cn",
        "official_guide_url": "https://sbj.cnipa.gov.cn/sbj/bszn/",
        "estimated_duration": "6-12个月",
        "legal_basis": "《中华人民共和国商标法》",
    },
]


def _seed_application_templates(db: Session):
    """如果申请表模板表为空, 插入种子数据."""
    existing = db.query(func.count(ApplicationTemplate.id)).scalar()
    if existing == 0:
        for item in APPLICATION_TEMPLATES_SEED:
            db.add(ApplicationTemplate(
                ip_type=item["ip_type"],
                jurisdiction=item["jurisdiction"],
                template_name=item["template_name"],
                template_version=item.get("template_version", "1.0"),
                form_schema=item.get("form_schema", {}),
                field_mappings=item.get("field_mappings", {}),
                validation_rules=item.get("validation_rules"),
                fee_schedule=item.get("fee_schedule"),
                required_documents=item.get("required_documents"),
                official_submission_url=item.get("official_submission_url"),
                official_guide_url=item.get("official_guide_url"),
                estimated_duration=item.get("estimated_duration"),
                legal_basis=item.get("legal_basis"),
                is_active=True,
            ))
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise


# ─── IP 登记记录 CRUD ─────────────────────────────────────────


@router.get("/ipr/registrations", response_model=ApiResponse[list])
def list_ip_registrations(
    ip_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取 IP 登记列表 (支持 ip_type/jurisdiction/status 过滤)."""
    query = db.query(IPRegistration)
    if ip_type:
        query = query.filter(IPRegistration.ip_type == ip_type)
    if jurisdiction:
        query = query.filter(IPRegistration.jurisdiction == jurisdiction)
    if status:
        query = query.filter(IPRegistration.status == status)

    records = query.order_by(IPRegistration.created_at.desc()).all()

    return ApiResponse(data=[
        {
            "id": r.id, "work_id": r.work_id, "ip_type": r.ip_type,
            "jurisdiction": r.jurisdiction,
            "application_no": r.application_no, "registration_no": r.registration_no,
            "filing_date": r.filing_date.isoformat() if r.filing_date else None,
            "registration_date": r.registration_date.isoformat() if r.registration_date else None,
            "expiration_date": r.expiration_date.isoformat() if r.expiration_date else None,
            "next_action_date": r.next_action_date.isoformat() if r.next_action_date else None,
            "next_action_type": r.next_action_type,
            "status": r.status, "category_info": r.category_info,
            "official_fee": r.official_fee, "total_cost": r.total_cost,
            "agent_name": r.agent_name, "agent_fee": r.agent_fee,
            "official_url": r.official_url,
            "notes": r.notes, "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ])


@router.post("/ipr/registrations", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_ip_registration(data: CreateIPRegistrationPayload, db: Session = Depends(get_db)):
    """创建 IP 登记记录."""
    record = IPRegistration(
        work_id=data.work_id,
        ip_type=data.ip_type,
        jurisdiction=data.jurisdiction,
        application_no=data.application_no,
        registration_no=data.registration_no,
        filing_date=_parse_date(data.filing_date),
        registration_date=_parse_date(data.registration_date),
        expiration_date=_parse_date(data.expiration_date),
        next_action_date=_parse_date(data.next_action_date),
        next_action_type=data.next_action_type,
        status=data.status,
        category_info=data.category_info,
        official_fee=data.official_fee,
        total_cost=data.total_cost,
        agent_name=data.agent_name,
        agent_fee=data.agent_fee,
        official_url=data.official_url,
        notes=data.notes,
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except SQLAlchemyError:
        db.rollback()
        raise
    return ApiResponse(message="IP 登记记录已创建", data={"id": record.id})


@router.get("/ipr/registrations/{record_id}", response_model=ApiResponse)
def get_ip_registration(record_id: str, db: Session = Depends(get_db)):
    """获取 IP 登记记录详情."""
    record = db.query(IPRegistration).filter(IPRegistration.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 获取时间线
    timeline = _build_timeline(record)

    return ApiResponse(data={
        "id": record.id, "work_id": record.work_id, "ip_type": record.ip_type,
        "jurisdiction": record.jurisdiction,
        "application_no": record.application_no, "registration_no": record.registration_no,
        "filing_date": record.filing_date.isoformat() if record.filing_date else None,
        "registration_date": record.registration_date.isoformat() if record.registration_date else None,
        "expiration_date": record.expiration_date.isoformat() if record.expiration_date else None,
        "next_action_date": record.next_action_date.isoformat() if record.next_action_date else None,
        "next_action_type": record.next_action_type,
        "status": record.status, "category_info": record.category_info,
        "official_fee": record.official_fee, "total_cost": record.total_cost,
        "agent_name": record.agent_name, "agent_fee": record.agent_fee,
        "official_url": record.official_url,
        "notes": record.notes,
        "timeline": timeline,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    })


@router.patch("/ipr/registrations/{record_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_ip_registration(record_id: str, data: UpdateIPRegistrationPayload, db: Session = Depends(get_db)):
    """更新 IP 登记进度 (P1.7.14: 状态变更时推送通知)."""
    record = db.query(IPRegistration).filter(IPRegistration.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    old_status = record.status

    update_data = data.model_dump(exclude_unset=True)

    # Parse date fields
    for key in ["filing_date", "registration_date", "expiration_date"]:
        if key in update_data and update_data[key] is not None:
            setattr(record, key, _parse_date(update_data[key]))
            # Remove from update_data so they're not set as strings
            update_data.pop(key, None)

    for key, value in update_data.items():
        setattr(record, key, value)

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    # P1.7.14: Push notification on status change
    new_status = update_data.get("status")
    if new_status and new_status != old_status:
        try:
            from app.routers.system import push_notification
            status_labels = {
                "draft": "草稿", "filed": "已提交", "under_review": "审查中",
                "registered": "已注册", "rejected": "已驳回", "expired": "已过期",
            }
            old_label = status_labels.get(old_status, old_status)
            new_label = status_labels.get(new_status, new_status)
            ip_type_labels = {
                "copyright": "版权", "trademark": "商标",
                "design_patent": "外观设计", "utility_patent": "专利",
            }
            ip_label = ip_type_labels.get(record.ip_type, record.ip_type)
            push_notification(
                db, user_id="default",
                type="ipr_update",
                title=f"{ip_label}登记状态更新",
                content=f"{ip_label}登记「{record.application_no or record.id[:8]}」状态从「{old_label}」变更为「{new_label}」。",
                related_module="ipr",
                related_id=record.id,
            )
        except Exception as e:
            logging.getLogger(__name__).exception("Error in update_ip_registration_status: %s", str(e))

    return ApiResponse(message="已更新")


@router.delete("/ipr/registrations/{record_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_ip_registration(record_id: str, db: Session = Depends(get_db)):
    """删除 IP 登记记录."""
    record = db.query(IPRegistration).filter(IPRegistration.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return ApiResponse(message="已删除")


# ─── 指引内容 ──────────────────────────────────────────────────


@router.get("/ipr/guidelines", response_model=ApiResponse)
def get_ipr_guidelines(jurisdiction: Optional[str] = None):
    """获取 IP 登记指引 (P2.4: 支持多辖区)."""
    all_guidelines = {
        "cn": {
            "copyright": COPYRIGHT_GUIDELINES_CN,
            "trademark": TRADEMARK_GUIDELINES_CN,
            "design_patent": DESIGN_GUIDELINES_CN,
        },
        "us": {
            "copyright": COPYRIGHT_GUIDELINES_US,
            "trademark": {
                "title": "美国商标注册指引 (USPTO)",
                "description": "美国商标须实际使用或意图使用。通过USPTO TEAS系统在线申请, 费用$250-$350/类。",
                "disclaimer": "本工具仅提供信息指引，不构成法律建议。",
                "legal_basis": "Lanham Act (15 U.S.C. §§ 1051 et seq.)",
                "institution": "USPTO (美国专利商标局)",
                "platform_url": "https://www.uspto.gov/trademarks",
                "fee": "$250/类 (TEAS Plus) / $350/类 (TEAS Standard)",
                "estimated_duration": "9-14个月",
                "validity": "有效期10年, 第5-6年需提交使用声明(§8 Declaration), 续展10年",
                "materials": [
                    {"name": "TEAS申请表", "required": True, "description": "在线填写TEAS Plus或TEAS Standard申请", "can_prefill": True},
                    {"name": "商标图样", "required": True, "description": "JPG格式, 标准字符或特殊形式商标", "can_prefill": False},
                    {"name": "使用样本(Specimen)", "required": False, "description": "使用基础(1a): 需提交商标在商品/服务上实际使用的样本", "can_prefill": False},
                    {"name": "申请人信息", "required": True, "description": "个人/企业名称、地址、实体类型", "can_prefill": False},
                ],
                "process": [
                    {"step": 1, "name": "商标检索", "description": "通过TESS系统检索现有商标", "duration": "自行安排"},
                    {"step": 2, "name": "选择申请基础", "description": "实际使用(1a)或意图使用(1b)", "duration": "即时"},
                    {"step": 3, "name": "在线提交TEAS", "description": "通过USPTO TEAS系统提交", "duration": "约1小时"},
                    {"step": 4, "name": "审查", "description": "USPTO审查律师审查 (约3-6个月后开始)", "duration": "约3-4个月"},
                    {"step": 5, "name": "公告", "description": "审查通过后在Official Gazette公告30天", "duration": "30天"},
                    {"step": 6, "name": "注册/NOA", "description": "1a基础→注册; 1b基础→准许通知(NOA)", "duration": "约2个月"},
                ],
            },
        },
        "eu": {
            "trademark": TRADEMARK_GUIDELINES_EU,
            "design_patent": {
                "title": "欧盟外观设计注册 (RCD)",
                "description": "注册式共同体外观设计(RCD)通过EUIPO一次注册在27个欧盟成员国获得保护。",
                "disclaimer": "本工具仅提供信息指引，不构成法律建议。",
                "institution": "EUIPO",
                "platform_url": "https://www.euipo.europa.eu",
                "fee": "€350起 (1项设计), 第2-10项€175/项",
                "estimated_duration": "约1-2周 (无实质审查)",
                "validity": "有效期5年, 可续展4次, 最长25年",
            },
            "sme_fund": EUIPO_SME_FUND_GUIDE,
        },
        "wipo": {
            "trademark": TRADEMARK_GUIDELINES_WIPO,
            "design_patent": DESIGN_GUIDELINES_WIPO_HAGUE,
        },
        "jp": {
            "trademark": TRADEMARK_GUIDELINES_JP,
        },
        "kr": {
            "trademark": TRADEMARK_GUIDELINES_KR,
        },
    }

    if jurisdiction and jurisdiction in all_guidelines:
        return ApiResponse(data={
            "jurisdiction": jurisdiction,
            "guidelines": all_guidelines[jurisdiction],
            "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有IP申请须由权利人自行向官方机构提交。",
        })

    return ApiResponse(data={
        "guidelines": all_guidelines,
        "categories": COMMON_CATEGORIES,
        "disclaimer": "本工具仅提供信息指引，不构成法律建议。所有IP申请须由权利人自行向官方机构提交。",
    })


@router.get("/ipr/guidelines/{ip_type}", response_model=ApiResponse)
def get_ipr_guidelines_by_type(
    ip_type: str,
    jurisdiction: str = "cn",
):
    """获取特定 IP 类型的详细指引 (P2.4: 支持多辖区)."""
    guidelines_map = {
        ("copyright", "cn"): COPYRIGHT_GUIDELINES_CN,
        ("copyright", "us"): COPYRIGHT_GUIDELINES_US,
        ("trademark", "cn"): TRADEMARK_GUIDELINES_CN,
        ("trademark", "eu"): TRADEMARK_GUIDELINES_EU,
        ("trademark", "wipo"): TRADEMARK_GUIDELINES_WIPO,
        ("trademark", "jp"): TRADEMARK_GUIDELINES_JP,
        ("trademark", "kr"): TRADEMARK_GUIDELINES_KR,
        ("design_patent", "cn"): DESIGN_GUIDELINES_CN,
        ("design_patent", "wipo"): DESIGN_GUIDELINES_WIPO_HAGUE,
    }
    result = guidelines_map.get((ip_type, jurisdiction))
    if result:
        return ApiResponse(data=result)
    raise HTTPException(status_code=404, detail=f"暂不支持 {ip_type}/{jurisdiction} 的详细指引")


# ─── 类别推荐 ──────────────────────────────────────────────────


@router.get("/ipr/nice-classes", response_model=ApiResponse)
def list_nice_classes(
    creative_only: bool = False,
    db: Session = Depends(get_db),
):
    """获取尼斯分类列表."""
    _seed_nice_classes(db)
    query = db.query(NiceClassification)
    if creative_only:
        query = query.filter(NiceClassification.is_creative_relevant == True)
    results = query.order_by(NiceClassification.class_no).all()
    return ApiResponse(data=[
        {
            "id": c.id, "class_no": c.class_no,
            "class_name_zh": c.class_name_zh, "class_name_en": c.class_name_en,
            "goods_services": c.goods_services,
            "is_creative_relevant": c.is_creative_relevant,
            "common_for_creators": c.common_for_creators,
        }
        for c in results
    ])


@router.get("/ipr/nice-classes/{class_no}/goods", response_model=ApiResponse)
def get_class_goods(class_no: int, db: Session = Depends(get_db)):
    """获取指定类别的规范商品/服务项目."""
    _seed_nice_classes(db)
    cls = db.query(NiceClassification).filter(NiceClassification.class_no == class_no).first()
    if not cls:
        raise HTTPException(status_code=404, detail=f"第{class_no}类不存在")
    return ApiResponse(data={
        "class_no": cls.class_no,
        "class_name_zh": cls.class_name_zh,
        "goods_services": cls.goods_services,
        "common_for_creators": cls.common_for_creators,
    })


@router.post("/ipr/recommend/classes", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def recommend_classes(data: RecommendClassesPayload, db: Session = Depends(get_db)):
    """基于作品标签/描述推荐商标类别 (P1.4.3, 合规修订: 多推荐+置信度, 最少3条)."""
    _seed_nice_classes(db)

    tags = data.tags
    description = data.description
    creator_type = data.creator_type

    # 从标签匹配 (关键词→类别+置信度)
    matched: dict = {}  # class_no -> confidence_score
    for tag in tags:
        tag_lower = tag.lower()
        for kw, classes in TAG_TO_CLASS_MAP.items():
            if kw.lower() in tag_lower or tag_lower in kw.lower():
                for c in classes:
                    matched[c] = max(matched.get(c, 0), 70)

    # 从描述匹配 (较低置信度)
    if description:
        desc_lower = description.lower()
        for kw, classes in TAG_TO_CLASS_MAP.items():
            if kw.lower() in desc_lower:
                for c in classes:
                    if c not in matched:
                        matched[c] = 50

    # 从创作者类型追加推荐 (低置信度)
    if creator_type and creator_type in CREATOR_STRATEGIES:
        strategy = CREATOR_STRATEGIES[creator_type]
        for c in strategy["classes"]:
            if c not in matched:
                matched[c] = 30

    # 最少3条底线 (合规要求: 不可只返回一条)
    if len(matched) < 3:
        fallback_classes = {16: 20, 35: 20, 41: 20, 25: 15, 21: 15, 28: 15, 42: 15, 9: 10}
        for c, default_conf in fallback_classes.items():
            if c not in matched and len(matched) < 8:
                matched[c] = default_conf

    # 查询尼斯分类数据
    nice_map = {
        c.class_no: c
        for c in db.query(NiceClassification).filter(
            NiceClassification.class_no.in_(list(matched.keys()))
        ).all()
    }

    recommendations = []
    for class_no, confidence in matched.items():
        nc = nice_map.get(class_no)
        desc = COMMON_CATEGORIES.get(str(class_no), "")

        if nc:
            name = nc.class_name_zh
        else:
            name = desc.split("、")[0] if desc else f"第{class_no}类"

        # 置信度分级
        if confidence >= 70:
            level = "high"
        elif confidence >= 40:
            level = "medium"
        else:
            level = "low"

        recommendations.append({
            "class_no": class_no,
            "class_name_zh": name,
            "confidence": confidence,
            "confidence_level": level,
            "reason": desc,
            "fee_estimate": 300,
        })

    recommendations.sort(key=lambda x: (-x["confidence"], x["class_no"]))

    total_fee = len(recommendations) * 300

    return ApiResponse(data={
        "recommendations": recommendations,
        "estimated_total_fee": total_fee,
        "disclaimer": "以上为基于作品信息的类别可能性分析, 不构成法律建议。最终注册类别应与持证商标律师确认。",
        "recommended_next_step": "联系律师审核类别选择",
    })


@router.get("/ipr/recommend/strategies", response_model=ApiResponse)
def get_recommend_strategies():
    """获取按创作者类型的预定义组合策略."""
    return ApiResponse(data=[
        {
            "key": k,
            "label": v["label"],
            "classes": v["classes"],
            "note": v["note"],
        }
        for k, v in CREATOR_STRATEGIES.items()
    ])


# ─── P2.4.8-P2.4.9: 申请表模板 ─────────────────────────────────


@router.get("/ipr/templates", response_model=ApiResponse)
def get_application_templates(
    ip_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取申请表模板列表 (P2.4.8)."""
    _seed_application_templates(db)
    query = db.query(ApplicationTemplate).filter(ApplicationTemplate.is_active == True)
    if ip_type:
        query = query.filter(ApplicationTemplate.ip_type == ip_type)
    if jurisdiction:
        query = query.filter(ApplicationTemplate.jurisdiction == jurisdiction)
    results = query.order_by(ApplicationTemplate.jurisdiction, ApplicationTemplate.ip_type).all()
    return ApiResponse(data=[
        {
            "id": t.id,
            "ip_type": t.ip_type,
            "jurisdiction": t.jurisdiction,
            "template_name": t.template_name,
            "template_version": t.template_version,
            "form_schema": t.form_schema,
            "field_mappings": t.field_mappings,
            "validation_rules": t.validation_rules,
            "fee_schedule": t.fee_schedule,
            "required_documents": t.required_documents,
            "official_submission_url": t.official_submission_url,
            "official_guide_url": t.official_guide_url,
            "estimated_duration": t.estimated_duration,
            "legal_basis": t.legal_basis,
        }
        for t in results
    ])


@router.get("/ipr/templates/{template_id}", response_model=ApiResponse)
def get_application_template(template_id: str, db: Session = Depends(get_db)):
    """获取单个申请表模板详情 (P2.4.9)."""
    _seed_application_templates(db)
    t = db.query(ApplicationTemplate).filter(ApplicationTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="模板不存在")
    return ApiResponse(data={
        "id": t.id,
        "ip_type": t.ip_type,
        "jurisdiction": t.jurisdiction,
        "template_name": t.template_name,
        "template_version": t.template_version,
        "form_schema": t.form_schema,
        "field_mappings": t.field_mappings,
        "validation_rules": t.validation_rules,
        "fee_schedule": t.fee_schedule,
        "required_documents": t.required_documents,
        "official_submission_url": t.official_submission_url,
        "official_guide_url": t.official_guide_url,
        "estimated_duration": t.estimated_duration,
        "legal_basis": t.legal_basis,
    })


# ─── 智能申请助手 ─────────────────────────────────────────────


@router.post("/ipr/assistant/prefill", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def prefill_application(data: PrefillApplicationPayload, db: Session = Depends(get_db)):
    """从作品数据预填申请表单 (P1.4.5-1.4.9)."""
    work_id = data.work_id
    ip_type = data.ip_type
    jurisdiction = data.jurisdiction

    if not work_id:
        raise HTTPException(status_code=400, detail="work_id 是必填项")

    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    # 获取作品标签
    tags = [t.tag for t in db.query(WorkTag).filter(WorkTag.work_id == work_id).all()]

    # 获取最新存证记录
    notary = db.query(NotaryRecord).filter(
        NotaryRecord.work_id == work_id,
        NotaryRecord.status == "confirmed",
    ).order_by(NotaryRecord.confirmed_at.desc()).first()

    fields = []
    missing = []

    if ip_type == "copyright":
        fields = _prefill_copyright(work, tags, notary)
    elif ip_type == "trademark":
        fields = _prefill_trademark(work, tags)
    else:
        fields = _prefill_generic(work, tags)

    # 计算完整度
    total_required = sum(1 for f in fields if f["required"])
    filled_required = sum(1 for f in fields if f["required"] and f["value"] is not None and f["value"] != "")
    completeness = int((filled_required / total_required * 100)) if total_required > 0 else 100
    missing = [f["official_field"] for f in fields if f["required"] and (f["value"] is None or f["value"] == "")]

    return ApiResponse(data={
        "work_title": work.title,
        "ip_type": ip_type,
        "jurisdiction": jurisdiction,
        "fields": fields,
        "completeness": completeness,
        "missing_fields": missing,
    })


@router.post("/ipr/assistant/validate", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def validate_application(data: ValidateApplicationPayload):
    """校验申请表单完整性和格式."""
    ip_type = data.ip_type
    fields_data = data.fields

    issues = []
    required_fields = []

    if ip_type == "copyright":
        required_fields = [
            "作品名称", "作品类别", "作者姓名", "创作完成日期", "创作说明",
        ]
    elif ip_type == "trademark":
        required_fields = [
            "商标名称", "申请人名称", "申请人地址", "商品/服务类别",
        ]

    for field in required_fields:
        val = fields_data.get(field, "")
        if not val or (isinstance(val, str) and val.strip() == ""):
            issues.append({
                "field": field, "level": "error",
                "message": f"{field} 为必填项",
            })

    # 日期校验
    completion_date = fields_data.get("创作完成日期")
    if completion_date:
        try:
            d = date.fromisoformat(completion_date)
            if d > date.today():
                issues.append({
                    "field": "创作完成日期", "level": "error",
                    "message": "创作完成日期不能晚于今天",
                })
        except (ValueError, TypeError):
            issues.append({
                "field": "创作完成日期", "level": "error",
                "message": "日期格式无效，应为 YYYY-MM-DD",
            })

    # 创作说明字数提示
    synopsis = fields_data.get("创作说明", "")
    if synopsis and isinstance(synopsis, str):
        if len(synopsis) < 50:
            issues.append({
                "field": "创作说明", "level": "warning",
                "message": f"创作说明当前{len(synopsis)}字, 建议50-500字",
            })
        elif len(synopsis) > 500:
            issues.append({
                "field": "创作说明", "level": "warning",
                "message": f"创作说明当前{len(synopsis)}字, 建议不超过500字",
            })

    error_count = sum(1 for i in issues if i["level"] == "error")
    valid = error_count == 0

    total_field_count = max(len(required_fields), len(fields_data), 1)
    filled = sum(
        1 for k in required_fields
        if k in fields_data and fields_data[k] and str(fields_data[k]).strip()
    )
    completeness = int(filled / total_field_count * 100)

    return ApiResponse(data={
        "valid": valid,
        "completeness": completeness,
        "issues": issues,
    })


@router.post("/ipr/assistant/generate", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def generate_application(data: GenerateApplicationPayload):
    """生成申请表信息(不实际生成PDF, 返回预览数据)."""
    ip_type = data.ip_type
    jurisdiction = data.jurisdiction
    fields = data.fields

    # 构造预览数据
    preview = {
        "ip_type": ip_type,
        "jurisdiction": jurisdiction,
        "fields": fields,
        "generated_at": datetime.utcnow().isoformat(),
        "disclaimer": "本申请表为系统自动预填，请核对无误后通过官方平台提交。本工具不构成法律建议。",
    }

    if ip_type == "copyright":
        preview["form_title"] = "作品登记申请表"
        preview["official_url"] = "https://www.ccopyright.com.cn"
    elif ip_type == "trademark":
        preview["form_title"] = "商标注册申请书"
        preview["official_url"] = "https://sbj.cnipa.gov.cn"

    return ApiResponse(data=preview)


@router.post("/ipr/assistant/export", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def export_application(data: ExportApplicationPayload, db: Session = Depends(get_db)):
    """导出申请材料预览(不实际生成ZIP, 返回清单).

    P3 UPL合规: 必须记录 lawyer_consulted 选择 (A/B/C).
    强制要求: 未完成律师审核确认(A或B)禁止导出.
    """
    ip_type = data.ip_type
    jurisdiction = data.jurisdiction
    lawyer_consulted = data.lawyer_consulted  # A/B/C

    # Mandatory: lawyer consultation confirmation required before export
    if not lawyer_consulted or lawyer_consulted not in ("A", "B"):
        raise HTTPException(
            status_code=403,
            detail="必须先完成律师审核确认才能导出申请材料",
        )

    if ip_type == "copyright":
        materials = COPYRIGHT_GUIDELINES_CN["materials"]
    else:
        materials = TRADEMARK_GUIDELINES_CN["materials"]

    checklist = []
    for m in materials:
        checklist.append({
            "name": m["name"],
            "required": m["required"],
            "status": "prepared" if m.get("can_prefill") else "requires_manual",
            "description": m["description"],
        })

    return ApiResponse(data={
        "ip_type": ip_type,
        "jurisdiction": jurisdiction,
        "lawyer_consulted": lawyer_consulted,
        "checklist": checklist,
        "disclaimer": "请核对材料清单后将所有文件通过官方平台提交。本工具不代提交申请。",
    })


# ─── P1.4.8: Application package ZIP export ─────────────────


@router.post("/ipr/registrations/{record_id}/export-package", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def export_application_package(record_id: str, db: Session = Depends(get_db)):
    """P1.4.8: 生成申请材料 ZIP 包.

    包含:
      - application_form.pdf (预填申请表占位)
      - materials_checklist.pdf (材料清单)
      - fee_summary.pdf (费用汇总)
      - official_links.txt (官方提交链接和说明)
    """
    record = db.query(IPRegistration).filter(IPRegistration.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    ip_type = record.ip_type
    jurisdiction = record.jurisdiction

    # 获取对应的指南数据
    guidelines_map = {
        ("copyright", "cn"): COPYRIGHT_GUIDELINES_CN,
        ("copyright", "us"): COPYRIGHT_GUIDELINES_US,
        ("trademark", "cn"): TRADEMARK_GUIDELINES_CN,
        ("trademark", "eu"): TRADEMARK_GUIDELINES_EU,
        ("trademark", "wipo"): TRADEMARK_GUIDELINES_WIPO,
        ("trademark", "jp"): TRADEMARK_GUIDELINES_JP,
        ("trademark", "kr"): TRADEMARK_GUIDELINES_KR,
        ("design_patent", "cn"): DESIGN_GUIDELINES_CN,
        ("design_patent", "wipo"): DESIGN_GUIDELINES_WIPO_HAGUE,
    }
    guidelines = guidelines_map.get((ip_type, jurisdiction))
    if not guidelines:
        guidelines = COPYRIGHT_GUIDELINES_CN  # default fallback

    # Build materials checklist
    materials = guidelines.get("materials", [])
    checklist = []
    for m in materials:
        checklist.append({
            "name": m["name"],
            "required": m["required"],
            "status": "prepared" if m.get("can_prefill") else "requires_manual",
            "description": m.get("description", ""),
        })

    # Fee summary
    fee_summary = {
        "official_fee": record.official_fee or 0,
        "agent_fee": record.agent_fee or 0,
        "total_cost": record.total_cost or 0,
        "fee_notes": guidelines.get("fee", {}),
        "currency_notes": "官方费用须由申请人直接支付给官方机构。本工具不代收任何费用。",
    }

    # Official links
    official_links = {
        "institution": guidelines.get("institution", ""),
        "platform_url": guidelines.get("platform_url", ""),
        "estimated_duration": guidelines.get("estimated_duration", ""),
        "validity": guidelines.get("validity", ""),
        "legal_basis": guidelines.get("legal_basis", ""),
        "process": guidelines.get("process", []),
        "disclaimer": guidelines.get("disclaimer", "本工具仅提供信息指引，不构成法律建议。"),
    }

    # Generate ZIP in memory
    import io
    import zipfile

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # application_form.pdf placeholder
        form_content = _generate_form_text(record, ip_type, jurisdiction, guidelines)
        zf.writestr("application_form.txt", form_content)

        # materials_checklist.pdf placeholder
        checklist_content = _generate_checklist_text(checklist, ip_type, jurisdiction)
        zf.writestr("materials_checklist.txt", checklist_content)

        # fee_summary.pdf placeholder
        fee_content = _generate_fee_summary_text(fee_summary)
        zf.writestr("fee_summary.txt", fee_content)

        # official_links.txt
        links_content = _generate_links_text(official_links, ip_type, jurisdiction)
        zf.writestr("official_links.txt", links_content)

    zip_buffer.seek(0)
    zip_b64 = __import__("base64").b64encode(zip_buffer.getvalue()).decode("utf-8")

    return ApiResponse(data={
        "record_id": record_id,
        "ip_type": ip_type,
        "jurisdiction": jurisdiction,
        "package_contents": [
            "application_form.txt", "materials_checklist.txt",
            "fee_summary.txt", "official_links.txt",
        ],
        "zip_data_base64": zip_b64,
        "note": "完整 PDF 生成需要部署 PDF 渲染服务。当前返回 TXT 格式的申请材料内容预览。",
        "disclaimer": guidelines.get("disclaimer", "本工具仅提供信息指引，不构成法律建议。"),
    })


def _generate_form_text(record, ip_type, jurisdiction, guidelines):
    """Generate application form text content."""
    lines = [
        f"=== {guidelines.get('title', 'IP Registration Application')} ===",
        f"IP Type: {ip_type}",
        f"Jurisdiction: {jurisdiction}",
        f"Application No: {record.application_no or '(待分配)'}",
        f"Filing Date: {record.filing_date.isoformat() if record.filing_date else '(待填写)'}",
        f"Status: {record.status}",
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
        "--- 申请人信息 ---",
        "(请手动填写)",
        "姓名/名称: _______________",
        "地址: _______________",
        "联系方式: _______________",
        "",
        "--- 作品/商标信息 ---",
        f"类别: {record.category_info or '(请填写)'}",
        f"备注: {record.notes or '(无)'}",
        "",
        f"--- 费用 ---",
        f"官费: {record.official_fee or 0}",
        f"代理费: {record.agent_fee or 0}",
        f"合计: {record.total_cost or 0}",
        "",
        f"平台: {guidelines.get('platform_url', '')}",
        f"机构: {guidelines.get('institution', '')}",
        "",
        "=== DISCLAIMER ===",
        guidelines.get("disclaimer", ""),
    ]
    return "\n".join(lines)


def _generate_checklist_text(checklist, ip_type, jurisdiction):
    """Generate materials checklist text."""
    lines = [
        f"=== Materials Checklist ({ip_type}/{jurisdiction}) ===",
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
    ]
    for idx, item in enumerate(checklist, 1):
        status_icon = "[x]" if item["status"] == "prepared" else "[ ]"
        lines.append(f"{idx}. {status_icon} {item['name']} - {'必填' if item['required'] else '选填'}")
        lines.append(f"   {item['description']}")
        lines.append("")
    return "\n".join(lines)


def _generate_fee_summary_text(fee_summary):
    """Generate fee summary text."""
    lines = [
        "=== Fee Summary ===",
        f"Official Fee: {fee_summary['official_fee']}",
        f"Agent Fee: {fee_summary['agent_fee']}",
        f"Total Cost: {fee_summary['total_cost']}",
        "",
        "--- Official Fee Schedule ---",
    ]
    fees = fee_summary.get("fee_notes", {})
    if isinstance(fees, dict):
        for k, v in fees.items():
            lines.append(f"  {k}: {v}")
    elif isinstance(fees, str):
        lines.append(f"  {fees}")
    lines.append("")
    lines.append(f"Note: {fee_summary.get('currency_notes', '')}")
    return "\n".join(lines)


def _generate_links_text(official_links, ip_type, jurisdiction):
    """Generate official links text."""
    lines = [
        "=== Official Links & Guidance ===",
        f"IP Type: {ip_type}",
        f"Jurisdiction: {jurisdiction}",
        f"Institution: {official_links.get('institution', '')}",
        f"Platform URL: {official_links.get('platform_url', '')}",
        f"Estimated Duration: {official_links.get('estimated_duration', '')}",
        f"Validity Period: {official_links.get('validity', '')}",
        f"Legal Basis: {official_links.get('legal_basis', '')}",
        "",
        "--- Application Process ---",
    ]
    process = official_links.get("process", [])
    for step in process:
        name = step.get("name", "")
        desc = step.get("description", "")
        dur = step.get("duration", "")
        lines.append(f"  Step {step.get('step', '?')}: {name} ({dur})")
        lines.append(f"    {desc}")
    lines.append("")
    lines.append("--- Disclaimer ---")
    lines.append(official_links.get("disclaimer", ""))
    return "\n".join(lines)
# ─── IP 资产仪表盘 ────────────────────────────────────────────


@router.get("/ipr/portfolio", response_model=ApiResponse)
def get_ip_portfolio(db: Session = Depends(get_db)):
    """IP 资产组合总览 (P1.4.10)."""
    all_records = db.query(IPRegistration).all()

    # 按类型统计
    by_type = {}
    for r in all_records:
        by_type.setdefault(r.ip_type, {"total": 0, "by_status": {}})
        by_type[r.ip_type]["total"] += 1
        by_type[r.ip_type]["by_status"].setdefault(r.status, 0)
        by_type[r.ip_type]["by_status"][r.status] += 1

    type_labels = {
        "copyright": "版权",
        "trademark": "商标",
        "design_patent": "外观设计",
        "utility_patent": "专利",
    }
    stats = []
    for ip_type, label in type_labels.items():
        data = by_type.get(ip_type, {"total": 0, "by_status": {}})
        stats.append({
            "ip_type": ip_type,
            "label": label,
            "total": data["total"],
            "by_status": data["by_status"],
        })

    # 计算到期提醒
    today = date.today()
    renewals = _calculate_renewals(all_records, today)

    total_ips = len(all_records)
    registered_count = sum(1 for r in all_records if r.status == "registered")
    pending_count = sum(1 for r in all_records if r.status in ("draft", "filed", "under_review"))

    # 按辖区统计
    by_jurisdiction = {}
    for r in all_records:
        by_jurisdiction.setdefault(r.jurisdiction, 0)
        by_jurisdiction[r.jurisdiction] += 1

    # 年度费用预估
    total_annual_cost = sum(
        r.total_cost or r.official_fee or 0 for r in all_records
        if r.status in ("registered", "filed", "under_review")
    )

    return ApiResponse(data={
        "stats": stats,
        "renewals": renewals,
        "total_ips": total_ips,
        "registered_count": registered_count,
        "pending_count": pending_count,
        "by_jurisdiction": by_jurisdiction,
        "total_annual_cost": total_annual_cost,
    })


@router.get("/ipr/reminders", response_model=ApiResponse)
def get_reminders(db: Session = Depends(get_db)):
    """到期提醒列表 (P1.4.11)."""
    all_records = db.query(IPRegistration).filter(
        IPRegistration.status.in_(["registered", "filed", "under_review"])
    ).all()

    today = date.today()
    reminders = _calculate_renewals(all_records, today)

    # 分类
    urgent = [r for r in reminders if r["urgency"] == "red"]
    upcoming = [r for r in reminders if r["urgency"] == "orange"]
    future = [r for r in reminders if r["urgency"] == "yellow"]

    return ApiResponse(data={
        "urgent": urgent,
        "upcoming": upcoming,
        "future": future,
        "total": len(reminders),
        "next_reminder_date": min(
            [r["next_action_date"] for r in reminders if r["next_action_date"]],
            default=None,
        ),
    })


@router.get("/ipr/dashboard", response_model=ApiResponse)
def get_ip_dashboard(db: Session = Depends(get_db)):
    """IP 仪表盘汇总数据 (P1.4.10 增强).

    包含:
    - per-type counts (with status breakdown)
    - per-jurisdiction breakdown
    - total fees paid (total cost across all records)
    - next actions due (upcoming renewals)
    - registered count, pending count
    """
    all_records = db.query(IPRegistration).all()
    today = date.today()

    # Type labels
    type_labels = {
        "copyright": "版权", "trademark": "商标",
        "design_patent": "外观设计", "utility_patent": "专利",
        "invention_patent": "发明专利",
    }
    jurisdiction_labels = {
        "cn": "中国", "us": "美国", "eu": "欧盟",
        "jp": "日本", "kr": "韩国", "wipo": "WIPO",
    }

    # Per-type counts with status breakdown
    by_type = {}
    for r in all_records:
        if r.ip_type not in by_type:
            by_type[r.ip_type] = {
                "label": type_labels.get(r.ip_type, r.ip_type),
                "total": 0,
                "by_status": {},
            }
        by_type[r.ip_type]["total"] += 1
        by_type[r.ip_type]["by_status"][r.status] = by_type[r.ip_type]["by_status"].get(r.status, 0) + 1

    # Per-status
    by_status = {}
    for r in all_records:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    # Per-jurisdiction breakdown with status
    by_jurisdiction = {}
    for r in all_records:
        if r.jurisdiction not in by_jurisdiction:
            by_jurisdiction[r.jurisdiction] = {
                "label": jurisdiction_labels.get(r.jurisdiction, r.jurisdiction),
                "total": 0,
                "by_type": {},
            }
        by_jurisdiction[r.jurisdiction]["total"] += 1
        by_jurisdiction[r.jurisdiction]["by_type"][r.ip_type] = \
            by_jurisdiction[r.jurisdiction]["by_type"].get(r.ip_type, 0) + 1

    # Total fees paid (sum of total_cost across all records)
    total_fees_paid = sum(r.total_cost or 0 for r in all_records)
    total_official_fee = sum(r.official_fee or 0 for r in all_records)
    total_agent_fee = sum(r.agent_fee or 0 for r in all_records)

    # Next actions due (upcoming renewals)
    renewals = _calculate_renewals(all_records, today)
    urgent_renewals = [r for r in renewals if r["urgency"] == "red"]
    upcoming_renewals = [r for r in renewals if r["urgency"] == "orange"]

    return ApiResponse(data={
        "total": len(all_records),
        "by_type": by_type,
        "by_status": by_status,
        "by_jurisdiction": by_jurisdiction,
        "fees": {
            "total_paid": total_fees_paid,
            "official_fee_total": total_official_fee,
            "agent_fee_total": total_agent_fee,
        },
        "next_actions": {
            "urgent_actions": urgent_renewals,
            "upcoming_actions": upcoming_renewals,
            "total_urgent": len(urgent_renewals),
            "total_upcoming": len(upcoming_renewals),
            "next_action_date": min(
                [r["next_action_date"] for r in renewals if r["next_action_date"]],
                default=None,
            ),
        },
        "type_labels": type_labels,
        "jurisdiction_labels": jurisdiction_labels,
    })


# ─── 全局路径信息 ──────────────────────────────────────────────


@router.get("/ipr/paths", response_model=ApiResponse)
def get_ipr_paths():
    """获取所有 IP 保护路径 (P2.4: 全球覆盖)."""
    return ApiResponse(data={
        "copyright": {
            "label": "版权",
            "jurisdictions": [
                {
                    "code": "cn", "label": "中国", "flag": "🇨🇳",
                    "fee": "¥0-300", "duration": "30工作日",
                    "url": "https://www.ccopyright.com.cn",
                },
                {
                    "code": "us", "label": "美国 (USCO)", "flag": "🇺🇸",
                    "fee": "$45-125", "duration": "1-7个月",
                    "url": "https://www.copyright.gov",
                },
            ],
        },
        "trademark": {
            "label": "商标",
            "jurisdictions": [
                {
                    "code": "cn", "label": "中国 (CNIPA)", "flag": "🇨🇳",
                    "fee": "¥300/类", "duration": "6-12月",
                    "url": "https://sbj.cnipa.gov.cn",
                },
                {
                    "code": "us", "label": "美国 (USPTO)", "flag": "🇺🇸",
                    "fee": "$250-350/类", "duration": "9-14月",
                    "url": "https://www.uspto.gov/trademarks",
                },
                {
                    "code": "eu", "label": "欧盟 (EUIPO)", "flag": "🇪🇺",
                    "fee": "€850起/1类", "duration": "4-6月",
                    "url": "https://www.euipo.europa.eu",
                },
                {
                    "code": "wipo", "label": "WIPO 马德里", "flag": "🌐",
                    "fee": "CHF 653起", "duration": "12-18月",
                    "url": "https://www.wipo.int/madrid",
                },
                {
                    "code": "jp", "label": "日本 (JPO)", "flag": "🇯🇵",
                    "fee": "¥12,000/类", "duration": "6-12月",
                    "url": "https://www.jpo.go.jp",
                },
                {
                    "code": "kr", "label": "韩国 (KIPO)", "flag": "🇰🇷",
                    "fee": "₩56,000/类", "duration": "6-10月",
                    "url": "https://www.kipo.go.kr",
                },
            ],
        },
        "design_patent": {
            "label": "外观设计",
            "jurisdictions": [
                {
                    "code": "cn", "label": "中国 (CNIPA)", "flag": "🇨🇳",
                    "fee": "¥500申请+¥600年费", "duration": "4-8月",
                    "url": "https://www.cnipa.gov.cn",
                },
                {
                    "code": "eu", "label": "欧盟 RCD (EUIPO)", "flag": "🇪🇺",
                    "fee": "€350起", "duration": "约1-2周",
                    "url": "https://www.euipo.europa.eu",
                },
                {
                    "code": "wipo", "label": "WIPO 海牙", "flag": "🌐",
                    "fee": "CHF 397起", "duration": "6-12月",
                    "url": "https://www.wipo.int/hague",
                },
            ],
        },
        "utility_patent": {
            "label": "专利",
            "jurisdictions": [
                {
                    "code": "cn", "label": "中国 (CNIPA)", "flag": "🇨🇳",
                    "fee": "¥900申请+年费", "duration": "2-3年(发明)",
                    "url": "https://www.cnipa.gov.cn",
                },
            ],
        },
        "disclaimer": "以上费用为官方参考价格, 实际以官方最新公告为准。本工具不代收任何费用。",
    })


# ─── P2.4.11: Trademark Gazette Monitoring Info ──────────────


TRADEMARK_GAZETTE_GUIDE = {
    "cn": {
        "title": "中国商标公告监测指引",
        "gazette_name": "商标公告 / 商标初审公告",
        "institution": "国家知识产权局商标局 (CNIPA)",
        "gazette_url": "https://sbj.cnipa.gov.cn/sbj/gg/",
        "search_url": "https://wcjs.sbj.cnipa.gov.cn/",
        "publication_frequency": "每周",
        "opposition_period": "公告之日起3个月",
        "how_to_monitor": [
            "访问商标局官网公告页面，按月/按类别查阅商标公告",
            "使用商标网上检索系统 (wcjs.sbj.cnipa.gov.cn) 按申请人/商标名称检索",
            "关注商标电子公告的 PDF 下载",
            "委托商标代理机构设置商标监测服务（推荐，约 ¥200-500/月）",
        ],
        "key_tips": [
            "初审公告期为3个月，此期间内任何人均可提出异议",
            "异议须在公告期满前提交，建议在公告期内尽早查阅以避免错过期限",
            "使用商标局官方检索系统而避免使用非官方第三方工具",
            "重点监测与自己商标相同/近似的第16/25/28/35/41/42类商标公告",
        ],
        "opposition_howto": "在商标初审公告发布之日起3个月内向商标局提交《商标异议申请书》及证据材料。",
        "official_fee_opposition": "异议申请费 ¥500/件（部分减免情况请咨询商标局）。",
    },
    "us": {
        "title": "USPTO Trademark Official Gazette (TMOG) Monitoring Guide",
        "gazette_name": "Trademark Official Gazette (TMOG)",
        "institution": "USPTO (美国专利商标局)",
        "gazette_url": "https://www.uspto.gov/trademarks/trademark-official-gazette-tmog",
        "search_url": "https://tsdr.uspto.gov/",
        "publication_frequency": "每周二",
        "opposition_period": "公告之日起30天（可申请30天延期）",
        "how_to_monitor": [
            "访问 USPTO 官网的 TMOG 页面，下载每周的 PDF 公告或按类别浏览",
            "使用 TSDR (Trademark Status & Document Retrieval) 检索具体商标状态",
            "使用 TESS (Trademark Electronic Search System) 进行监控检索",
            "设置 USPTO 通知提醒，订阅商标状态变更通知",
            "委托美国商标律师设置商标监测（推荐，约 $100-300/月）",
        ],
        "key_tips": [
            "公告期仅30天（TTAB 可批准30天延期），时间紧迫务必及时关注",
            "在美外国申请人必须指定美国代理律师（USC 37 CFR 2.11）",
            "异议须向 TTAB (Trademark Trial and Appeal Board) 提交",
        ],
        "opposition_howto": "在公告期30天内向 TTAB 提交 Notice of Opposition 或申请延期。",
        "official_fee_opposition": "TTAB 异议费 $400/类（通过 ESTTA 电子提交）。",
    },
    "eu": {
        "title": "EUIPO EUTM Bulletin Monitoring Guide",
        "gazette_name": "EUTM Bulletin (欧盟商标公告)",
        "institution": "EUIPO (欧盟知识产权局)",
        "gazette_url": "https://www.euipo.europa.eu/en/trademarks/eutm-bulletin",
        "search_url": "https://euipo.europa.eu/eSearch/",
        "publication_frequency": "每日",
        "opposition_period": "公告之日起3个月",
        "how_to_monitor": [
            "访问 EUIPO eSearch plus 数据库进行商标检索",
            "设置 EUIPO Watch Service（商标监测服务，官方提供，€200-400/年区域）",
            "订阅 EUTM Bulletin 每日更新",
        ],
        "key_tips": [
            "EUIPO 提供官方商标监测服务 (Watch Service)，可在商标公告时自动通知",
            "异议期为3个月，不提供延期",
            "反对方须在异议期内提交 Notice of Opposition (€320)",
            "异议有 cooling-off period (2个月，可延长至24个月)",
        ],
        "opposition_howto": "在公告期3个月内通过 EUIPO 电子平台提交 Opposition。",
        "official_fee_opposition": "异议费 €320。",
    },
}


@router.get("/ipr/gazette/{jurisdiction}", response_model=ApiResponse)
def get_trademark_gazette_info(jurisdiction: str):
    """P2.4.11: 商标公告监测指引.

    返回特定辖区的商标公告监测指南，包含:
    - 公告名称和机构
    - 公告频率
    - 异议期时间窗口
    - 如何监测的步骤
    - 关键提示
    """
    jurisdiction = jurisdiction.lower()
    guide = TRADEMARK_GAZETTE_GUIDE.get(jurisdiction)
    if not guide:
        return ApiResponse(data={
            "jurisdiction": jurisdiction,
            "available_jurisdictions": list(TRADEMARK_GAZETTE_GUIDE.keys()),
            "message": f"暂不支持 '{jurisdiction}' 的公告监测指引。当前支持: CN, US, EU",
        })
    return ApiResponse(data=guide)


@router.post("/ipr/fee-calculator", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def fee_calculator(data: FeeCalculatorPayload):
    """IP 费用计算器: 计算各辖区商标/版权/外观设计的官方费用.

    Request body:
        ip_type: "trademark" | "copyright" | "design_patent"
        jurisdictions: ["cn", "us", "eu", ...]
        classes: [16, 25, 41]  (商标类别, trademark时才需要)
        design_count: int  (外观设计数量, design_patent时才需要)
        wipo_designations: ["eu", "us"]  (仅WIPO时需要指定国家)
        is_color: bool  (WIPO商标彩色加收CHF 250)
    """
    ip_type = data.ip_type
    jurisdictions = data.jurisdictions
    classes = data.classes
    design_count = data.design_count
    wipo_designations = data.wipo_designations
    is_color = data.is_color

    if not jurisdictions:
        raise HTTPException(status_code=400, detail="jurisdictions 是必填项, 至少指定一个辖区")

    disclaimer = "本工具仅提供信息指引，不构成法律建议。费用为官方参考价，实际以各官方机构最新公告为准。汇率以实时汇率为准。所有费用须由申请人直接支付给官方机构。本工具不代收任何费用。"

    # 汇率参考 (2026年6月, 近似值)
    fx_rates = {
        "CNY": 1.0,
        "USD": 7.25,
        "EUR": 7.85,
        "CHF": 8.05,
        "JPY": 0.048,
        "KRW": 0.0053,
    }

    breakdown = []
    total_cny = 0.0

    for jur in jurisdictions:
        fee_info = FEE_SCHEDULE.get(jur, {}).get(ip_type)
        if not fee_info:
            breakdown.append({
                "jurisdiction": jur,
                "label": f"{jur} - 不支持",
                "currency": "N/A",
                "fee": 0,
                "fee_cny": 0,
                "error": f"不支持的 IP 类型/辖区组合: {ip_type}/{jur}",
            })
            continue

        currency = fee_info["currency"]
        rate = fx_rates.get(currency, 1.0)
        fee = 0.0

        if ip_type == "trademark":
            class_count = len(classes) if classes else 1
            if jur == "eu":
                # EUIPO: €850 class 1, €50 class 2, €150 class 3+
                if class_count >= 1:
                    fee += 850
                if class_count >= 2:
                    fee += 50
                if class_count >= 3:
                    fee += 150 * (class_count - 2)
            elif jur == "wipo":
                base = 903 if is_color else 653
                fee += base
                # Designation fees
                designations = wipo_designations if wipo_designations else ["eu", "us", "jp", "kr"]
                for des in designations:
                    des_fee = fee_info.get("designation_fees", {}).get(des, 0)
                    fee += des_fee
            else:
                fee = fee_info.get("application_fee_per_class", 0) * class_count

        elif ip_type == "copyright":
            fee = fee_info.get("application_fee_per_class", 0)

        elif ip_type == "design_patent":
            if jur == "eu":
                fee = 350
                if design_count > 1:
                    fee += 175 * min(design_count - 1, 9)
            elif jur == "wipo":
                fee = fee_info.get("application_fee_per_class", 397)
                if design_count > 1:
                    fee += fee_info.get("additional_design_fee", 19) * (design_count - 1)
                fee += fee_info.get("publication_fee", 17) * design_count
                # Designation fees
                designations = wipo_designations if wipo_designations else ["eu"]
                for des in designations:
                    fee += fee_info.get("designation_fees", {}).get(des, 0)
            else:
                fee = fee_info.get("application_fee_per_class", 0)

        fee_cny = round(fee * rate, 2)
        total_cny += fee_cny

        # Fee detail
        detail_parts = {}
        if ip_type == "trademark" and jur == "eu":
            detail_parts["第1类"] = "€850"
            if len(classes) >= 2:
                detail_parts["第2类"] = "€50"
            if len(classes) >= 3:
                detail_parts["第3类起"] = f"€150 × {len(classes) - 2}"
            detail_parts["汇率"] = f"€1 = ¥{rate}"
        elif ip_type == "trademark" and jur == "wipo":
            detail_parts["基础费"] = f"CHF {base}"
            if is_color:
                detail_parts["彩色加收"] = "CHF 250"
            for des_idx, des in enumerate(wipo_designations if wipo_designations else ["eu", "us", "jp", "kr"]):
                des_fee = fee_info.get("designation_fees", {}).get(des)
                if des_fee:
                    detail_parts[f"指定{des.upper()}"] = f"CHF {des_fee}"
            detail_parts["汇率"] = f"CHF 1 = ¥{rate}"
        elif ip_type == "design_patent" and jur == "wipo":
            detail_parts["基本费"] = f"CHF {fee_info.get('application_fee_per_class', 397)}"
            if design_count > 1:
                detail_parts["额外设计费"] = f"CHF {fee_info.get('additional_design_fee', 19)} × {design_count - 1}"
            detail_parts["公告费"] = f"CHF {fee_info.get('publication_fee', 17)} × {design_count}"
            for des in (wipo_designations if wipo_designations else ["eu"]):
                des_fee = fee_info.get("designation_fees", {}).get(des)
                if des_fee:
                    detail_parts[f"指定{des.upper()}"] = f"CHF {des_fee}"
            detail_parts["汇率"] = f"CHF 1 = ¥{rate}"

        item = {
            "jurisdiction": jur,
            "jurisdiction_label": fee_info["label"],
            "currency": currency,
            "fee": fee,
            "fee_cny": fee_cny,
            "rate": rate,
            "classes_count": len(classes) if ip_type == "trademark" else None,
            "design_count": design_count if ip_type == "design_patent" else None,
            "notes": fee_info.get("notes", ""),
            "detail": detail_parts if detail_parts else None,
        }
        breakdown.append(item)

    # 汇总
    summary = {
        "ip_type": ip_type,
        "ip_type_label": {
            "trademark": "商标",
            "copyright": "版权",
            "design_patent": "外观设计",
        }.get(ip_type, ip_type),
        "jurisdictions_count": len(jurisdictions),
        "total_fee_cny": round(total_cny, 2),
        "currency_breakdown": {},
        "disclaimer": disclaimer,
    }

    for item in breakdown:
        cur = item["currency"]
        if cur not in summary["currency_breakdown"]:
            summary["currency_breakdown"][cur] = 0
        summary["currency_breakdown"][cur] += item["fee"]

    # Round currency breakdown
    for cur in summary["currency_breakdown"]:
        summary["currency_breakdown"][cur] = round(summary["currency_breakdown"][cur], 2)

    return ApiResponse(data={
        "summary": summary,
        "breakdown": breakdown,
        "fx_rates_used": fx_rates,
        "fx_rates_note": "参考汇率 (2026年6月), 实际费用以支付时的汇率为准",
    })


# ─── 辅助函数 ─────────────────────────────────────────────────


def _parse_date(value):
    """安全解析日期字符串."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def _prefill_copyright(work, tags, notary):
    """预填版权登记字段."""
    fields = [
        {
            "official_field": "作品名称", "label_zh": "作品名称",
            "value": work.title or "", "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "作品类别", "label_zh": "作品类别",
            "value": _map_file_type_to_category(work.file_type),
            "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "作者姓名", "label_zh": "作者姓名",
            "value": "", "source": "manual", "editable": True, "required": True,
        },
        {
            "official_field": "创作完成日期", "label_zh": "创作完成日期",
            "value": work.created_at.strftime("%Y-%m-%d") if work.created_at else "",
            "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "首次发表日期", "label_zh": "首次发表日期",
            "value": work.created_at.strftime("%Y-%m-%d") if work.created_at else "",
            "source": "work", "editable": True, "required": False,
        },
        {
            "official_field": "创作说明", "label_zh": "创作说明 (50-500字)",
            "value": work.description or "",
            "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "权利归属", "label_zh": "权利归属说明",
            "value": "本人独立创作，享有完整著作权", "source": "manual", "editable": True, "required": True,
        },
        {
            "official_field": "标签关键词", "label_zh": "标签/关键词",
            "value": ", ".join(tags) if tags else "",
            "source": "work", "editable": True, "required": False,
        },
        {
            "official_field": "作品文件", "label_zh": "作品样本文件",
            "value": work.file_name if work.file_name else "",
            "source": "work", "editable": False, "required": True,
        },
        {
            "official_field": "存证哈希", "label_zh": "区块链存证哈希 (可选附加)",
            "value": notary.evidence_hash if notary else "",
            "source": "notary", "editable": False, "required": False,
        },
    ]
    return fields


def _prefill_trademark(work, tags):
    """预填商标注册字段."""
    fields = [
        {
            "official_field": "商标名称", "label_zh": "商标名称",
            "value": work.title or "", "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "申请人名称", "label_zh": "申请人名称",
            "value": "", "source": "manual", "editable": True, "required": True,
        },
        {
            "official_field": "申请人地址", "label_zh": "申请人地址",
            "value": "", "source": "manual", "editable": True, "required": True,
        },
        {
            "official_field": "商品/服务类别", "label_zh": "商品/服务类别",
            "value": _recommend_classes_from_tags(tags),
            "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "商标图样", "label_zh": "商标图样文件",
            "value": work.file_name if work.file_name else "",
            "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "标签关键词", "label_zh": "标签/关键词",
            "value": ", ".join(tags) if tags else "",
            "source": "work", "editable": True, "required": False,
        },
    ]
    return fields


def _prefill_generic(work, tags):
    """通用预填."""
    return [
        {
            "official_field": "名称", "label_zh": "名称",
            "value": work.title or "", "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "创作完成日期", "label_zh": "创作完成日期",
            "value": work.created_at.strftime("%Y-%m-%d") if work.created_at else "",
            "source": "work", "editable": True, "required": True,
        },
        {
            "official_field": "标签关键词", "label_zh": "标签/关键词",
            "value": ", ".join(tags) if tags else "",
            "source": "work", "editable": True, "required": False,
        },
    ]


def _map_file_type_to_category(file_type):
    """映射文件类型到版权作品类别."""
    mapping = {
        "image": "美术作品",
        "video": "视听作品",
        "audio": "音乐作品",
        "document": "文字作品",
        "code": "计算机软件",
        "design": "美术作品",
    }
    return mapping.get(file_type, "美术作品")


def _recommend_classes_from_tags(tags):
    """从作品标签推荐商品/服务类别."""
    matched = set()
    for tag in tags:
        tag_lower = tag.lower()
        for kw, classes in TAG_TO_CLASS_MAP.items():
            if kw.lower() in tag_lower or tag_lower in kw.lower():
                matched.update(classes)
    if not matched:
        matched = {16, 41}
    return ", ".join(f"第{c}类" for c in sorted(matched))


def _build_timeline(record):
    """构建状态时间线."""
    timeline = []
    if record.created_at:
        timeline.append({
            "date": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
            "status": "draft", "label": "创建记录",
        })
    if record.filing_date:
        timeline.append({
            "date": record.filing_date.isoformat() if hasattr(record.filing_date, "isoformat") else str(record.filing_date),
            "status": "filed", "label": "提交申请",
        })
    if record.registration_date:
        timeline.append({
            "date": record.registration_date.isoformat() if hasattr(record.registration_date, "isoformat") else str(record.registration_date),
            "status": "registered", "label": "注册完成",
        })
    if record.expiration_date:
        timeline.append({
            "date": record.expiration_date.isoformat() if hasattr(record.expiration_date, "isoformat") else str(record.expiration_date),
            "status": "expiration_due", "label": "到期日",
        })
    timeline.sort(key=lambda x: x["date"])
    return timeline


def _calculate_renewals(records, today):
    """计算续展提醒列表."""
    renewals = []
    for r in records:
        # 使用 next_action_date 或 expiration_date
        ref_date = r.next_action_date or r.expiration_date
        if not ref_date:
            continue

        if isinstance(ref_date, datetime):
            ref_date = ref_date.date()

        days = (ref_date - today).days

        # 只返回未来的事件和最近已过期的
        if days < -365:
            continue

        # 判断紧急程度
        if days < 0:
            urgency = "red"
        elif days <= 60:
            urgency = "red"
        elif days <= 180:
            urgency = "orange"
        else:
            urgency = "yellow"

        ip_type_labels = {
            "trademark": "商标",
            "copyright": "版权",
            "design_patent": "外观设计",
            "utility_patent": "专利",
        }

        jurisdiction_labels = {
            "cn": "中国", "us": "美国", "eu": "欧盟",
            "jp": "日本", "kr": "韩国", "wipo": "WIPO",
        }

        renewals.append({
            "id": r.id,
            "ip_type": r.ip_type,
            "ip_type_label": ip_type_labels.get(r.ip_type, r.ip_type),
            "jurisdiction": r.jurisdiction,
            "jurisdiction_label": jurisdiction_labels.get(r.jurisdiction, r.jurisdiction),
            "application_no": r.application_no,
            "registration_no": r.registration_no,
            "status": r.status,
            "expiration_date": r.expiration_date.isoformat() if r.expiration_date else None,
            "next_action_date": ref_date.isoformat(),
            "next_action_type": r.next_action_type,
            "days_remaining": days,
            "urgency": urgency,
        })

    # 按紧急程度和天数排序
    renewals.sort(key=lambda x: ({"red": 0, "orange": 1, "yellow": 2}[x["urgency"]], x["days_remaining"]))
    return renewals
