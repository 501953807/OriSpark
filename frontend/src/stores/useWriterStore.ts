import { defineStore } from 'pinia'
import { ref } from 'vue'
import { writerApi } from '@/api/writer'
import type {
  Article,
  Book,
  Manuscript,
  WriterStats,
  CreateArticleInput,
  UpdateArticleInput,
  CreateBookInput,
  CreateManuscriptInput,
  UpdateManuscriptInput,
} from '@/types/writer'

export const useWriterStore = defineStore('writer', () => {
  // ── State ────────────────────────────────────────────────────────

  const articles = ref<Article[]>([])
  const books = ref<Book[]>([])
  const manuscripts = ref<Manuscript[]>([])
  const stats = ref<WriterStats>({
    total_articles: 0,
    published_count: 0,
    total_words: 0,
    active_books: 0,
    monthly_reads: 0,
  })
  const loading = ref(false)
  const errorMsg = ref('')

  // ── Helpers ──────────────────────────────────────────────────────

  function setError(msg: string, e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : msg
  }

  // ── Articles ─────────────────────────────────────────────────────

  async function fetchArticles() {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await writerApi.getArticles()
      articles.value = res.data.data ?? []
    } catch (e: unknown) {
      setError('获取文章列表失败', e)
      articles.value = []
    } finally {
      loading.value = false
    }
  }

  async function createArticle(data: CreateArticleInput): Promise<Article | null> {
    try {
      const res = await writerApi.createArticle(data)
      const item = res.data.data
      articles.value = [...articles.value, item]
      return item
    } catch (e: unknown) {
      setError('创建文章失败', e)
      return null
    }
  }

  async function updateArticle(id: string, data: UpdateArticleInput): Promise<Article | null> {
    try {
      const res = await writerApi.updateArticle(id, data)
      const updated = res.data.data
      articles.value = articles.value.map((a) => (a.id === id ? updated : a))
      return updated
    } catch (e: unknown) {
      setError('更新文章失败', e)
      return null
    }
  }

  async function deleteArticle(id: string): Promise<boolean> {
    try {
      await writerApi.deleteArticle(id)
      articles.value = articles.value.filter((a) => a.id !== id)
      return true
    } catch (e: unknown) {
      setError('删除文章失败', e)
      return false
    }
  }

  // ── Books ────────────────────────────────────────────────────────

  async function fetchBooks() {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await writerApi.getBooks()
      books.value = res.data.data ?? []
    } catch (e: unknown) {
      setError('获取书籍列表失败', e)
      books.value = []
    } finally {
      loading.value = false
    }
  }

  async function createBook(data: CreateBookInput): Promise<Book | null> {
    try {
      const res = await writerApi.createBook(data)
      const item = res.data.data
      books.value = [...books.value, item]
      return item
    } catch (e: unknown) {
      setError('创建书籍失败', e)
      return null
    }
  }

  async function updateBook(id: string, data: Partial<Book>): Promise<Book | null> {
    try {
      const res = await writerApi.updateBook(id, data)
      const updated = res.data.data
      books.value = books.value.map((b) => (b.id === id ? updated : b))
      return updated
    } catch (e: unknown) {
      setError('更新书籍失败', e)
      return null
    }
  }

  async function deleteBook(id: string): Promise<boolean> {
    try {
      await writerApi.deleteBook(id)
      books.value = books.value.filter((b) => b.id !== id)
      return true
    } catch (e: unknown) {
      setError('删除书籍失败', e)
      return false
    }
  }

  // ── Manuscripts ──────────────────────────────────────────────────

  async function fetchManuscripts(bookId?: string) {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await writerApi.getManuscripts(bookId)
      manuscripts.value = res.data.data ?? []
    } catch (e: unknown) {
      setError('获取手稿列表失败', e)
      manuscripts.value = []
    } finally {
      loading.value = false
    }
  }

  async function createManuscript(data: CreateManuscriptInput): Promise<Manuscript | null> {
    try {
      const res = await writerApi.createManuscript(data)
      const item = res.data.data
      manuscripts.value = [...manuscripts.value, item]
      return item
    } catch (e: unknown) {
      setError('创建手稿失败', e)
      return null
    }
  }

  async function updateManuscript(id: string, data: UpdateManuscriptInput): Promise<Manuscript | null> {
    try {
      const res = await writerApi.updateManuscript(id, data)
      const updated = res.data.data
      manuscripts.value = manuscripts.value.map((m) => (m.id === id ? updated : m))
      return updated
    } catch (e: unknown) {
      setError('更新手稿失败', e)
      return null
    }
  }

  async function deleteManuscript(id: string): Promise<boolean> {
    try {
      await writerApi.deleteManuscript(id)
      manuscripts.value = manuscripts.value.filter((m) => m.id !== id)
      return true
    } catch (e: unknown) {
      setError('删除手稿失败', e)
      return false
    }
  }

  // ── Stats ────────────────────────────────────────────────────────

  async function computeStats(): Promise<WriterStats> {
    loading.value = true
    try {
      const res = await writerApi.getStats()
      stats.value = res.data.data ?? stats.value
    } catch (e: unknown) {
      setError('获取统计数据失败', e)
    } finally {
      loading.value = false
    }
    return stats.value
  }

  // ── Bulk ─────────────────────────────────────────────────────────

  async function fetchAll() {
    loading.value = true
    errorMsg.value = ''
    try {
      await Promise.all([
        fetchArticles(),
        fetchBooks(),
        fetchManuscripts(),
        computeStats(),
      ])
    } catch (e: unknown) {
      setError('加载数据失败', e)
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    articles,
    books,
    manuscripts,
    stats,
    loading,
    errorMsg,
    // Actions
    fetchArticles,
    createArticle,
    updateArticle,
    deleteArticle,
    fetchBooks,
    createBook,
    updateBook,
    deleteBook,
    fetchManuscripts,
    createManuscript,
    updateManuscript,
    deleteManuscript,
    computeStats,
    fetchAll,
  }
})
