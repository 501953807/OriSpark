import client from './client'

export const aiGenerateApi = {
  autoTags: (workId: string) =>
    client.post<{ data: { tags: string[]; confidence: number } }>(
      '/ai/generate/tags',
      { work_id: workId },
    ),

  autoDescription: (workId: string) =>
    client.post<{ data: { description: string } }>(
      '/ai/generate/description',
      { work_id: workId },
    ),

  draftArticle: (prompt: string, tone: string = 'professional', maxWords: number = 2000) =>
    client.post<{ data: string }>('/ai/generate/article', {
      prompt,
      tone,
      max_words: maxWords,
    }),

  draftProductDesc: (
    productName: string,
    materials: string[],
    techniques: string[],
  ) =>
    client.post<{ data: string }>('/ai/generate/product-desc', {
      product_name: productName,
      materials,
      techniques,
    }),

  draftMusicDesc: (title: string, genre: string, mood: string, bpm: number) =>
    client.post<{ data: string }>('/ai/generate/music-desc', {
      title,
      genre,
      mood,
      bpm,
    }),

  moderateContent: (text: string) =>
    client.post<{
      data: { safe: boolean; categories: Record<string, boolean>; reason: string }
    }>('/ai/generate/moderate', { text }),

  getConfig: () =>
    client.get<{ data: { configured: boolean; provider: string } }>('/ai/generate/config'),
}
