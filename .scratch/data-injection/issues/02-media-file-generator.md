# 02 — 媒体文件生成器

**What to build:** 为6种创作者类型生成真实媒体文件（图片/音频/视频/PDF），存入test_media目录。

**Blocked by:** 01-database-schema-fix（需要确保目录结构正确）

**Status:** ready-for-agent

## 背景
系统需要真实媒体文件支撑业务演示，但目前test_media目录为空。

## 媒体需求矩阵
| 创作者类型 | 图片数量 | 音频数量 | 视频数量 | PDF数量 |
|-----------|---------|---------|---------|--------|
| illustrator | 10张 | 0 | 0 | 0 |
| photographer | 10张 | 0 | 0 | 0 |
| video_creator | 5张 | 0 | 5个 | 0 |
| crafter | 8张 | 0 | 0 | 0 |
| musician | 5张 | 5个 | 0 | 0 |
| writer | 5张 | 0 | 0 | 5个 |

## 验收标准
- [ ] test_media/images/ 包含≥43张图片（800×600或400×600分辨率）
- [ ] test_media/audio/ 包含≥5个音频文件（MP3格式，时长5-15秒）
- [ ] test_media/video/ 包含≥5个视频占位（或使用图片替代）
- [ ] 图片使用PIL生成彩色测试图（非空白）
- [ ] 音频使用WAV格式正弦波（可播放）
- [ ] PDF使用reportlab生成（含标题和正文）
- [ ] 每个文件命名符合规范：`{creator_type}_{index}.{ext}`

## 技术说明
- 图片：PIL生成随机颜色测试图
- 音频：struct打包WAV格式正弦波
- PDF：reportlab生成含文本的PDF
- 不使用外部API（避免网络依赖）
