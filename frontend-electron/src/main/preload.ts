// src/main/preload.ts — Secure bridge between Electron main process and Vue renderer
import { contextBridge, ipcRenderer } from 'electron'

export interface ScreenInfo {
  width: number
  height: number
  scaleFactor: number
}

export interface ShortcutPayload {
  key: string
  ctrlKey: boolean
  metaKey: boolean
  shiftKey: boolean
}

export interface AppAPI {
  toggleFullscreen: () => Promise<boolean>
  getFullscreenState: () => Promise<boolean>
  minimize: () => void
  maximize: () => void
  close: () => void
  getScreenInfo: () => Promise<ScreenInfo>
  onShortcut: (handler: (payload: ShortcutPayload) => void) => void
  offShortcut: (handler: (payload: ShortcutPayload) => void) => void
}

const api: AppAPI = {
  toggleFullscreen: () => ipcRenderer.invoke('app:toggle-fullscreen'),
  getFullscreenState: () => ipcRenderer.invoke('app:get-fullscreen'),
  minimize: () => ipcRenderer.invoke('app:minimize'),
  maximize: () => ipcRenderer.invoke('app:maximize'),
  close: () => ipcRenderer.invoke('app:close'),
  getScreenInfo: () => ipcRenderer.invoke('app:get-screen-info'),

  onShortcut: (handler) => {
    const listener = (_event: Electron.IpcRendererEvent, payload: ShortcutPayload) => handler(payload)
    ipcRenderer.on('app:shortcut-reply', listener)
    // Attach to API object for cleanup
    ;(api as Record<string, unknown>)._shortcutListener = listener
    ;(api as Record<string, unknown>)._shortcutHandler = handler
  },

  offShortcut: (handler) => {
    const listener = (api as Record<string, unknown>)._shortcutListener
    const storedHandler = (api as Record<string, unknown>)._shortcutHandler
    if (listener && handler === storedHandler) {
      ipcRenderer.off('app:shortcut-reply', listener)
    }
  },
}

contextBridge.exposeInMainWorld('oristudio', api)
