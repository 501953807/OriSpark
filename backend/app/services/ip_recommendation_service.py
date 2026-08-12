"""IP 类别推荐服务 — 基于关键词匹配 + 简单 TF-IDF 启发式."""

from collections import Counter
from typing import Optional

from app.models.ipr import NiceClassification
from sqlalchemy.orm import Session

_NICE_CLASSES_FULL = [
    {"class_no": 1, "name_zh": "化学原料", "name_en": "Chemicals", "keywords": ["工业化学品", "摄影化学品", "粘合剂", "肥料", "防腐剂"]},
    {"class_no": 2, "name_zh": "颜料油漆", "name_en": "Paints and Coatings", "keywords": ["颜料", "油漆", "清漆", "防锈制剂", "印刷油墨", "绘画颜料", "水彩颜料", "油画颜料"]},
    {"class_no": 3, "name_zh": "日化用品", "name_en": "Cosmetics and Cleaning Preparations", "keywords": ["洗衣制剂", "清洁剂", "香水", "护肤品", "化妆品", "牙膏", "发用制剂"]},
    {"class_no": 4, "name_zh": "润滑油燃料", "name_en": "Lubricants and Fuels", "keywords": ["工业用油脂", "润滑油", "燃料", "照明用蜡烛"]},
    {"class_no": 5, "name_zh": "医药制剂", "name_en": "Pharmaceutical Preparations", "keywords": ["药品", "医用营养品", "消毒剂", "杀虫制剂", "兽药"]},
    {"class_no": 6, "name_zh": "金属材料", "name_en": "Common Metals and Alloys", "keywords": ["普通金属合金", "建筑材料金属", "金属锁", "钢丝绳"]},
    {"class_no": 7, "name_zh": "机械设备", "name_en": "Machinery", "keywords": ["机器机床", "发动机", "农业机械", "建筑机械"]},
    {"class_no": 8, "name_zh": "手工器械", "name_en": "Hand Tools and Implements", "keywords": ["刀具", "勺叉餐具", "锉刀", "剪刀", "剃须刀"]},
    {"class_no": 9, "name_zh": "电子仪器", "name_en": "Electric and Scientific Apparatus", "keywords": ["软件", "APP", "电子出版物", "摄影器材", "计算机硬件", "耳机", "虚拟现实设备", "人工智能软件", "AIGC生成软件"]},
    {"class_no": 10, "name_zh": "医疗器械", "name_en": "Medical Apparatus and Instruments", "keywords": ["医疗器械", "假肢", "矫形物品", "婴儿用品"]},
    {"class_no": 11, "name_zh": "灯具空调", "name_en": "Apparatus for Lighting, Heating, Cooling", "keywords": ["照明设备", "电灯", "加热设备", "空调", "冷冻设备", "消毒设备"]},
    {"class_no": 12, "name_zh": "运输工具", "name_en": "Vehicles", "keywords": ["汽车", "自行车", "电动车", "飞行器", "船舶"]},
    {"class_no": 13, "name_zh": "烟火武器", "name_en": "Firearms and Ammunition", "keywords": ["火器", "弹药", "烟火制品", "烟花"]},
    {"class_no": 14, "name_zh": "珠宝钟表", "name_en": "Jewellery and Timepieces", "keywords": ["首饰", "宝石", "钟表", "贵金属", "珠宝盒"]},
    {"class_no": 15, "name_zh": "乐器", "name_en": "Musical Instruments", "keywords": ["乐器", "电子琴", "吉他", "钢琴", "音序器", "MIDI设备"]},
    {"class_no": 16, "name_zh": "纸品文具", "name_en": "Paper and Stationery", "keywords": ["纸张", "文具", "办公用品", "印刷品", "画作", "海报", "贴纸", "笔记本", "美术用品", "画布", "油画框"]},
    {"class_no": 17, "name_zh": "橡胶制品", "name_en": "Rubber and Plastic Products", "keywords": ["橡胶制品", "塑料填充料", "包装材料"]},
    {"class_no": 18, "name_zh": "皮革箱包", "name_en": "Leather and Bag Making", "keywords": ["皮革", "行李箱", "手提包", "钱包", "皮带", "驯兽皮"]},
    {"class_no": 19, "name_zh": "非金属建材", "name_en": "Non-metallic Building Materials", "keywords": ["建筑材料", "玻璃", "水泥", "非金属管道"]},
    {"class_no": 20, "name_zh": "家具制品", "name_en": "Furniture and Furnishings", "keywords": ["家具", "枕头", "床垫", "镜子", "相框"]},
    {"class_no": 21, "name_zh": "家用器具", "name_en": "Household and Kitchen Utensils", "keywords": ["家用玻璃器皿", "梳子", "刷子", "清洁用具", "化妆用具"]},
    {"class_no": 22, "name_zh": "绳索织品", "name_en": "Rope and Cordage and Fibres", "keywords": ["绳索", "帆布", "帐篷", "麻袋", "纤维"]},
    {"class_no": 23, "name_zh": "纱线丝", "name_en": "Yarn and Thread", "keywords": ["纺织纤维", "缝纫线", "刺绣线"]},
    {"class_no": 24, "name_zh": "织物床单", "name_en": "Fabrics and Textile Goods", "keywords": ["布料", "床单", "桌布", "窗帘", "纺织品"]},
    {"class_no": 25, "name_zh": "服装鞋帽", "name_en": "Clothing, Footwear, Headgear", "keywords": ["服装", "鞋", "帽", "T恤", "外套", "运动鞋", "潮牌服饰"]},
    {"class_no": 26, "name_zh": "饰品纽扣", "name_en": "Fancy Goods", "keywords": ["钮扣", "拉链", "花边", "发饰", "假发"]},
    {"class_no": 27, "name_zh": "地毯席垫", "name_en": "Floor Coverings", "keywords": ["地毯", "席子", "地垫", "墙纸"]},
    {"class_no": 28, "name_zh": "玩具游戏", "name_en": "Games and Sporting Goods", "keywords": ["玩具", "游戏器具", "桌游", "运动器材", "圣诞装饰", "手办", "盲盒", "玩偶"]},
    {"class_no": 29, "name_zh": "食品", "name_en": "Food and Beverages", "keywords": ["肉类", "鱼类", "腌渍食品", "奶制品", "食用油"]},
    {"class_no": 30, "name_zh": "调味品谷物", "name_en": "Staple Foodstuffs", "keywords": ["咖啡", "茶", "糖", "米面制品", "调味品", "面包"]},
    {"class_no": 31, "name_zh": "生鲜食品", "name_en": "Fresh Fruits and Vegetables", "keywords": ["新鲜水果", "蔬菜", "活体动物", "饲料", "花卉"]},
    {"class_no": 32, "name_zh": "啤酒饮料", "name_en": "Beers and Non-alcoholic Beverages", "keywords": ["啤酒", "果汁", "矿泉水", "苏打水", "饮料"]},
    {"class_no": 33, "name_zh": "含酒精饮料", "name_en": "Wines and Spirits", "keywords": ["葡萄酒", "烈酒", "含酒精饮料"]},
    {"class_no": 34, "name_zh": "烟草用品", "name_en": "Smoking Articles", "keywords": ["烟草", "火柴", "打火机", "烟斗"]},
    {"class_no": 35, "name_zh": "广告销售", "name_en": "Advertising and Business Management", "keywords": ["广告", "商业管理", "替他人推销", "在线市场", "零售服务", "市场营销"]},
    {"class_no": 36, "name_zh": "保险金融", "name_en": "Insurance and Financial Affairs", "keywords": ["金融事务", "保险", "金融评估", "货币兑换"]},
    {"class_no": 37, "name_zh": "建筑修理", "name_en": "Building Construction and Repair", "keywords": ["建筑", "修理", "安装服务", "装修"]},
    {"class_no": 38, "name_zh": "电信服务", "name_en": "Telecommunications", "keywords": ["电信服务", "卫星传输", "流媒体传输"]},
    {"class_no": 39, "name_zh": "运输旅行", "name_en": "Transport and Travel Arrangement", "keywords": ["运输", "旅行安排", "快递", "货物仓储"]},
    {"class_no": 40, "name_zh": "材料加工", "name_en": "Treatment of Materials", "keywords": ["材料处理", "食品加工", "布料处理", "印刷服务"]},
    {"class_no": 41, "name_zh": "教育娱乐", "name_en": "Education and Entertainment", "keywords": ["教育", "培训", "娱乐", "影视制作", "动画制作", "出版", "艺术指导", "娱乐信息", "流媒体播放"]},
    {"class_no": 42, "name_zh": "科研服务", "name_en": "Scientific and Technological Services", "keywords": ["科学研究", "工业设计", "软件开发", "计算机编程", "人工智能", "SaaS", "云计算", "设计服务"]},
    {"class_no": 43, "name_zh": "餐饮住宿", "name_en": "Food and Beverage Services", "keywords": ["餐厅", "酒吧", "咖啡馆", "住宿服务"]},
    {"class_no": 44, "name_zh": "医疗园艺", "name_en": "Medical and Beauty Care", "keywords": ["医疗服务", "兽医服务", "美容服务", "理发店", "园艺服务"]},
    {"class_no": 45, "name_zh": "法律服务", "name_en": "Legal and Personal Services", "keywords": ["法律服务", "安全管理", "个人服务"]},
]


