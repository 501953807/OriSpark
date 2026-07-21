export type CreatorType =
  | 'illustrator'
  | 'photographer'
  | 'video'
  | 'craftsman'
  | 'musician'
  | 'writer'

export interface CreatorTypeInfo {
  type: CreatorType
  label: string
  icon: string
  color: string
  description: string
  routes: string[]
  features: string[]
}

export const CREATOR_TYPES: Record<CreatorType, CreatorTypeInfo> = {
  illustrator: {
    type: 'illustrator',
    label: '插画师',
    icon: 'Palette',
    color: '#8B5CF6',
    description: '数字插画与矢量设计创作平台',
    routes: ['works', 'rights', 'monitor', 'business', 'illustrator'],
    features: ['AIGC防护', '风格分析', '版权登记'],
  },
  photographer: {
    type: 'photographer',
    label: '摄影师',
    icon: 'Camera',
    color: '#3B82F6',
    description: '摄影作品管理与图库分发平台',
    routes: ['works', 'rights', 'monitor', 'business', 'photographer'],
    features: ['RAW元数据', 'GPS定位', '图库渠道'],
  },
  video: {
    type: 'video',
    label: '视频创作者',
    icon: 'Video',
    color: '#EF4444',
    description: '视频创作与版权监控平台',
    routes: ['works', 'rights', 'monitor', 'business', 'video'],
    features: ['指纹扫描', '工程包管理', '平台分发'],
  },
  craftsman: {
    type: 'craftsman',
    label: '手工艺人',
    icon: 'Hammer',
    color: '#F59E0B',
    description: '手工艺品制作与销售平台',
    routes: ['works', 'rights', 'monitor', 'business', 'craftsman'],
    features: ['工厂对接', '询价管理', 'Etsy同步'],
  },
  musician: {
    type: 'musician',
    label: '音乐人',
    icon: 'Music',
    color: '#10B981',
    description: '音乐创作与发行平台',
    routes: ['works', 'rights', 'monitor', 'business', 'musician'],
    features: ['ISRC注册', '分成协议', '平台分发'],
  },
  writer: {
    type: 'writer',
    label: '文字作者',
    icon: 'Feather',
    color: '#6366F1',
    description: '文字创作与出版管理平台',
    routes: ['works', 'rights', 'monitor', 'business', 'writer'],
    features: ['文章管理', '书籍创作', '手稿编辑'],
  },
}

/** Map route name prefixes to their CreatorType values. */
const ROUTE_TO_TYPE_MAP: Record<string, CreatorType> = {
  illustrator: 'illustrator',
  photographer: 'photographer',
  video: 'video',
  craftsman: 'craftsman',
  musician: 'musician',
  writer: 'writer',
}

export function getCreatorType(routeName?: string): CreatorType {
  if (!routeName) return 'illustrator'
  for (const [prefix, type] of Object.entries(ROUTE_TO_TYPE_MAP)) {
    if (routeName.includes(prefix)) return type
  }
  return 'illustrator'
}

export function getAllCreators(): CreatorTypeInfo[] {
  return Object.values(CREATOR_TYPES)
}

export function getDefaultCreatorType(): CreatorType {
  return 'illustrator'
}
