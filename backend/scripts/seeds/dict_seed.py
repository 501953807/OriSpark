"""字典种子数据.

初始化 60+ 字典分组及对应条目。
在应用启动时自动调用，幂等（已存在的不会重复插入）。
"""

import hashlib
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.system import DictionaryGroup, DictionaryItem


def _gen_id() -> str:
    return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:16]


# 所有字典种子数据
# 格式: (group_key, group_name, module, description, is_extensible, items[])
# items: [(item_key, item_value, item_value_en, extra_dict, sort_order), ...]

SEED_DATA = [
    # ==================== 01-作品相关 ====================
    ("file_types", "文件类型", "works", "作品文件的基础类型分类", False, [
        ("image", "图片", "Image", {"icon": "image", "color": "#4A90D9"}, 1),
        ("audio", "音频", "Audio", {"icon": "music", "color": "#E67E22"}, 2),
        ("video", "视频", "Video", {"icon": "video", "color": "#E74C3C"}, 3),
        ("document", "文档", "Document", {"icon": "file-text", "color": "#2ECC71"}, 4),
        ("code", "代码", "Code", {"icon": "code", "color": "#9B59B6"}, 5),
        ("design", "设计", "Design", {"icon": "pen-tool", "color": "#1ABC9C"}, 6),
        ("other", "其他", "Other", {"icon": "file", "color": "#95A5A6"}, 99),
    ]),
    ("import_modes", "导入模式", "works", "作品文件导入模式", False, [
        ("hash_only", "仅哈希", "Hash Only", {"description": "仅计算文件指纹，不上传文件"}, 1),
        ("lowres", "低分辨率", "Low Res", {"description": "上传低分辨率预览图"}, 2),
        ("full", "完整文件", "Full", {"description": "上传完整原始文件"}, 3),
    ]),
    ("work_statuses", "作品状态", "works", "作品生命周期状态", False, [
        ("draft", "草稿", "Draft", {"color": "#95A5A6"}, 1),
        ("active", "活跃", "Active", {"color": "#2ECC71"}, 2),
        ("trashed", "回收站", "Trashed", {"color": "#E74C3C"}, 3),
        ("archived", "已归档", "Archived", {"color": "#7F8C8D"}, 4),
    ]),
    ("process_stages_image", "图片创作阶段", "works", "图像创作流程阶段", True, [
        ("inspiration", "灵感", "Inspiration", {"icon": "lightbulb"}, 1),
        ("sketch", "草图", "Sketch", {"icon": "pencil"}, 2),
        ("lineart", "线稿", "Lineart", {"icon": "pen-tool"}, 3),
        ("color", "上色", "Coloring", {"icon": "palette"}, 4),
        ("detail", "细节", "Detailing", {"icon": "zoom-in"}, 5),
        ("final", "终稿", "Final", {"icon": "check-circle"}, 6),
        ("export", "导出", "Export", {"icon": "download"}, 7),
    ]),
    ("process_stages_audio", "音频创作阶段", "works", "音频创作流程阶段", True, [
        ("inspiration", "灵感", "Inspiration", {"icon": "lightbulb"}, 1),
        ("compose", "编曲", "Composing", {"icon": "music"}, 2),
        ("record", "录音", "Recording", {"icon": "mic"}, 3),
        ("mix", "混音", "Mixing", {"icon": "sliders"}, 4),
        ("master", "母带", "Mastering", {"icon": "disc"}, 5),
        ("publish", "发行", "Publishing", {"icon": "upload-cloud"}, 6),
    ]),
    ("process_stages_video", "视频创作阶段", "works", "视频创作流程阶段", True, [
        ("script", "脚本", "Script", {"icon": "file-text"}, 1),
        ("storyboard", "分镜", "Storyboard", {"icon": "grid"}, 2),
        ("rough_cut", "粗剪", "Rough Cut", {"icon": "scissors"}, 3),
        ("fine_cut", "精剪", "Fine Cut", {"icon": "film"}, 4),
        ("color_grade", "调色", "Color Grading", {"icon": "palette"}, 5),
        ("final", "成片", "Final", {"icon": "check-circle"}, 6),
    ]),
    ("process_stages_document", "文档创作阶段", "works", "文档创作流程阶段", True, [
        ("outline", "大纲", "Outline", {"icon": "list"}, 1),
        ("draft", "初稿", "Draft", {"icon": "edit"}, 2),
        ("revise", "修订", "Revising", {"icon": "refresh-cw"}, 3),
        ("final", "终稿", "Final", {"icon": "check-circle"}, 4),
        ("typeset", "排版", "Typesetting", {"icon": "layout"}, 5),
        ("publish", "发布", "Publishing", {"icon": "upload-cloud"}, 6),
    ]),
    ("process_stages_generic", "通用阶段", "works", "通用创作流程阶段", False, [
        ("start", "开始", "Start", {"icon": "play"}, 1),
        ("in_progress", "进行中", "In Progress", {"icon": "loader"}, 2),
        ("done", "完成", "Done", {"icon": "check-circle"}, 3),
        ("abandoned", "废弃", "Abandoned", {"icon": "trash-2"}, 4),
        ("archived", "归档", "Archived", {"icon": "archive"}, 5),
    ]),
    ("license_types", "许可证类型", "works", "作品授权许可证", False, [
        ("cc_by_4.0", "CC BY 4.0", "CC BY 4.0", {"url": "https://creativecommons.org/licenses/by/4.0/"}, 1),
        ("cc_by_sa_4.0", "CC BY-SA 4.0", "CC BY-SA 4.0", {"url": "https://creativecommons.org/licenses/by-sa/4.0/"}, 2),
        ("cc_by_nc_4.0", "CC BY-NC 4.0", "CC BY-NC 4.0", {"url": "https://creativecommons.org/licenses/by-nc/4.0/"}, 3),
        ("cc_by_nd_4.0", "CC BY-ND 4.0", "CC BY-ND 4.0", {"url": "https://creativecommons.org/licenses/by-nd/4.0/"}, 4),
        ("cc0_1.0", "CC0 1.0", "CC0 1.0", {"url": "https://creativecommons.org/publicdomain/zero/1.0/"}, 5),
        ("all_rights_reserved", "保留所有权利", "All Rights Reserved", {}, 6),
        ("mit", "MIT", "MIT License", {}, 7),
    ]),
    ("rights_acquisition", "权利取得方式", "works", "知识产权权利取得方式", False, [
        ("original", "原创", "Original", {}, 1),
        ("transfer", "权利转让", "Transfer", {}, 2),
        ("commission", "委托创作", "Commission", {}, 3),
        ("work_for_hire", "职务作品", "Work for Hire", {}, 4),
        ("licensed", "授权许可", "Licensed", {}, 5),
    ]),

    # ==================== 02-存证相关 ====================
    ("notary_platforms", "存证平台", "notary", "第三方存证平台", False, [
        ("banquanjia", "版权家", "BanQuanJia", {"url": "https://www.banquanjia.com.cn"}, 1),
        ("antchain", "蚂蚁链", "AntChain", {"url": "https://antchain.antgroup.com"}, 2),
        ("zhixinchain", "知信链", "ZhiXinChain", {"url": "https://zhixinchain.com"}, 3),
    ]),
    ("notary_statuses", "存证状态", "notary", "存证生命周期状态", False, [
        ("unverified", "未验证", "Unverified", {"color": "#95A5A6"}, 1),
        ("pending", "待确认", "Pending", {"color": "#F39C12"}, 2),
        ("confirmed", "已确认", "Confirmed", {"color": "#2ECC71"}, 3),
        ("expired", "已过期", "Expired", {"color": "#E74C3C"}, 4),
    ]),
    ("notary_layers", "存证层级", "notary", "存证法律效力层级", False, [
        ("L1_local", "L1 本地存证", "L1 Local", {"description": "本地哈希存证"}, 1),
        ("L2_blockchain", "L2 区块链存证", "L2 Blockchain", {"description": "上链存证"}, 2),
        ("L3_judicial", "L3 司法存证", "L3 Judicial", {"description": "司法鉴定中心接入"}, 3),
        ("L4_credential", "L4 凭证存证", "L4 Credential", {"description": "C2PA 凭证存证"}, 4),
    ]),
    ("certificate_types", "证书类型", "notary", "存证证书类型", False, [
        ("pdf", "PDF 证书", "PDF Certificate", {}, 1),
        ("pdf_2.0", "PDF 2.0 证书", "PDF 2.0 Certificate", {}, 2),
        ("json_cert", "JSON 凭证", "JSON Certificate", {}, 3),
    ]),

    # ==================== 03-监测相关 ====================
    ("search_platforms", "搜索平台", "monitor", "侵权监测搜索引擎", False, [
        ("baidu", "百度", "Baidu", {"url": "https://www.baidu.com"}, 1),
        ("google", "Google", "Google", {"url": "https://www.google.com"}, 2),
        ("bing", "Bing", "Bing", {"url": "https://www.bing.com"}, 3),
        ("yandex", "Yandex", "Yandex", {"url": "https://yandex.com"}, 4),
        ("github", "GitHub", "GitHub", {"url": "https://github.com"}, 5),
    ]),
    ("search_types", "搜索类型", "monitor", "监测搜索类型", False, [
        ("image", "图片搜索", "Image Search", {"icon": "image"}, 1),
        ("text", "文本搜索", "Text Search", {"icon": "file-text"}, 2),
        ("code", "代码搜索", "Code Search", {"icon": "code"}, 3),
        ("logo", "Logo 搜索", "Logo Search", {"icon": "aperture"}, 4),
        ("brand", "品牌搜索", "Brand Search", {"icon": "tag"}, 5),
    ]),
    ("match_statuses", "匹配状态", "monitor", "侵权匹配处理状态", False, [
        ("pending_review", "待审核", "Pending Review", {"color": "#F39C12"}, 1),
        ("infringing", "侵权确认", "Infringing", {"color": "#E74C3C"}, 2),
        ("ignored", "已忽略", "Ignored", {"color": "#95A5A6"}, 3),
        ("whitelisted", "白名单", "Whitelisted", {"color": "#2ECC71"}, 4),
    ]),
    ("similarity_tiers", "相似度分级", "monitor", "侵权匹配相似度等级", False, [
        ("high", "高 (>=90%)", "High (>=90%)", {"color": "#E74C3C", "min": 90, "max": 100}, 1),
        ("mid", "中 (70-90%)", "Mid (70-90%)", {"color": "#F39C12", "min": 70, "max": 90}, 2),
        ("low", "低 (50-70%)", "Low (50-70%)", {"color": "#3498DB", "min": 50, "max": 70}, 3),
        ("very_low", "极低 (<50%)", "Very Low (<50%)", {"color": "#95A5A6", "min": 0, "max": 50}, 4),
    ]),
    ("scan_intervals", "扫描频率", "monitor", "监测扫描频率", False, [
        ("manual", "手动", "Manual", {}, 1),
        ("daily", "每天", "Daily", {}, 2),
        ("weekly", "每周", "Weekly", {}, 3),
        ("monthly", "每月", "Monthly", {}, 4),
        ("custom", "自定义", "Custom", {}, 5),
    ]),
    ("evidence_types", "证据包类型", "monitor", "证据包类型", False, [
        ("complaint", "投诉材料", "Complaint", {}, 1),
        ("lawyer_letter", "律师函", "Lawyer Letter", {}, 2),
        ("dmca", "DMCA 通知", "DMCA Notice", {}, 3),
        ("evidence", "证据包", "Evidence Package", {}, 4),
    ]),

    # ==================== 04-知识产权相关 ====================
    ("ip_types", "IP类型", "ipr", "知识产权类型", False, [
        ("copyright", "著作权", "Copyright", {"icon": "copy"}, 1),
        ("trademark", "商标", "Trademark", {"icon": "tag"}, 2),
        ("design_patent", "外观设计专利", "Design Patent", {"icon": "box"}, 3),
        ("utility_patent", "实用新型专利", "Utility Patent", {"icon": "tool"}, 4),
        ("invention_patent", "发明专利", "Invention Patent", {"icon": "zap"}, 5),
    ]),
    ("ip_statuses", "IP状态", "ipr", "知识产权申请状态", False, [
        ("draft", "草稿", "Draft", {"color": "#95A5A6"}, 1),
        ("filed", "已提交", "Filed", {"color": "#3498DB"}, 2),
        ("under_review", "审查中", "Under Review", {"color": "#F39C12"}, 3),
        ("registered", "已注册", "Registered", {"color": "#2ECC71"}, 4),
        ("rejected", "已驳回", "Rejected", {"color": "#E74C3C"}, 5),
        ("expired", "已过期", "Expired", {"color": "#7F8C8D"}, 6),
    ]),
    ("jurisdictions", "司法管辖区", "ipr", "司法管辖区代码", False, [
        ("cn", "中国", "China", {"flag": "🇨🇳"}, 1),
        ("us", "美国", "United States", {"flag": "🇺🇸"}, 2),
        ("eu", "欧盟", "European Union", {"flag": "🇪🇺"}, 3),
        ("jp", "日本", "Japan", {"flag": "🇯🇵"}, 4),
        ("kr", "韩国", "Korea", {"flag": "🇰🇷"}, 5),
        ("wipo", "WIPO", "WIPO", {"flag": "🌐"}, 6),
        ("gb", "英国", "United Kingdom", {"flag": "🇬🇧"}, 7),
        ("de", "德国", "Germany", {"flag": "🇩🇪"}, 8),
        ("fr", "法国", "France", {"flag": "🇫🇷"}, 9),
    ]),
    ("trademark_offices", "商标局", "ipr", "各国商标注册管理机构", False, [
        ("cnipa", "国家知识产权局 (CNIPA)", "CNIPA", {}, 1),
        ("uspto", "美国专利商标局 (USPTO)", "USPTO", {}, 2),
        ("euipo", "欧盟知识产权局 (EUIPO)", "EUIPO", {}, 3),
        ("jpo", "日本特许厅 (JPO)", "JPO", {}, 4),
        ("kipo", "韩国特许厅 (KIPO)", "KIPO", {}, 5),
        ("wipo", "世界知识产权组织 (WIPO)", "WIPO", {}, 6),
    ]),
    ("nice_classes", "尼斯分类", "ipr", "商标注册用商品和服务国际分类 (第1-45类)", False, [
        ("c1", "第1类 - 化学原料", "Class 1 - Chemicals", {}, 1),
        ("c2", "第2类 - 颜料油漆", "Class 2 - Paints", {}, 2),
        ("c3", "第3类 - 日化用品", "Class 3 - Cosmetics", {}, 3),
        ("c4", "第4类 - 燃料油脂", "Class 4 - Fuels", {}, 4),
        ("c5", "第5类 - 医药", "Class 5 - Pharmaceuticals", {}, 5),
        ("c6", "第6类 - 金属材料", "Class 6 - Metals", {}, 6),
        ("c7", "第7类 - 机械设备", "Class 7 - Machinery", {}, 7),
        ("c8", "第8类 - 手工器械", "Class 8 - Hand Tools", {}, 8),
        ("c9", "第9类 - 科学仪器", "Class 9 - Scientific Devices", {}, 9),
        ("c10", "第10类 - 医疗器械", "Class 10 - Medical Apparatus", {}, 10),
        ("c11", "第11类 - 灯具空调", "Class 11 - Lighting", {}, 11),
        ("c12", "第12类 - 运输工具", "Class 12 - Vehicles", {}, 12),
        ("c13", "第13类 - 军火烟火", "Class 13 - Firearms", {}, 13),
        ("c14", "第14类 - 珠宝钟表", "Class 14 - Jewelry", {}, 14),
        ("c15", "第15类 - 乐器", "Class 15 - Musical Instruments", {}, 15),
        ("c16", "第16类 - 办公用品", "Class 16 - Paper Goods", {}, 16),
        ("c17", "第17类 - 橡胶制品", "Class 17 - Rubber", {}, 17),
        ("c18", "第18类 - 皮革皮具", "Class 18 - Leather", {}, 18),
        ("c19", "第19类 - 建筑材料", "Class 19 - Building Materials", {}, 19),
        ("c20", "第20类 - 家具", "Class 20 - Furniture", {}, 20),
        ("c21", "第21类 - 厨房洁具", "Class 21 - Kitchenware", {}, 21),
        ("c22", "第22类 - 绳网袋篷", "Class 22 - Ropes", {}, 22),
        ("c23", "第23类 - 纱线纺织", "Class 23 - Yarns", {}, 23),
        ("c24", "第24类 - 布料床单", "Class 24 - Fabrics", {}, 24),
        ("c25", "第25类 - 服装鞋帽", "Class 25 - Clothing", {}, 25),
        ("c26", "第26类 - 纽扣拉链", "Class 26 - Fancy Goods", {}, 26),
        ("c27", "第27类 - 地毯席垫", "Class 27 - Floor Coverings", {}, 27),
        ("c28", "第28类 - 玩具体育", "Class 28 - Toys", {}, 28),
        ("c29", "第29类 - 食品", "Class 29 - Food", {}, 29),
        ("c30", "第30类 - 调味茶饮", "Class 30 - Beverages", {}, 30),
        ("c31", "第31类 - 农林生鲜", "Class 31 - Agriculture", {}, 31),
        ("c32", "第32类 - 啤酒饮料", "Class 32 - Beers", {}, 32),
        ("c33", "第33类 - 酒精饮料", "Class 33 - Wines", {}, 33),
        ("c34", "第34类 - 烟草烟具", "Class 34 - Tobacco", {}, 34),
        ("c35", "第35类 - 广告商业", "Class 35 - Advertising", {}, 35),
        ("c36", "第36类 - 金融物管", "Class 36 - Finance", {}, 36),
        ("c37", "第37类 - 建筑修理", "Class 37 - Construction", {}, 37),
        ("c38", "第38类 - 通讯服务", "Class 38 - Communications", {}, 38),
        ("c39", "第39类 - 运输贮藏", "Class 39 - Transport", {}, 39),
        ("c40", "第40类 - 材料加工", "Class 40 - Material Treatment", {}, 40),
        ("c41", "第41类 - 教育娱乐", "Class 41 - Education", {}, 41),
        ("c42", "第42类 - 科技服务", "Class 42 - Science & Tech", {}, 42),
        ("c43", "第43类 - 餐饮住宿", "Class 43 - Hospitality", {}, 43),
        ("c44", "第44类 - 医疗园艺", "Class 44 - Medical & Horticulture", {}, 44),
        ("c45", "第45类 - 社会服务", "Class 45 - Social Services", {}, 45),
    ]),
    ("creator_types", "创作者类型", "ipr", "创作者身份分类", False, [
        ("illustrator", "插画师", "Illustrator", {"icon": "pen-tool"}, 1),
        ("vtuber", "虚拟主播/VTuber", "VTuber", {"icon": "user"}, 2),
        ("gamedev", "游戏开发者", "Game Developer", {"icon": "gamepad"}, 3),
        ("musician", "音乐人", "Musician", {"icon": "music"}, 4),
        ("writer", "作家/作者", "Writer", {"icon": "edit"}, 5),
        ("designer", "设计师", "Designer", {"icon": "layout"}, 6),
        ("photographer", "摄影师", "Photographer", {"icon": "camera"}, 7),
        ("filmmaker", "视频创作者", "Filmmaker", {"icon": "video"}, 8),
        ("crafter", "手工艺人", "Crafter", {"icon": "scissors"}, 9),
    ]),

    # ==================== 05-变现相关 ====================
    ("monetization_paths", "变现路径", "supply", "内容变现方式", False, [
        ("pod", "按需印刷 (POD)", "Print on Demand", {"icon": "printer"}, 1),
        ("crowdfunding", "众筹", "Crowdfunding", {"icon": "users"}, 2),
        ("licensing", "授权", "Licensing", {"icon": "file-text"}, 3),
        ("custom_mfg", "定制生产", "Custom Manufacturing", {"icon": "tool"}, 4),
        ("digital", "数字商品", "Digital Products", {"icon": "download"}, 5),
    ]),
    ("pod_platforms", "POD平台", "supply", "按需印刷合作平台", False, [
        ("printful", "Printful", "Printful", {"url": "https://www.printful.com"}, 1),
        ("printify", "Printify", "Printify", {"url": "https://printify.com"}, 2),
        ("redbubble", "Redbubble", "Redbubble", {"url": "https://www.redbubble.com"}, 3),
        ("society6", "Society6", "Society6", {"url": "https://society6.com"}, 4),
        ("gelato", "Gelato", "Gelato", {"url": "https://www.gelato.com"}, 5),
        ("zazzle", "Zazzle", "Zazzle", {"url": "https://www.zazzle.com"}, 6),
        ("teespring", "Teespring/Spring", "Spring", {"url": "https://www.spri.ng"}, 7),
        ("spreadshirt", "Spreadshirt", "Spreadshirt", {"url": "https://www.spreadshirt.com"}, 8),
    ]),
    ("crowdfunding_platforms", "众筹平台", "supply", "内容众筹平台", False, [
        ("modian", "摩点", "MoDian", {"url": "https://www.modian.com"}, 1),
        ("zaodianxinhuo", "造点新货", "ZaoDianXinHuo", {"url": "https://zaodianxinhuo.com"}, 2),
        ("kickstarter", "Kickstarter", "Kickstarter", {"url": "https://www.kickstarter.com"}, 3),
        ("indiegogo", "Indiegogo", "Indiegogo", {"url": "https://www.indiegogo.com"}, 4),
        ("patreon", "Patreon", "Patreon", {"url": "https://www.patreon.com"}, 5),
    ]),
    ("licensing_platforms", "授权平台", "supply", "内容授权交易平台", False, [
        ("creative_fabrica", "Creative Fabrica", "Creative Fabrica", {"url": "https://www.creativefabrica.com"}, 1),
        ("creative_market", "Creative Market", "Creative Market", {"url": "https://creativemarket.com"}, 2),
        ("envato", "Envato", "Envato", {"url": "https://envato.com"}, 3),
        ("design_cuts", "Design Cuts", "Design Cuts", {"url": "https://www.designcuts.com"}, 4),
    ]),
    ("license_model_types", "授权模式", "supply", "内容商业授权模式", False, [
        ("single_use", "单次使用", "Single Use", {}, 1),
        ("multi_use", "多次使用", "Multi Use", {}, 2),
        ("commercial_extended", "商业扩展", "Commercial Extended", {}, 3),
        ("buyout", "买断", "Buyout", {}, 4),
    ]),
    ("material_categories", "材质分类", "supply", "产品材质分类", False, [
        ("paper", "纸质", "Paper", {}, 1),
        ("textile", "纺织", "Textile", {}, 2),
        ("hard_plastic", "硬质塑料", "Hard Plastic", {}, 3),
        ("metal", "金属", "Metal", {}, 4),
        ("wood", "木质", "Wood", {}, 5),
        ("leather", "皮革", "Leather", {}, 6),
        ("ceramic", "陶瓷", "Ceramic", {}, 7),
        ("canvas", "帆布", "Canvas", {}, 8),
        ("acrylic", "亚克力", "Acrylic", {}, 9),
        ("silicone", "硅胶", "Silicone", {}, 10),
    ]),
    ("product_categories_paper", "纸质产品", "supply", "纸质品类产品", True, [
        ("poster", "海报", "Poster", {}, 1),
        ("postcard", "明信片", "Postcard", {}, 2),
        ("sticker", "贴纸", "Sticker", {}, 3),
        ("notebook", "笔记本", "Notebook", {}, 4),
        ("calendar", "日历", "Calendar", {}, 5),
        ("bookmark", "书签", "Bookmark", {}, 6),
        ("greeting_card", "贺卡", "Greeting Card", {}, 7),
        ("art_print", "艺术微喷", "Art Print", {}, 8),
        ("wrapping_paper", "包装纸", "Wrapping Paper", {}, 9),
    ]),
    ("product_categories_textile", "纺织产品", "supply", "纺织品类产品", True, [
        ("tshirt", "T恤", "T-Shirt", {}, 1),
        ("hoodie", "卫衣", "Hoodie", {}, 2),
        ("tote_bag", "帆布袋", "Tote Bag", {}, 3),
        ("cap", "帽子", "Cap", {}, 4),
        ("scarf", "围巾", "Scarf", {}, 5),
        ("pillow", "抱枕", "Pillow", {}, 6),
        ("bath_towel", "浴巾", "Bath Towel", {}, 7),
        ("socks", "袜子", "Socks", {}, 8),
        ("blanket", "毯子", "Blanket", {}, 9),
        ("tapestry", "挂毯", "Tapestry", {}, 10),
        ("apron", "围裙", "Apron", {}, 11),
    ]),
    ("product_categories_hardgoods", "硬质产品", "supply", "硬质品类产品", True, [
        ("mug", "马克杯", "Mug", {}, 1),
        ("enamel_mug", "搪瓷杯", "Enamel Mug", {}, 2),
        ("coaster", "杯垫", "Coaster", {}, 3),
        ("plate", "盘子", "Plate", {}, 4),
        ("clock", "时钟", "Clock", {}, 5),
        ("puzzle", "拼图", "Puzzle", {}, 6),
        ("rug", "地毯", "Rug", {}, 7),
    ]),
    ("product_categories_plastic", "塑料产品", "supply", "塑料品类产品", True, [
        ("phone_case", "手机壳", "Phone Case", {}, 1),
        ("airpods_case", "AirPods壳", "AirPods Case", {}, 2),
        ("mousepad", "鼠标垫", "Mousepad", {}, 3),
        ("acrylic_stand", "亚克力立牌", "Acrylic Stand", {}, 4),
        ("badge", "徽章", "Badge", {}, 5),
        ("keychain", "钥匙扣", "Keychain", {}, 6),
    ]),
    ("product_categories_metal", "金属产品", "supply", "金属品类产品", True, [
        ("metal_bookmark", "金属书签", "Metal Bookmark", {}, 1),
        ("metal_badge", "金属徽章", "Metal Badge", {}, 2),
        ("metal_keychain", "金属钥匙扣", "Metal Keychain", {}, 3),
        ("necklace", "项链", "Necklace", {}, 4),
        ("earrings", "耳环", "Earrings", {}, 5),
        ("bracelet", "手链", "Bracelet", {}, 6),
        ("ornament", "摆件", "Ornament", {}, 7),
    ]),
    ("product_categories_digital", "数字产品", "supply", "数字品类产品", True, [
        ("brush", "笔刷", "Brush", {}, 1),
        ("template", "模板", "Template", {}, 2),
        ("pdf", "PDF", "PDF", {}, 3),
        ("stl", "STL 3D模型", "STL Model", {}, 4),
        ("font", "字体", "Font", {}, 5),
        ("png_clipart", "PNG素材", "PNG Clipart", {}, 6),
        ("tutorial", "教程", "Tutorial", {}, 7),
        ("video_asset", "视频素材", "Video Asset", {}, 8),
        ("music_loop", "音乐/音效", "Music Loop", {}, 9),
        ("plugin", "插件", "Plugin", {}, 10),
    ]),
    ("order_statuses", "订单状态", "supply", "订单生命周期状态", False, [
        ("draft", "草稿", "Draft", {"color": "#95A5A6"}, 1),
        ("quoting", "报价中", "Quoting", {"color": "#3498DB"}, 2),
        ("confirmed", "已确认", "Confirmed", {"color": "#2ECC71"}, 3),
        ("in_production", "生产中", "In Production", {"color": "#F39C12"}, 4),
        ("quality_check", "质检中", "Quality Check", {"color": "#9B59B6"}, 5),
        ("shipped", "已发货", "Shipped", {"color": "#1ABC9C"}, 6),
        ("delivered", "已签收", "Delivered", {"color": "#2ECC71"}, 7),
        ("cancelled", "已取消", "Cancelled", {"color": "#E74C3C"}, 8),
        ("refunded", "已退款", "Refunded", {"color": "#7F8C8D"}, 9),
    ]),
    ("payment_types", "支付类型", "supply", "订单支付阶段类型", False, [
        ("deposit", "定金", "Deposit", {}, 1),
        ("progress", "进度款", "Progress Payment", {}, 2),
        ("balance", "尾款", "Balance", {}, 3),
        ("other", "其他", "Other", {}, 4),
    ]),

    # ==================== 06-产品数据相关 ====================
    ("feed_formats", "Feed格式", "supply", "数据Feed导出格式", False, [
        ("json", "JSON", "JSON", {}, 1),
        ("csv", "CSV", "CSV", {}, 2),
        ("xml", "XML", "XML", {}, 3),
    ]),
    ("feed_targets", "Feed目标", "supply", "数据Feed目标平台", False, [
        ("google", "Google Shopping", "Google Shopping", {}, 1),
        ("shopify", "Shopify", "Shopify", {}, 2),
        ("wangdiantong", "旺店通", "WangDianTong", {}, 3),
    ]),
    ("ai_desc_styles", "AI描述风格", "supply", "AI生成商品描述的风格", False, [
        ("xiaohongshu", "小红书", "Xiaohongshu", {"description": "种草风格，活泼亲切"}, 1),
        ("taobao", "淘宝", "Taobao", {"description": "电商卖货风格"}, 2),
        ("douyin", "抖音", "Douyin", {"description": "短视频带货风格"}, 3),
        ("shopify", "Shopify", "Shopify", {"description": "国际电商风格"}, 4),
        ("etsy", "Etsy", "Etsy", {"description": "手工艺人社群风格"}, 5),
        ("kickstarter", "Kickstarter", "Kickstarter", {"description": "众筹故事风格"}, 6),
    ]),
    ("revenue_sources", "收入来源", "supply", "收入数据来源", False, [
        ("manual", "手动录入", "Manual", {}, 1),
        ("mcp_api", "MCP API", "MCP API", {}, 2),
        ("csv_import", "CSV导入", "CSV Import", {}, 3),
        ("pod_api", "POD API", "POD API", {}, 4),
    ]),
    ("currencies", "货币", "supply", "货币代码", False, [
        ("CNY", "人民币 (CNY)", "CNY", {"symbol": "¥"}, 1),
        ("USD", "美元 (USD)", "USD", {"symbol": "$"}, 2),
        ("EUR", "欧元 (EUR)", "EUR", {"symbol": "€"}, 3),
        ("JPY", "日元 (JPY)", "JPY", {"symbol": "¥"}, 4),
        ("KRW", "韩元 (KRW)", "KRW", {"symbol": "₩"}, 5),
        ("CHF", "瑞士法郎 (CHF)", "CHF", {"symbol": "CHF"}, 6),
        ("GBP", "英镑 (GBP)", "GBP", {"symbol": "£"}, 7),
    ]),

    # ==================== 07-系统相关 ====================
    ("languages", "语言", "system", "界面支持语言", False, [
        ("zh-CN", "简体中文", "Simplified Chinese", {}, 1),
        ("en-US", "English (US)", "English (US)", {}, 2),
        ("ja-JP", "日本語", "Japanese", {}, 3),
        ("ko-KR", "한국어", "Korean", {}, 4),
    ]),
    ("themes", "主题", "system", "界面主题", False, [
        ("light", "浅色", "Light", {}, 1),
        ("dark", "暗色", "Dark", {}, 2),
        ("auto", "跟随系统", "Auto", {}, 3),
    ]),
    ("auth_providers", "认证提供方", "system", "支持的身份认证方式", False, [
        ("google", "Google", "Google", {"icon": "G"}, 1),
        ("wechat", "微信", "WeChat", {"icon": "💬"}, 2),
        ("douyin", "抖音", "Douyin", {"icon": "🎵"}, 3),
        ("email", "邮箱", "Email", {"icon": "✉️"}, 4),
        ("local", "本地免登录", "Local", {"icon": "💡"}, 5),
    ]),
    ("notification_types", "通知类型", "system", "系统通知分类", False, [
        ("cert_ready", "存证完成", "Certificate Ready", {}, 1),
        ("scan_result", "扫描结果", "Scan Result", {}, 2),
        ("reminder", "到期提醒", "Reminder", {}, 3),
        ("renewal", "续展提醒", "Renewal", {}, 4),
        ("order_update", "订单状态", "Order Update", {}, 5),
        ("quota_warning", "配额预警", "Quota Warning", {}, 6),
        ("backup_complete", "备份完成", "Backup Complete", {}, 7),
        ("system_update", "系统更新", "System Update", {}, 8),
    ]),
    ("notification_channels", "通知渠道", "system", "通知推送渠道", False, [
        ("websocket", "WebSocket 实时推送", "WebSocket", {}, 1),
        ("in_app", "系统内消息", "In-App", {}, 2),
        ("email", "邮件", "Email", {}, 3),
        ("wechat_template", "微信模板消息", "WeChat Template", {}, 4),
    ]),

    ("file_extensions", "允许的文件扩展名", "works", "作品上传允许的文件扩展名", True, [
        ("jpg", "JPG", "JPG", {}, 1),
        ("jpeg", "JPEG", "JPEG", {}, 2),
        ("png", "PNG", "PNG", {}, 3),
        ("webp", "WebP", "WebP", {}, 4),
        ("gif", "GIF", "GIF", {}, 5),
        ("svg", "SVG", "SVG", {}, 6),
        ("bmp", "BMP", "BMP", {}, 7),
        ("tiff", "TIFF", "TIFF", {}, 8),
        ("mp3", "MP3", "MP3", {}, 9),
        ("wav", "WAV", "WAV", {}, 10),
        ("flac", "FLAC", "FLAC", {}, 11),
        ("ogg", "OGG", "OGG", {}, 12),
        ("aac", "AAC", "AAC", {}, 13),
        ("m4a", "M4A", "M4A", {}, 14),
        ("mp4", "MP4", "MP4", {}, 15),
        ("mov", "MOV", "MOV", {}, 16),
        ("webm", "WebM", "WebM", {}, 17),
        ("avi", "AVI", "AVI", {}, 18),
        ("mkv", "MKV", "MKV", {}, 19),
        ("pdf", "PDF", "PDF", {}, 20),
        ("docx", "DOCX", "DOCX", {}, 21),
        ("doc", "DOC", "DOC", {}, 22),
        ("txt", "TXT", "TXT", {}, 23),
        ("md", "MD", "MD", {}, 24),
        ("rtf", "RTF", "RTF", {}, 25),
        ("psd", "PSD", "PSD", {}, 26),
        ("ai", "AI", "AI", {}, 27),
        ("fig", "Figma", "Figma", {}, 28),
        ("sketch", "Sketch", "Sketch", {}, 29),
        ("py", "Python", "Python", {}, 30),
        ("js", "JavaScript", "JavaScript", {}, 31),
        ("ts", "TypeScript", "TypeScript", {}, 32),
        ("html", "HTML", "HTML", {}, 33),
        ("css", "CSS", "CSS", {}, 34),
        ("json", "JSON", "JSON", {}, 35),
        ("zip", "ZIP", "ZIP", {}, 36),
    ]),
    # ==================== 通用 ====================
    ("countries", "国家/地区", "system", "ISO 3166-1 国家和地区", False, [
        ("CN", "中国", "China", {"flag": "🇨🇳", "currency": "CNY"}, 1),
        ("US", "美国", "United States", {"flag": "🇺🇸", "currency": "USD"}, 2),
        ("JP", "日本", "Japan", {"flag": "🇯🇵", "currency": "JPY"}, 3),
        ("KR", "韩国", "South Korea", {"flag": "🇰🇷", "currency": "KRW"}, 4),
        ("GB", "英国", "United Kingdom", {"flag": "🇬🇧", "currency": "GBP"}, 5),
        ("DE", "德国", "Germany", {"flag": "🇩🇪", "currency": "EUR"}, 6),
        ("FR", "法国", "France", {"flag": "🇫🇷", "currency": "EUR"}, 7),
        ("CA", "加拿大", "Canada", {"flag": "🇨🇦", "currency": "CAD"}, 8),
        ("AU", "澳大利亚", "Australia", {"flag": "🇦🇺", "currency": "AUD"}, 9),
        ("BR", "巴西", "Brazil", {"flag": "🇧🇷", "currency": "BRL"}, 10),
        ("IN", "印度", "India", {"flag": "🇮🇳", "currency": "INR"}, 11),
        ("RU", "俄罗斯", "Russia", {"flag": "🇷🇺", "currency": "RUB"}, 12),
        ("IT", "意大利", "Italy", {"flag": "🇮🇹", "currency": "EUR"}, 13),
        ("ES", "西班牙", "Spain", {"flag": "🇪🇸", "currency": "EUR"}, 14),
        ("NL", "荷兰", "Netherlands", {"flag": "🇳🇱", "currency": "EUR"}, 15),
        ("SE", "瑞典", "Sweden", {"flag": "🇸🇪", "currency": "SEK"}, 16),
        ("SG", "新加坡", "Singapore", {"flag": "🇸🇬", "currency": "SGD"}, 17),
        ("HK", "中国香港", "Hong Kong", {"flag": "🇭🇰", "currency": "HKD"}, 18),
        ("TW", "中国台湾", "Taiwan", {"flag": "🇹🇼", "currency": "TWD"}, 19),
        ("TH", "泰国", "Thailand", {"flag": "🇹🇭", "currency": "THB"}, 20),
        ("MY", "马来西亚", "Malaysia", {"flag": "🇲🇾", "currency": "MYR"}, 21),
        ("PH", "菲律宾", "Philippines", {"flag": "🇵🇭", "currency": "PHP"}, 22),
        ("ID", "印尼", "Indonesia", {"flag": "🇮🇩", "currency": "IDR"}, 23),
        ("VN", "越南", "Vietnam", {"flag": "🇻🇳", "currency": "VND"}, 24),
    ]),
    ("timezones", "时区", "system", "常见时区", False, [
        ("Asia/Shanghai", "中国标准时间 (UTC+8)", "China Standard Time", {"offset": "+08:00"}, 1),
        ("Asia/Tokyo", "日本标准时间 (UTC+9)", "Japan Standard Time", {"offset": "+09:00"}, 2),
        ("Asia/Seoul", "韩国标准时间 (UTC+9)", "Korea Standard Time", {"offset": "+09:00"}, 3),
        ("America/New_York", "美东时间 (UTC-5)", "Eastern Time", {"offset": "-05:00"}, 4),
        ("America/Los_Angeles", "美西时间 (UTC-8)", "Pacific Time", {"offset": "-08:00"}, 5),
        ("Europe/London", "英国时间 (UTC+0)", "GMT", {"offset": "+00:00"}, 6),
        ("Europe/Paris", "欧洲中部时间 (UTC+1)", "CET", {"offset": "+01:00"}, 7),
    ]),
    ("units_length", "长度单位", "system", "度量衡长度单位", False, [
        ("mm", "毫米", "mm", {}, 1),
        ("cm", "厘米", "cm", {}, 2),
        ("inch", "英寸", "inch", {}, 3),
    ]),
    ("units_weight", "重量单位", "system", "度量衡重量单位", False, [
        ("gram", "克", "gram", {}, 1),
        ("kg", "千克", "kg", {}, 2),
        ("oz", "盎司", "oz", {}, 3),
        ("lb", "磅", "lb", {}, 4),
    ]),
]


