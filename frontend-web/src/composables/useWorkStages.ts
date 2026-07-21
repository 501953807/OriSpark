/** 作品过程阶段定义.

按 file_type 提供不同的阶段选项. 每种知产类型有独立的阶段定义.
*/

export interface StageOption {
  value: string
  label: string
  color: string
}

/** 图片/插画创作流程 */
export const IMAGE_STAGES: StageOption[] = [
  { value: 'inspiration', label: '灵感', color: '#8B5CF6' },
  { value: 'sketch', label: '草图', color: '#EC4896' },
  { value: 'lineart', label: '线稿', color: '#F59E0B' },
  { value: 'coloring', label: '上色', color: '#EF4444' },
  { value: 'detail', label: '细节', color: '#10B981' },
  { value: 'final', label: '终稿', color: '#3B82F6' },
]

/** 视频创作流程 */
export const VIDEO_STAGES: StageOption[] = [
  { value: 'script', label: '脚本', color: '#8B5CF6' },
  { value: 'storyboard', label: '分镜', color: '#EC4896' },
  { value: 'roughcut', label: '粗剪', color: '#F59E0B' },
  { value: 'finecut', label: '精剪', color: '#EF4444' },
  { value: 'colorgrade', label: '调色', color: '#10B981' },
  { value: 'final', label: '成片', color: '#3B82F6' },
]

/** 音频创作流程 */
export const AUDIO_STAGES: StageOption[] = [
  { value: 'idea', label: '构思', color: '#8B5CF6' },
  { value: 'arrangement', label: '编曲', color: '#EC4896' },
  { value: 'recording', label: '录音', color: '#F59E0B' },
  { value: 'mixing', label: '混音', color: '#EF4444' },
  { value: 'mastering', label: '母带', color: '#10B981' },
  { value: 'release', label: '发行', color: '#3B82F6' },
]

/** 文档创作流程 */
export const DOCUMENT_STAGES: StageOption[] = [
  { value: 'outline', label: '大纲', color: '#8B5CF6' },
  { value: 'draft', label: '初稿', color: '#EC4896' },
  { value: 'revision', label: '修订', color: '#F59E0B' },
  { value: 'final', label: '定稿', color: '#EF4444' },
]

/** 设计/3D创作流程 */
export const DESIGN_STAGES: StageOption[] = [
  { value: 'concept', label: '概念', color: '#8B5CF6' },
  { value: 'modeling', label: '建模', color: '#EC4896' },
  { value: 'texturing', label: '贴图', color: '#F59E0B' },
  { value: 'rigging', label: '绑定', color: '#EF4444' },
  { value: 'animation', label: '动画', color: '#10B981' },
  { value: 'render', label: '渲染', color: '#3B82F6' },
  { value: 'final', label: '成品', color: '#6366F1' },
]

/** 代码创作流程 */
export const CODE_STAGES: StageOption[] = [
  { value: 'design', label: '设计', color: '#8B5CF6' },
  { value: 'prototype', label: '原型', color: '#EC4896' },
  { value: 'develop', label: '开发', color: '#F59E0B' },
  { value: 'test', label: '测试', color: '#EF4444' },
  { value: 'deploy', label: '部署', color: '#10B981' },
  { value: 'maintain', label: '维护', color: '#3B82F6' },
]

/** file_type → 阶段集合映射 */
const STAGE_MAP: Record<string, StageOption[]> = {
  image: IMAGE_STAGES,
  video: VIDEO_STAGES,
  audio: AUDIO_STAGES,
  document: DOCUMENT_STAGES,
  design: DESIGN_STAGES,
  code: CODE_STAGES,
}

/** 根据文件类型获取对应的阶段集合 */
export function getStagesForFileType(fileType: string): StageOption[] {
  return STAGE_MAP[fileType] || IMAGE_STAGES
}

/** 获取所有唯一的阶段值（用于内部使用） */
export function getAllStages(): StageOption[] {
  const seen = new Set<string>()
  const result: StageOption[] = []
  for (const stages of Object.values(STAGE_MAP)) {
    for (const s of stages) {
      if (!seen.has(s.value)) {
        seen.add(s.value)
        result.push(s)
      }
    }
  }
  return result
}

/** 根据阶段值查找颜色 */
export function getStageColor(stage: string): string {
  for (const stages of Object.values(STAGE_MAP)) {
    const found = stages.find(s => s.value === stage)
    if (found) return found.color
  }
  return '#6B7280'
}

/** 根据阶段值和文件类型获取阶段索引 */
export function getStageIndex(stage: string, fileType: string): number {
  const stages = getStagesForFileType(fileType)
  return stages.findIndex(s => s.value === stage)
}

// 旧名称别名，保持向后兼容
export const ILLUSTRATION_STAGES = IMAGE_STAGES
export const GENERIC_STAGES = IMAGE_STAGES // 已废弃，保留用于兼容
