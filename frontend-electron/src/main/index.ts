// src/main/index.ts — Electron main process
import { app, BrowserWindow, ipcMain, screen, shell } from 'electron'
import * as path from 'path'

const IS_DEV = process.env.NODE_ENV === 'development' || !!process.argv.includes('--dev')

function createWindow(): BrowserWindow {
  const primaryDisplay = screen.getPrimaryDisplay()
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize

  const windowWidth = Math.min(1440, screenWidth)
  const windowHeight = Math.min(900, screenHeight)
  const x = Math.floor((screenWidth - windowWidth) / 2)
  const y = Math.floor((screenHeight - windowHeight) / 2)

  const mainWindow = new BrowserWindow({
    width: windowWidth,
    height: windowHeight,
    x,
    y,
    minWidth: 1024,
    minHeight: 768,
    titleBarStyle: 'hidden',
    frame: false,
    title: 'OriStudio — 创作者全链路助手',
    icon: path.resolve(__dirname, '../../frontend-web/public/favicon.svg'),
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.resolve(__dirname, 'preload.js'),
      webgl: true,
      webSecurity: false,
    },
  })

  if (IS_DEV) {
    mainWindow.loadURL('http://localhost:5175')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.resolve(__dirname, '../../dist/web/index.html'))
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  // Security: custom CSP
  mainWindow.webContents.session.webRequest.onHeadersReceived((_details, callback) => {
    callback({
      responseHeaders: {
        ...(_details.responseHeaders ?? {}),
        'Content-Security-Policy': [
          "default-src 'self'; " +
          "script-src 'self' 'unsafe-eval'; " +
          "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
          "font-src 'self' https://fonts.gstatic.com; " +
          "img-src 'self' data: https:; " +
          "connect-src 'self' http://localhost:* ws://localhost:*;",
        ],
      },
    })
  })

  // Open external links in system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://') || url.startsWith('http://')) {
      shell.openExternal(url)
    }
    return { action: 'deny' }
  })

  return mainWindow
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────

let cleanupShortcuts: (() => void) | null = null

// Global shortcut: F11 or Cmd/Ctrl+Shift+M toggles immersive mode
const registerShortcuts = (win: BrowserWindow): (() => void) => {
  const { globalShortcut } = require('electron') as typeof import('electron')
  const registered =
    globalShortcut.register('F11', () => win.webContents.send('app:shortcut', { key: 'F11' })) &&
    globalShortcut.register('CommandOrControl+Shift+M', () =>
      win.webContents.send('app:shortcut', { key: 'CmdOrCtrl+Shift+M' })
    )
  if (!registered) {
    console.warn('[Main] Failed to register global shortcuts')
  }
  return () => {
    globalShortcut.unregisterAll()
  }
}

app.whenReady().then(() => {
  const mainWindow = createWindow()
  cleanupShortcuts = registerShortcuts(mainWindow)

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      const win = createWindow()
      cleanupShortcuts = registerShortcuts(win)
    }
  })
})

app.on('window-all-closed', () => {
  cleanupShortcuts?.()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('will-quit', () => {
  cleanupShortcuts?.()
})

// ─── IPC Handlers ─────────────────────────────────────────────────────────────

// Fullscreen toggle
ipcMain.handle('app:toggle-fullscreen', (_event) => {
  const win = BrowserWindow.fromWebContents(_event.sender)
  if (!win) return false
  win.setFullScreen(!win.isFullScreen())
  return win.isFullScreen()
})

// Current fullscreen state
ipcMain.handle('app:get-fullscreen', (_event) => {
  const win = BrowserWindow.fromWebContents(_event.sender)
  return win?.isFullScreen() ?? false
})

// Window controls
ipcMain.handle('app:minimize', () => {
  BrowserWindow.fromWebContents(ipcMain.event.sender)?.minimize()
})

ipcMain.handle('app:maximize', () => {
  const win = BrowserWindow.fromWebContents(ipcMain.event.sender)
  if (win?.isMaximized()) {
    win.unmaximize()
  } else {
    win?.maximize()
  }
})

ipcMain.handle('app:close', () => {
  BrowserWindow.fromWebContents(ipcMain.event.sender)?.close()
})

// Screen info for responsive layouts
ipcMain.handle('app:get-screen-info', () => {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize
  const scaleFactor = screen.getPrimaryDisplay().scaleFactor
  return { width, height, scaleFactor }
})

// Forward keyboard shortcuts from renderer back to main
ipcMain.on('app:shortcut', (_event, payload: { key: string; ctrlKey: boolean; metaKey: boolean; shiftKey: boolean }) => {
  _event.sender.send('app:shortcut-reply', payload)
})