def seed_dictionaries(db: Session):
    """初始化字典种子数据 (幂等)."""
    existing_groups = {g.group_key for g in db.query(DictionaryGroup).all()}

    for group_key, group_name, module, description, is_extensible, items in SEED_DATA:
        if group_key in existing_groups:
            continue

        group = DictionaryGroup(
            id=_gen_id(),
            group_key=group_key,
            group_name=group_name,
            module=module,
            description=description,
            is_extensible=is_extensible,
            sort_order=0,
        )
        db.add(group)

        for item_key, item_value, item_value_en, extra, sort_order in items:
            item = DictionaryItem(
                id=_gen_id(),
                group_key=group_key,
                item_key=item_key,
                item_value=item_value,
                item_value_en=item_value_en,
                extra=extra,
                is_active=True,
                sort_order=sort_order,
            )
            db.add(item)

    db.commit()


# ================================================================
# P3.6.8: 设计品类映射表 (供 AI 设计自适应端点使用)
# ================================================================

DESIGN_CATEGORIES = {
    "t_shirt": {"name_zh": "T恤", "name_en": "T-Shirt", "sizes": ["4500x5400px"], "supported": True},
    "mug": {"name_zh": "马克杯", "name_en": "Mug", "sizes": ["2400x1200px"], "supported": True},
    "poster": {"name_zh": "海报", "name_en": "Poster", "sizes": ["3508x4961px", "4961x3508px"], "supported": True},
    "sticker": {"name_zh": "贴纸", "name_en": "Sticker", "sizes": ["1200x1200px"], "supported": True},
    "phone_case": {"name_zh": "手机壳", "name_en": "Phone Case", "sizes": ["1800x3600px"], "supported": True},
    "canvas": {"name_zh": "帆布画", "name_en": "Canvas", "sizes": ["3600x3600px"], "supported": True},
    "tote_bag": {"name_zh": "帆布袋", "name_en": "Tote Bag", "sizes": ["3000x3000px"], "supported": True},
    "notebook": {"name_zh": "笔记本", "name_en": "Notebook", "sizes": ["2100x2970px"], "supported": True},
}
