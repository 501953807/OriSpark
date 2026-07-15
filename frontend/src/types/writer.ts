// ── Enumerations ────────────────────────────────────────────────────

export type ArticleStatus = 'draft' | 'published' | 'archived'
export type ArticleCategory = 'tech' | 'literature' | 'history' | 'art' | 'science' | 'other'

export type BookStatus = 'writing' | 'published' | 'archived'
export type BookGenre = 'novel' | 'essay' | 'poetry' | 'academic' | 'other'

export type ManuscriptStatus = 'draft' | 'revising' | 'final'

// ── Domain Entities ────────────────────────────────────────────────

export interface Article {
  id: string
  title: string
  subtitle?: string
  excerpt?: string
  category?: ArticleCategory
  tags?: string[]
  word_count?: number
  reading_time_minutes?: number
  status: ArticleStatus
  published_at?: string
  created_at?: string
  updated_at?: string
}

export interface Book {
  id: string
  title: string
  cover_path?: string
  description?: string
  genre?: BookGenre
  publisher?: string
  isbn?: string
  total_chapters?: number
  total_word_count?: number
  publication_date?: string
  status: BookStatus
  created_at?: string
  updated_at?: string
}

export interface Manuscript {
  id: string
  title: string
  content?: string
  book_id?: string
  chapter_number?: number
  word_count?: number
  status: ManuscriptStatus
  version: number
  created_at?: string
  updated_at?: string
}

export interface WriterStats {
  total_articles: number
  published_count: number
  total_words: number
  active_books: number
  monthly_reads: number
}

// ── Form DTOs (Partial for creation) ───────────────────────────────

export type CreateArticleInput = Omit<Article, 'id' | 'created_at' | 'updated_at'>
export type UpdateArticleInput = Partial<Omit<Article, 'id'>>

export type CreateBookInput = Omit<Book, 'id' | 'created_at' | 'updated_at'>
export type UpdateBookInput = Partial<Omit<Book, 'id'>>

export type CreateManuscriptInput = Omit<Manuscript, 'id' | 'created_at' | 'updated_at'>
export type UpdateManuscriptInput = Partial<Omit<Manuscript, 'id'>>
