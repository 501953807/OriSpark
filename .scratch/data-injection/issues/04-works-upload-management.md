# 04 — 作品上传与管理（6种类型全覆盖）

**What to build:** 为每个创作者账号上传5个作品，涵盖图片/音频/视频/PDF所有类型，包含标签、项目分组等管理操作。

**Blocked by:** 03-creator-account-registration

**Status:** ready-for-agent

## 背景
作品是系统的核心数据实体，需要覆盖所有创作者类型的文件格式。

## 作品分布
| 创作者类型 | 作品数 | 文件类型 | 关键属性 |
|-----------|-------|---------|---------|
| illustrator | 25 | image/jpg | tags=["奇幻","赛博朋克"] |
| photographer | 25 | image/jpg | exif_data={"camera":"Test"} |
| video_creator | 25 | video/mp4 | duration字段 |
| crafter | 25 | image/jpg | 材质信息 |
| musician | 25 | audio/mp3 | album信息 |
| writer | 25 | document/pdf | 书籍关联 |

总计：150个作品

## 验收标准
- [ ] 每个创作者有5个作品（共150个）
- [ ] 作品file_type与创作者类型匹配
- [ ] 作品包含有效的thumbnail_path
- [ ] 支持作品标签添加（POST /api/works/{id}/tags）
- [ ] 支持作品元数据更新（PATCH /api/works/{id}）
- [ ] 作品列表查询按类型筛选正常工作
- [ ] SHA-256哈希正确生成

## API端点
- POST /api/works — 创建作品
- POST /api/works/{id}/tags — 添加标签
- PATCH /api/works/{id} — 更新元数据
- GET /api/works — 列表查询
- GET /api/works/{id} — 详情