def _tokenize(text: str) -> list[str]:
    """简单中文分词 + 英文单词分割."""
    tokens = []
    if text:
        for ch in text:
            if ord(ch) > 127:
                tokens.append(ch)
            elif ch.isalnum():
                tokens.append(ch)
    return tokens


def _tokenize_keywords(keywords: list[str]) -> set[str]:
    """提取所有关键词 token."""
    tokens = set()
    for kw in keywords:
        tokens.update(_tokenize(kw))
    return tokens


class IPRecommendationService:
    """IP 类别推荐服务."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def recommend_classes(self, description: str, ip_type: str) -> list[dict]:
        """根据描述和IP类型推荐尼斯分类，返回 top 3-5 条."""
        tokens = _tokenize(description)
        if not tokens:
            return self._fallback_recommendation(ip_type)

        scores: dict[int, float] = {}
        tf = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1
        n_classes = len(_NICE_CLASSES_FULL)

        for cls in _NICE_CLASSES_FULL:
            kw_tokens = _tokenize_keywords(cls["keywords"])
            if not kw_tokens:
                continue
            overlap = set(tokens) & kw_tokens
            if not overlap:
                continue
            idf = 1.0 + (n_classes / max(1, len(cls["keywords"])))
            tfidf = sum((tf.get(t, 0) / max_tf) * idf for t in overlap)
            scores[cls["class_no"]] = tfidf

        if not scores:
            return self._fallback_recommendation(ip_type)

        sorted_classes = sorted(scores.items(), key=lambda x: -x[1])
        top_k = min(5, len(sorted_classes))
        results = []

        for class_no, raw_score in sorted_classes[:top_k]:
            cls = next((c for c in _NICE_CLASSES_FULL if c["class_no"] == class_no), None)
            if not cls:
                continue
            confidence = round(min(0.99, 0.35 + raw_score * 0.12), 2)
            if confidence < 0.20:
                confidence = 0.15
            results.append({
                "class_id": class_no,
                "class_name": cls["name_zh"],
                "class_name_en": cls["name_en"],
                "confidence": confidence,
                "description": "、".join(cls["keywords"][:5]),
            })

        if not results:
            return self._fallback_recommendation(ip_type)
        return results

    def _fallback_recommendation(self, ip_type: str) -> list[dict]:
        """无描述时的兜底推荐."""
        defaults = {
            "trademark": [9, 16, 25, 28, 35, 41, 42],
            "copyright": [9, 16, 41, 42],
            "design_patent": [16, 21, 25, 28],
            "utility_patent": [7, 9, 42],
        }
        class_nums = defaults.get(ip_type, [16, 35, 41, 42])
        results = []
        for class_no in class_nums:
            cls = next((c for c in _NICE_CLASSES_FULL if c["class_no"] == class_no), None)
            if cls:
                results.append({
                    "class_id": class_no,
                    "class_name": cls["name_zh"],
                    "class_name_en": cls["name_en"],
                    "confidence": 0.25,
                    "description": "、".join(cls["keywords"][:5]),
                })
        return results
