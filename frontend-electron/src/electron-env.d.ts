// Global type declarations for the preload-exposed API
export {}

declare global {
  interface Window {
    oristudio: import('../src/main/preload').AppAPI
  }
}
