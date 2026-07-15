<template>
  <div class="writer-view">
    <!-- Stats Bar -->
    <div class="stats-bar animate-fade-in">
      <div
        v-for="(metric, i) in statMetrics"
        :key="i"
        class="stat-item"
      >
        <div class="stat-icon">{{ metric.icon }}</div>
        <div class="stat-value">{{ metric.value }}</div>
        <div class="stat-label">{{ metric.label }}</div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 1: Articles
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'articles'" class="tab-panel animate-fade-in">
      <div class="toolbar">
        <div class="toolbar-filters">
          <select v-model="articleFilter.status" class="form-select">
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="published">已发布</option>
            <option value="archived">归档</option>
          </select>
          <select v-model="articleFilter.category" class="form-select">
            <option value="">全部分类</option>
            <option v-for="c in categoryOptions" :key="c" :value="c">{{ categoryLabels[c] }}</option>
          </select>
          <input
            v-model="articleSearch"
            class="form-input"
            placeholder="搜索文章标题..."
            style="width:220px"
          />
        </div>
        <button class="btn btn-primary" @click="showArticleModal = true">+ 新建文章</button>
      </div>

      <div v-if="writerStore.loading && !filteredArticles.length" class="center-loading">加载中...</div>

      <div v-else-if="!filteredArticles.length" class="empty-state-card">
        <div class="empty-icon">📝</div>
        <div class="empty-title">暂无文章</div>
        <div class="empty-desc">开始写作你的第一篇文章</div>
        <button class="btn btn-primary" @click="showArticleModal = true">+ 新建文章</button>
      </div>

      <div v-else class="card-grid">
        <div v-for="a in filteredArticles" :key="a.id" class="article-card card">
          <div class="card-header">
            <strong class="card-title">{{ a.title }}</strong>
            <StatusBadge
              :status="a.status"
              :labels="{ draft: '草稿', published: '已发布', archived: '归档' }"
              :variants="{ draft: 'info', published: 'success', archived: 'default' }"
            />
          </div>

          <div v-if="a.subtitle" class="card-subtitle">{{ a.subtitle }}</div>
          <div v-if="a.excerpt" class="card-excerpt">{{ a.excerpt }}</div>

          <div class="card-meta-row">
            <span v-if="a.category" class="tag">{{ categoryLabels[a.category] }}</span>
            <span v-for="tag in (a.tags || []).slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
          </div>

          <div class="card-stats-row">
            <span class="stat-pill">{{ fmtWords(a.word_count) }}</span>
            <span class="stat-pill">{{ a.reading_time_minutes || 0 }} 分钟阅读</span>
            <span v-if="a.published_at" class="stat-pill">{{ formatDate(a.published_at) }}</span>
          </div>

          <div class="card-actions">
            <button class="btn btn-sm btn-secondary" @click="editArticle(a)">编辑</button>
            <button class="btn btn-sm btn-danger" @click="confirmDeleteArticle(a)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 2: Books
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'books'" class="tab-panel animate-fade-in">
      <div class="toolbar">
        <div class="toolbar-filters">
          <select v-model="bookFilter.status" class="form-select">
            <option value="">全部状态</option>
            <option value="writing">创作中</option>
            <option value="published">已出版</option>
            <option value="archived">已归档</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="showBookModal = true">+ 新书籍</button>
      </div>

      <div v-if="writerStore.loading && !writerStore.books.length" class="center-loading">加载中...</div>

      <div v-else-if="!writerStore.books.length" class="empty-state-card">
        <div class="empty-icon">📚</div>
        <div class="empty-title">暂无书籍</div>
        <div class="empty-desc">创建你的第一本书籍</div>
        <button class="btn btn-primary" @click="showBookModal = true">+ 新书籍</button>
      </div>

      <div v-else class="book-grid">
        <div v-for="b in writerStore.books" :key="b.id" class="book-card card">
          <div v-if="b.cover_path" class="book-cover">
            <img :src="`/api/files/${b.cover_path}`" :alt="b.title" />
          </div>
          <div v-else class="book-cover-placeholder">
            <span>📖</span>
          </div>

          <div class="book-info">
            <strong class="book-title">{{ b.title }}</strong>
            <StatusBadge
              :status="b.status"
              :labels="{ writing: '创作中', published: '已出版', archived: '已归档' }"
              :variants="{ writing: 'info', published: 'success', archived: 'default' }"
            />
            <div v-if="b.genre" class="book-genre">{{ genreLabels[b.genre] }}</div>
            <div v-if="b.publisher" class="book-detail">出版社: {{ b.publisher }}</div>
            <div v-if="b.isbn" class="book-detail">ISBN: {{ b.isbn }}</div>
            <div v-if="b.publication_date" class="book-detail">出版日期: {{ formatDate(b.publication_date) }}</div>
          </div>

          <div class="book-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: bookProgress(b) + '%' }"></div>
            </div>
            <span class="progress-label">{{ b.total_chapters || 0 }} 章 · {{ fmtWords(b.total_word_count) }}</span>
          </div>

          <div class="card-actions">
            <button class="btn btn-sm btn-secondary" @click="editBook(b)">编辑</button>
            <button class="btn btn-sm btn-danger" @click="confirmDeleteBook(b)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 3: Manuscripts
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'manuscripts'" class="tab-panel animate-fade-in">
      <div class="toolbar">
        <div class="toolbar-filters">
          <select v-model="manuscriptFilter.bookId" class="form-select">
            <option value="">全部书籍</option>
            <option v-for="b in writerStore.books" :key="b.id" :value="b.id">{{ b.title }}</option>
          </select>
          <select v-model="manuscriptFilter.status" class="form-select">
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="revising">修改中</option>
            <option value="final">终稿</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="showManuscriptModal = true">+ 新章节</button>
      </div>

      <div v-if="writerStore.loading && !writerStore.manuscripts.length" class="center-loading">加载中...</div>

      <div v-else-if="!writerStore.manuscripts.length" class="empty-state-card">
        <div class="empty-icon">✍️</div>
        <div class="empty-title">暂无手稿</div>
        <div class="empty-desc">为你的书籍创建第一个章节手稿</div>
        <button class="btn btn-primary" @click="showManuscriptModal = true">+ 新章节</button>
      </div>

      <div v-else class="manuscript-list">
        <div v-for="m in filteredManuscripts" :key="m.id" class="manuscript-row card">
          <div class="ms-header">
            <div class="ms-chapter-badge">第 {{ m.chapter_number }} 章</div>
            <strong class="ms-title">{{ m.title }}</strong>
            <StatusBadge
              :status="m.status"
              :labels="{ draft: '草稿', revising: '修改中', final: '终稿' }"
              :variants="{ draft: 'info', revising: 'warning', final: 'success' }"
            />
            <span class="ms-version">v{{ m.version }}</span>
          </div>

          <div class="ms-body">
            <span class="stat-pill">{{ fmtWords(m.word_count) }}</span>
            <span v-if="m.book_id" class="ms-book-link" @click="switchToBook(m.book_id)">{{ getBookTitle(m.book_id) }}</span>
            <span class="ms-date">{{ formatDate(m.updated_at) }}</span>
          </div>

          <div class="ms-actions">
            <button class="btn btn-sm btn-secondary" @click="editManuscript(m)">编辑</button>
            <button class="btn btn-sm btn-danger" @click="confirmDeleteManuscript(m)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Modals
         ═══════════════════════════════════════════════════════════ -->

    <!-- Article Modal -->
    <div v-if="showArticleModal" class="modal-overlay" @click.self="showArticleModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header">
          <h3>{{ editingArticleId ? '编辑文章' : '新建文章' }}</h3>
          <button class="modal-close-btn" @click="showArticleModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>标题</label>
          <input v-model.trim="articleForm.title" class="form-input" placeholder="文章标题" />
        </div>
        <div class="form-group">
          <label>副标题</label>
          <input v-model.trim="articleForm.subtitle" class="form-input" placeholder="可选的副标题" />
        </div>
        <div class="form-group">
          <label>简介/摘要</label>
          <textarea v-model.trim="articleForm.excerpt" class="form-input" rows="2" placeholder="文章摘要"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>分类</label>
            <select v-model="articleForm.category" class="form-input">
              <option v-for="c in categoryOptions" :key="c" :value="c">{{ categoryLabels[c] }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="articleForm.status" class="form-input">
              <option value="draft">草稿</option>
              <option value="published">已发布</option>
              <option value="archived">归档</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>标签 (逗号分隔)</label>
          <input v-model="articleTagsRaw" class="form-input" placeholder="Vue, TypeScript, 前端" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showArticleModal = false">取消</button>
          <button class="btn btn-primary" @click="saveArticle">{{ editingArticleId ? '保存修改' : '创建文章' }}</button>
        </div>
      </div>
    </div>

    <!-- Book Modal -->
    <div v-if="showBookModal" class="modal-overlay" @click.self="showBookModal = false">
      <div class="modal-card animate-scale-in" style="max-width:520px">
        <div class="modal-header">
          <h3>{{ editingBookId ? '编辑书籍' : '新书籍' }}</h3>
          <button class="modal-close-btn" @click="showBookModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>书名</label>
          <input v-model.trim="bookForm.title" class="form-input" placeholder="书名" />
        </div>
        <div class="form-group">
          <label>类型</label>
          <select v-model="bookForm.genre" class="form-input">
            <option v-for="g in genreOptions" :key="g" :value="g">{{ genreLabels[g] }}</option>
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>出版社</label>
            <input v-model.trim="bookForm.publisher" class="form-input" placeholder="可选" />
          </div>
          <div class="form-group">
            <label>ISBN</label>
            <input v-model.trim="bookForm.isbn" class="form-input" placeholder="978-X-XXX-XXXXX-X" />
          </div>
        </div>
        <div class="form-group">
          <label>简介</label>
          <textarea v-model.trim="bookForm.description" class="form-input" rows="3" placeholder="内容简介"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>状态</label>
            <select v-model="bookForm.status" class="form-input">
              <option value="writing">创作中</option>
              <option value="published">已出版</option>
              <option value="archived">已归档</option>
            </select>
          </div>
          <div class="form-group">
            <label>出版日期</label>
            <input v-model="bookForm.publication_date" type="date" class="form-input" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showBookModal = false">取消</button>
          <button class="btn btn-primary" @click="saveBook">{{ editingBookId ? '保存修改' : '创建书籍' }}</button>
        </div>
      </div>
    </div>

    <!-- Manuscript Edit Modal (for content editing) -->
    <div v-if="showManuscriptEditor" class="modal-overlay" @click.self="showManuscriptEditor = false">
      <div class="modal-card animate-scale-in" style="max-width:800px; max-height:90vh; overflow-y:auto;">
        <div class="modal-header">
          <h3>编辑章节</h3>
          <button class="modal-close-btn" @click="showManuscriptEditor = false">&times;</button>
        </div>
        <ManuscriptEditor
          v-if="currentManuscriptForEditor"
          :manuscript="currentManuscriptForEditor"
          :on-save="handleManuscriptSave"
          :on-publish="handleManuscriptPublish"
        />
      </div>
    </div>

    <!-- Manuscript Create/Edit Simple Modal (for metadata only) -->
    <div v-if="showManuscriptModal" class="modal-overlay" @click.self="showManuscriptModal = false">
      <div class="modal-card animate-scale-in" style="max-width:520px">
        <div class="modal-header">
          <h3>{{ editingManuscriptId ? '编辑章节' : '新章节' }}</h3>
          <button class="modal-close-btn" @click="showManuscriptModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>所属书籍</label>
          <select v-model="manuscriptForm.book_id" class="form-input">
            <option value="">-- 选择书籍 --</option>
            <option v-for="b in writerStore.books" :key="b.id" :value="b.id">{{ b.title }}</option>
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>章节号</label>
            <input v-model.number="manuscriptForm.chapter_number" type="number" min="1" class="form-input" />
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="manuscriptForm.status" class="form-input">
              <option value="draft">草稿</option>
              <option value="revising">修改中</option>
              <option value="final">终稿</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>章节标题</label>
          <input v-model.trim="manuscriptForm.title" class="form-input" placeholder="第一章: ..." />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showManuscriptModal = false">取消</button>
          <button class="btn btn-primary" @click="saveManuscript">{{ editingManuscriptId ? '保存修改' : '创建章节' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ManuscriptEditor from '@/components/writer/ManuscriptEditor.vue'
import { useWriterStore } from '@/stores/useWriterStore'
import type {
  Article,
  Book,
  Manuscript,
  ArticleCategory,
  BookGenre,
  ManuscriptStatus,
  CreateArticleInput,
  CreateBookInput,
  CreateManuscriptInput,
} from '@/types/writer'

const writerStore = useWriterStore()

const activeTab = ref<'articles' | 'books' | 'manuscripts'>('articles')

// ── Tab definitions ──────────────────────────────────────────────

const tabs = [
  { key: 'articles' as const, label: '文章管理', icon: '📝' },
  { key: 'books' as const, label: '书籍管理', icon: '📚' },
  { key: 'manuscripts' as const, label: '手稿', icon: '✍️' },
]

// ── Category / Genre Labels ──────────────────────────────────────

const categoryLabels: Record<string, string> = {
  tech: '科技', literature: '文学', history: '历史', art: '艺术', science: '科学', other: '其他',
}
const categoryOptions: ArticleCategory[] = ['tech', 'literature', 'history', 'art', 'science', 'other']

const genreLabels: Record<string, string> = {
  novel: '小说', essay: '散文', poetry: '诗歌', academic: '学术', other: '其他',
}
const genreOptions: BookGenre[] = ['novel', 'essay', 'poetry', 'academic', 'other']

// ── Stats Bar ────────────────────────────────────────────────────

const statMetrics = computed(() => [
  { icon: '📝', label: '总文章数', value: String(writerStore.stats.total_articles) },
  { icon: '✅', label: '已发布', value: String(writerStore.stats.published_count) },
  { icon: '📖', label: '总字数', value: fmtWords(writerStore.stats.total_words) },
  { icon: '📚', label: '活跃书籍', value: String(writerStore.stats.active_books) },
  { icon: '👁️', label: '月阅读', value: String(writerStore.stats.monthly_reads) },
])

// ── Article Filters ──────────────────────────────────────────────

const articleFilter = ref({ status: '', category: '' })
const articleSearch = ref('')

const filteredArticles = computed(() => {
  let list: Article[] = writerStore.articles
  if (articleFilter.value.status) {
    list = list.filter((a: Article) => a.status === articleFilter.value.status)
  }
  if (articleFilter.value.category) {
    list = list.filter((a: Article) => a.category === articleFilter.value.category)
  }
  if (articleSearch.value.trim()) {
    const q = articleSearch.value.toLowerCase()
    list = list.filter((a: Article) => a.title.toLowerCase().includes(q))
  }
  return list
})

// ── Book Filters ─────────────────────────────────────────────────

const bookFilter = ref({ status: '' })

// ── Manuscript Filters ───────────────────────────────────────────

const manuscriptFilter = ref({ bookId: '', status: '' })

const filteredManuscripts = computed(() => {
  let list: Manuscript[] = writerStore.manuscripts
  if (manuscriptFilter.value.bookId) {
    list = list.filter((m: Manuscript) => m.book_id === manuscriptFilter.value.bookId)
  }
  if (manuscriptFilter.value.status) {
    list = list.filter((m: Manuscript) => m.status === manuscriptFilter.value.status)
  }
  return list
})

// ── Modal: Articles ─────────────────────────────────────────────

const showArticleModal = ref(false)
const editingArticleId = ref<string | null>(null)
const articleForm = ref({
  title: '', subtitle: '', excerpt: '', category: '' as ArticleCategory | '', status: 'draft' as Article['status'], tags: [] as string[],
})
const articleTagsRaw = ref('')

function openArticleForm(article?: Article) {
  if (article) {
    editingArticleId.value = article.id
    articleForm.value = {
      title: article.title, subtitle: article.subtitle || '', excerpt: article.excerpt || '',
      category: article.category || '', status: article.status, tags: article.tags || [],
    }
    articleTagsRaw.value = (article.tags || []).join(', ')
  } else {
    editingArticleId.value = null
    articleForm.value = { title: '', subtitle: '', excerpt: '', category: '', status: 'draft', tags: [] }
    articleTagsRaw.value = ''
  }
  showArticleModal.value = true
}

function editArticle(a: Article) { openArticleForm(a) }

async function saveArticle() {
  const { title, subtitle, excerpt, category, status } = articleForm.value
  if (!title) {
    ;(window as any).$toast?.show('请输入文章标题', 'warning')
    return
  }
  const tags = articleTagsRaw.value.split(/[,，]/).map((t) => t.trim()).filter(Boolean)
  const input: CreateArticleInput = { title, subtitle: subtitle || undefined, excerpt: excerpt || undefined, category: category || undefined, tags: tags.length ? tags : undefined, status }

  if (editingArticleId.value) {
    const updated = await writerStore.updateArticle(editingArticleId.value, input as Partial<Article>)
    if (updated) {
      ;(window as any).$toast?.show('文章已更新', 'success')
      showArticleModal.value = false
    }
  } else {
    const created = await writerStore.createArticle(input)
    if (created) {
      ;(window as any).$toast?.show('文章已创建', 'success')
      showArticleModal.value = false
    }
  }
}

async function confirmDeleteArticle(a: Article) {
  if (confirm(`确定删除《${a.title}》？`)) {
    const ok = await writerStore.deleteArticle(a.id)
    if (ok) {
      ;(window as any).$toast?.show('文章已删除', 'success')
    }
  }
}

// ── Modal: Books ─────────────────────────────────────────────────

const showBookModal = ref(false)
const editingBookId = ref<string | null>(null)
const bookForm = ref({
  title: '', cover_path: '', description: '', genre: '' as BookGenre | '', publisher: '', isbn: '',
  publication_date: '', status: 'writing' as Book['status'],
})

function openBookForm(book?: Book) {
  if (book) {
    editingBookId.value = book.id
    bookForm.value = {
      title: book.title, cover_path: book.cover_path || '', description: book.description || '',
      genre: book.genre || '', publisher: book.publisher || '', isbn: book.isbn || '',
      publication_date: book.publication_date || '', status: book.status,
    }
  } else {
    editingBookId.value = null
    bookForm.value = { title: '', cover_path: '', description: '', genre: '', publisher: '', isbn: '', publication_date: '', status: 'writing' }
  }
  showBookModal.value = true
}

function editBook(b: Book) { openBookForm(b) }

async function saveBook() {
  const { title } = bookForm.value
  if (!title) {
    ;(window as any).$toast?.show('请输入书名', 'warning')
    return
  }
  const input: CreateBookInput = {
    title, cover_path: bookForm.value.cover_path || undefined,
    description: bookForm.value.description || undefined,
    genre: bookForm.value.genre || undefined,
    publisher: bookForm.value.publisher || undefined,
    isbn: bookForm.value.isbn || undefined,
    publication_date: bookForm.value.publication_date || undefined,
    status: bookForm.value.status,
  }

  if (editingBookId.value) {
    const updated = await writerStore.updateBook(editingBookId.value, input as Partial<Book>)
    if (updated) {
      ;(window as any).$toast?.show('书籍已更新', 'success')
      showBookModal.value = false
    }
  } else {
    const created = await writerStore.createBook(input)
    if (created) {
      ;(window as any).$toast?.show('书籍已创建', 'success')
      showBookModal.value = false
    }
  }
}

async function confirmDeleteBook(b: Book) {
  if (confirm(`确定删除《${b.title}》？`)) {
    const ok = await writerStore.deleteBook(b.id)
    if (ok) {
      ;(window as any).$toast?.show('书籍已删除', 'success')
    }
  }
}

// ── Modal: Manuscripts ───────────────────────────────────────────

const showManuscriptModal = ref(false)
const editingManuscriptId = ref<string | null>(null)
const manuscriptForm = ref({
  title: '', book_id: '' as string | undefined, chapter_number: 1,
  status: 'draft' as ManuscriptStatus, version: 1,
})

// Manuscript editor state (for content editing via ManuscriptEditor component)
const showManuscriptEditor = ref(false)
const currentManuscriptForEditor = ref<Manuscript | null>(null)

function openManuscriptForm(ms?: Manuscript) {
  if (ms) {
    editingManuscriptId.value = ms.id
    manuscriptForm.value = {
      title: ms.title, book_id: ms.book_id, chapter_number: ms.chapter_number || 1,
      status: ms.status, version: ms.version,
    }
  } else {
    editingManuscriptId.value = null
    manuscriptForm.value = { title: '', book_id: undefined, chapter_number: 1, status: 'draft', version: 1 }
  }
  showManuscriptModal.value = true
}

function editManuscript(m: Manuscript) {
  // Use ManuscriptEditor component for content editing
  currentManuscriptForEditor.value = { ...m }
  showManuscriptEditor.value = true
}

async function handleManuscriptSave(ms: Manuscript, content: string) {
  if (!ms.id) return
  try {
    const updated = await writerStore.updateManuscript(ms.id, {
      title: ms.title,
      content,
    } as Partial<Manuscript>)
    if (updated) {
      currentManuscriptForEditor.value = updated
      ;(window as any)?.$toast?.show('章节已更新', 'success')
      showManuscriptEditor.value = false
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    ;(window as any)?.$toast?.show(msg, 'error')
  }
}

async function handleManuscriptPublish(ms: Manuscript, content: string, status: ManuscriptStatus) {
  if (!ms.id) return
  try {
    const updated = await writerStore.updateManuscript(ms.id, {
      title: ms.title,
      content,
      status,
    } as Partial<Manuscript>)
    if (updated) {
      currentManuscriptForEditor.value = updated
      showManuscriptEditor.value = false
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '发布失败'
    ;(window as any)?.$toast?.show(msg, 'error')
  }
}

async function confirmDeleteManuscript(m: Manuscript) {
  if (confirm(`确定删除第 ${m.chapter_number} 章《${m.title}》？`)) {
    const ok = await writerStore.deleteManuscript(m.id)
    if (ok) {
      ;(window as any).$toast?.show('章节已删除', 'success')
    }
  }
}

// ── Save Manuscript (modal form) ─────────────────────────────────

async function saveManuscript() {
  const { title, book_id, chapter_number, status } = manuscriptForm.value
  if (!title) {
    ;(window as any).$toast?.show('请输入章节标题', 'warning')
    return
  }
  if (editingManuscriptId.value) {
    // Update existing
    const updated = await writerStore.updateManuscript(editingManuscriptId.value, {
      title, chapter_number, status,
    })
    if (updated) {
      editingManuscriptId.value = null
      showManuscriptModal.value = false
      ;(window as any).$toast?.show('章节已更新', 'success')
    }
  } else {
    // Create new
    const created = await writerStore.createManuscript({
      title, book_id, chapter_number: chapter_number ?? 1, status, version: 1,
    })
    if (created) {
      editingManuscriptId.value = null
      showManuscriptModal.value = false
      ;(window as any).$toast?.show('章节已创建', 'success')
    }
  }
}

// ── Helpers ──────────────────────────────────────────────────────

function fmtWords(n?: number): string {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, '') + '万'
  return n.toLocaleString('zh-CN')
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '-'
  return dateStr.slice(0, 10)
}

function bookProgress(b: Book): number {
  if (!b.total_chapters) return 0
  const completed = writerStore.manuscripts.filter(
    (m: Manuscript) => m.book_id === b.id && m.status === 'final'
  ).length
  return Math.min(100, Math.round((completed / b.total_chapters) * 100))
}

function getBookTitle(bookId: string): string {
  return writerStore.books.find((b: Book) => b.id === bookId)?.title || bookId
}

function switchToBook(bookId: string) {
  const book = writerStore.books.find((b: Book) => b.id === bookId)
  if (book) {
    activeTab.value = 'books'
  }
}

// ── Lifecycle ────────────────────────────────────────────────────

onMounted(() => {
  writerStore.fetchAll()
})
</script>

<style scoped>
.writer-view { display: flex; flex-direction: column; gap: 20px; }

/* ── Stats Bar ─────────────────────────────────────────────────── */
.stats-bar { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 14px; }
.stat-item { padding: 16px 20px; text-align: center; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); }
.stat-icon { font-size: 1.4rem; margin-bottom: 4px; }
.stat-value { font-size: 1.3rem; font-weight: 800; color: var(--fg); }
.stat-label { font-size: 0.74rem; color: var(--muted); margin-top: 2px; }

/* ── Tab Bar ───────────────────────────────────────────────────── */
.tab-bar { display: flex; gap: 8px; flex-wrap: wrap; }
.tab-btn { padding: 8px 20px; border-radius: 100px; font-size: 0.84rem; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: var(--surface); color: var(--muted); font-family: var(--font-body); transition: all .2s; }
.tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

/* ── Toolbar ───────────────────────────────────────────────────── */
.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.toolbar-filters { display: flex; gap: 8px; flex-wrap: wrap; }
.form-select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.82rem; font-family: var(--font-body); background: var(--surface); color: var(--fg); outline: none; cursor: pointer; }
.form-select:focus { border-color: var(--accent); }

/* ── Card Grid ─────────────────────────────────────────────────── */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
.card { padding: 18px 20px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md); display: flex; flex-direction: column; gap: 10px; }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.card-title { font-size: 0.95rem; font-weight: 700; }
.card-subtitle { font-size: 0.82rem; color: var(--muted); font-style: italic; }
.card-excerpt { font-size: 0.82rem; color: var(--fg); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-meta-row { display: flex; gap: 4px; flex-wrap: wrap; }
.card-stats-row { display: flex; gap: 8px; flex-wrap: wrap; }
.card-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }

/* ── Tags & Pills ──────────────────────────────────────────────── */
.tag { padding: 2px 10px; border-radius: 100px; font-size: 0.68rem; background: oklch(56% 0.12 170 / .1); color: var(--accent); }
.stat-pill { font-size: 0.72rem; color: var(--muted); padding: 2px 8px; background: oklch(0 0 0 / .03); border-radius: 100px; }

/* ── Buttons ───────────────────────────────────────────────────── */
.btn { padding: 10px 20px; border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; font-family: var(--font-body); transition: all .2s; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { filter: brightness(1.1); }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-secondary { background: var(--surface); color: var(--fg); border: 1px solid var(--border); }
.btn-secondary:hover { background: var(--border); }
.btn-sm { padding: 4px 12px; font-size: 0.74rem; }
.btn-danger { background: oklch(56% 0.18 20 / .1); color: oklch(56% 0.18 20); border: 1px solid oklch(56% 0.18 20 / .2); }
.btn-danger:hover { background: oklch(56% 0.18 20 / .15); }

/* ── Empty State ───────────────────────────────────────────────── */
.empty-state-card { padding: 60px 20px; text-align: center; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); }
.empty-icon { font-size: 3rem; opacity: 0.6; margin-bottom: 12px; }
.empty-title { font-size: 1rem; font-weight: 600; color: var(--fg); }
.empty-desc { font-size: 0.82rem; color: var(--muted); margin: 4px 0 16px; }
.center-loading { text-align: center; padding: 40px; color: var(--muted); }

/* ── Book Card ─────────────────────────────────────────────────── */
.book-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
.book-card { overflow: hidden; }
.book-cover { width: 100%; height: 200px; overflow: hidden; background: var(--surface); }
.book-cover img { width: 100%; height: 100%; object-fit: cover; }
.book-cover-placeholder { width: 100%; height: 200px; display: flex; align-items: center; justify-content: center; font-size: 3rem; background: var(--surface); }
.book-info { display: flex; flex-direction: column; gap: 4px; margin-top: 10px; }
.book-title { font-size: 0.95rem; }
.book-genre { font-size: 0.78rem; color: var(--accent); font-weight: 600; }
.book-detail { font-size: 0.74rem; color: var(--muted); }
.book-progress { margin-top: 8px; }
.progress-bar { width: 100%; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 4px; }
.progress-fill { height: 100%; background: var(--accent); border-radius: 3px; transition: width .3s; }
.progress-label { font-size: 0.72rem; color: var(--muted); }

/* ── Manuscript Row ────────────────────────────────────────────── */
.manuscript-list { display: flex; flex-direction: column; gap: 8px; }
.manuscript-row { display: flex; flex-direction: column; gap: 8px; }
.ms-header { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.ms-chapter-badge { padding: 2px 10px; border-radius: var(--radius-sm); font-size: 0.74rem; font-weight: 700; background: oklch(56% 0.12 250 / .1); color: oklch(56% 0.12 250); }
.ms-title { font-size: 0.9rem; font-weight: 600; }
.ms-version { font-size: 0.72rem; color: var(--muted); }
.ms-body { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.ms-book-link { font-size: 0.78rem; color: var(--accent); cursor: pointer; text-decoration: underline; }
.ms-date { font-size: 0.72rem; color: var(--muted); margin-left: auto; }

/* ── Modal ─────────────────────────────────────────────────────── */
.modal-overlay { position: fixed; inset: 0; background: oklch(0 0 0 / .4); backdrop-filter: blur(4px); z-index: 9998; display: flex; align-items: center; justify-content: center; }
.modal-card { background: var(--surface); border-radius: var(--radius-xl); padding: 28px; max-width: 520px; width: 90%; box-shadow: 0 16px 64px oklch(0 0 0 / .16); display: flex; flex-direction: column; gap: 14px; }
.modal-header { display: flex; align-items: center; justify-content: space-between; }
.modal-header h3 { margin: 0; font-size: 1rem; }
.modal-close-btn { background: none; border: none; cursor: pointer; font-size: 1.4rem; color: var(--muted); }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; }

/* ── Form ──────────────────────────────────────────────────────── */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input { padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.88rem; font-family: var(--font-body); color: var(--fg); background: var(--surface); outline: none; }
.form-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / .1); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
textarea.form-input { resize: vertical; }

/* ── Animations ────────────────────────────────────────────────── */
.animate-fade-in { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.animate-scale-in { animation: scaleIn .2s ease; }
@keyframes scaleIn { from { opacity: 0; transform: scale(.96); } to { opacity: 1; transform: scale(1); } }
</style>
