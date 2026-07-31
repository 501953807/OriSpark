// app/plugins/motion.ts
import { useMotionStore, initMotionStore } from '@/stores/motion'

export default function initMotionPlugin() {
  // 在客户端初始化 motion store
  if (typeof window !== 'undefined') {
    const store = useMotionStore()
    initMotionStore()
  }
}
