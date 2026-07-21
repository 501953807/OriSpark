import client from './client'
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

export const writerApi = {
  // ── Articles ───────────────────────────────────────────────────────

  /** 获取文章列表 */
  getArticles: (params?: Record<string, unknown>) =>
    client.get<{ data: Article[] }>('/writer/articles', { params }),

  /** 创建文章 */
  createArticle: (data: CreateArticleInput) =>
    client.post<{ data: Article }>('/writer/articles', data),

  /** 获取文章详情 */
  getArticle: (id: string) =>
    client.get<{ data: Article }>(`/writer/articles/${id}`),

  /** 更新文章 */
  updateArticle: (id: string, data: UpdateArticleInput) =>
    client.put<{ data: Article }>(`/writer/articles/${id}`, data),

  /** 删除文章 */
  deleteArticle: (id: string) =>
    client.delete<{ data: unknown }>(`/writer/articles/${id}`),

  // ── Books ──────────────────────────────────────────────────────────

  /** 获取书籍列表 */
  getBooks: (params?: Record<string, unknown>) =>
    client.get<{ data: Book[] }>('/writer/books', { params }),

  /** 创建书籍 */
  createBook: (data: CreateBookInput) =>
    client.post<{ data: Book }>('/writer/books', data),

  /** 获取书籍详情 */
  getBook: (id: string) =>
    client.get<{ data: Book }>(`/writer/books/${id}`),

  /** 更新书籍 */
  updateBook: (id: string, data: Partial<Book>) =>
    client.put<{ data: Book }>(`/writer/books/${id}`, data),

  /** 删除书籍 */
  deleteBook: (id: string) =>
    client.delete<{ data: unknown }>(`/writer/books/${id}`),

  // ── Manuscripts ────────────────────────────────────────────────────

  /** 获取手稿列表 (可按 book_id 筛选) */
  getManuscripts: (bookId?: string) => {
    const qs = bookId ? `?book_id=${bookId}` : ''
    return client.get<{ data: Manuscript[] }>(`/writer/manuscripts${qs}`)
  },

  /** 创建手稿 */
  createManuscript: (data: CreateManuscriptInput) =>
    client.post<{ data: Manuscript }>('/writer/manuscripts', data),

  /** 获取手稿详情 */
  getManuscript: (id: string) =>
    client.get<{ data: Manuscript }>(`/writer/manuscripts/${id}`),

  /** 更新手稿 */
  updateManuscript: (id: string, data: UpdateManuscriptInput) =>
    client.put<{ data: Manuscript }>(`/writer/manuscripts/${id}`, data),

  /** 删除手稿 */
  deleteManuscript: (id: string) =>
    client.delete<{ data: unknown }>(`/writer/manuscripts/${id}`),

  // ── Stats ──────────────────────────────────────────────────────────

  /** 获取写作统计 */
  getStats: () =>
    client.get<{ data: WriterStats }>('/writer/stats'),
}
