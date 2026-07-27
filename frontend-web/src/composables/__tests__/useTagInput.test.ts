import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useTagInput } from '@/composables/useTagInput'

describe('useTagInput', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('starts with empty tags', () => {
    const { tags } = useTagInput()
    expect(tags.value).toHaveLength(0)
  })

  it('initializes with provided tags (deep copy)', () => {
    const initial = [{ id: '1', tag: 'existing' }]
    const { tags } = useTagInput(initial)
    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].tag).toBe('existing')

    // Mutating initial should not affect the ref
    initial[0].tag = 'mutated'
    expect(tags.value[0].tag).toBe('existing')
  })

  it('adds a new tag', () => {
    const { tags, addTag } = useTagInput()
    addTag('new tag')
    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].tag).toBe('new tag')
    expect(tags.value[0].id).toBe('')
  })

  it('prevents duplicate tags', () => {
    const { tags, addTag } = useTagInput()
    addTag('same')
    addTag('same')
    expect(tags.value).toHaveLength(1)
  })

  it('removes a tag by index', () => {
    const { tags, removeTag, addTag } = useTagInput()
    addTag('first')
    addTag('second')
    removeTag(0)
    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].tag).toBe('second')
  })

  it('clears all tags via reset', () => {
    const { tags, inputVal, suggestions, showSuggestions, addTag, reset } = useTagInput()
    addTag('tag1')
    addTag('tag2')
    inputVal.value = 'typing...'
    suggestions.value = ['sug1']
    showSuggestions.value = true

    reset()

    expect(tags.value).toHaveLength(0)
    expect(inputVal.value).toBe('')
    expect(suggestions.value).toHaveLength(0)
    expect(showSuggestions.value).toBe(false)
  })

  it('handles Enter key to add tag', async () => {
    const { tags, onKeydown, inputVal } = useTagInput()
    inputVal.value = 'hello'

    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' })
    onKeydown(enterEvent)

    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].tag).toBe('hello')
    expect(inputVal.value).toBe('')
  })

  it('does not add empty tag on Enter', () => {
    const { tags, onKeydown, inputVal } = useTagInput()
    inputVal.value = ''

    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' })
    onKeydown(enterEvent)

    expect(tags.value).toHaveLength(0)
  })

  it('removes last tag on Backspace when input is empty', () => {
    const { tags, onKeydown, addTag } = useTagInput()
    addTag('first')
    addTag('second')

    const backspaceEvent = new KeyboardEvent('keydown', { key: 'Backspace' })
    onKeydown(backspaceEvent)

    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].tag).toBe('first')
  })

  it('does not remove on Backspace when tags is empty', () => {
    const { tags, onKeydown } = useTagInput()
    const backspaceEvent = new KeyboardEvent('keydown', { key: 'Backspace' })
    onKeydown(backspaceEvent)
    expect(tags.value).toHaveLength(0)
  })

  it('hides suggestions on Escape', () => {
    const { showSuggestions, onKeydown } = useTagInput()
    showSuggestions.value = true

    const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' })
    onKeydown(escapeEvent)

    expect(showSuggestions.value).toBe(false)
  })

  it('clears suggestions when query is empty', async () => {
    const { onInput, suggestions, showSuggestions } = useTagInput()
    showSuggestions.value = true
    suggestions.value = ['some']

    onInput('')
    vi.advanceTimersByTime(300)

    expect(suggestions.value).toHaveLength(0)
    expect(showSuggestions.value).toBe(false)
  })

  it('addSuggestion adds by index', () => {
    const { suggestions, addSuggestion, tags } = useTagInput()
    suggestions.value = ['first', 'second', 'third']
    addSuggestion(1)
    expect(tags.value).toHaveLength(1)
    expect(tags.value[0].tag).toBe('second')
  })

  it('addSuggestion clears suggestions after adding', () => {
    const { suggestions, addSuggestion } = useTagInput()
    suggestions.value = ['a', 'b']
    addSuggestion(0)
    expect(suggestions.value).toHaveLength(0)
  })
})
