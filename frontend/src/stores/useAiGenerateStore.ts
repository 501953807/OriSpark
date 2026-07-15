import { defineStore } from 'pinia'
import { ref } from 'vue'
import { aiGenerateApi } from '@/api/ai_generate'

export interface TagResult {
  tags: string[]
  confidence: number
}

export interface DescriptionResult {
  description: string
}

export interface ModerationResult {
  safe: boolean
  categories: Record<string, boolean>
  reason: string
}

export interface AIConfig {
  configured: boolean
  provider: string
}

export const useAiGenerateStore = defineStore('aiGenerate', () => {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const config = ref<AIConfig | null>(null)

  async function loadConfig() {
    try {
      const res = await aiGenerateApi.getConfig()
      config.value = res.data.data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '加载 AI 配置失败'
    }
  }

  async function autoTag(workId: string): Promise<TagResult | null> {
    loading.value = true
    error.value = null
    try {
      const res = await aiGenerateApi.autoTags(workId)
      return res.data.data
    } catch (e: unknown) {
      const status = (e as any)?.response?.status
      error.value = status === 503 ? 'AI 服务暂不可用' : (e instanceof Error ? e.message : '生成标签失败')
      return null
    } finally {
      loading.value = false
    }
  }

  async function autoDescription(workId: string): Promise<DescriptionResult | null> {
    loading.value = true
    error.value = null
    try {
      const res = await aiGenerateApi.autoDescription(workId)
      return res.data.data
    } catch (e: unknown) {
      const status = (e as any)?.response?.status
      error.value = status === 503 ? 'AI 服务暂不可用' : (e instanceof Error ? e.message : '生成描述失败')
      return null
    } finally {
      loading.value = false
    }
  }

  async function draftArticle(
    prompt: string,
    tone: string = 'professional',
    maxWords: number = 2000,
  ): Promise<string | null> {
    loading.value = true
    error.value = null
    try {
      const res = await aiGenerateApi.draftArticle(prompt, tone, maxWords)
      return res.data.data
    } catch (e: unknown) {
      const status = (e as any)?.response?.status
      error.value = status === 503 ? 'AI 服务暂不可用' : (e instanceof Error ? e.message : '生成草稿失败')
      return null
    } finally {
      loading.value = false
    }
  }

  async function draftProductDesc(
    productName: string,
    materials: string[],
    techniques: string[],
  ): Promise<string | null> {
    loading.value = true
    error.value = null
    try {
      const res = await aiGenerateApi.draftProductDesc(productName, materials, techniques)
      return res.data.data
    } catch (e: unknown) {
      const status = (e as any)?.response?.status
      error.value = status === 503 ? 'AI 服务暂不可用' : (e instanceof Error ? e.message : '生成商品描述失败')
      return null
    } finally {
      loading.value = false
    }
  }

  async function draftMusicDesc(
    title: string, genre: string, mood: string, bpm: number,
  ): Promise<string | null> {
    loading.value = true
    error.value = null
    try {
      const res = await aiGenerateApi.draftMusicDesc(title, genre, mood, bpm)
      return res.data.data
    } catch (e: unknown) {
      const status = (e as any)?.response?.status
      error.value = status === 503 ? 'AI 服务暂不可用' : (e instanceof Error ? e.message : '生成音乐描述失败')
      return null
    } finally {
      loading.value = false
    }
  }

  async function moderateContent(text: string): Promise<ModerationResult | null> {
    loading.value = true
    error.value = null
    try {
      const res = await aiGenerateApi.moderateContent(text)
      return res.data.data
    } catch (e: unknown) {
      const status = (e as any)?.response?.status
      error.value = status === 503 ? 'AI 服务暂不可用' : (e instanceof Error ? e.message : '内容审核失败')
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    config,
    loadConfig,
    autoTag,
    autoDescription,
    draftArticle,
    draftProductDesc,
    draftMusicDesc,
    moderateContent,
  }
})
