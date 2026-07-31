<!-- app/components/ThreeScene.vue -->
<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useMotionStore } from '@/stores/motion'

// 动态导入 three，避免 SSR 失败
let THREE: any = null

const container = ref<HTMLDivElement | null>(null)
let scene: any = null
let camera: any = null
let renderer: any = null
let particles: any = null
let animationId: number | null = null
const motionStore = useMotionStore()

// Three.js 场景初始化
const initThreeJS = () => {
  if (!container.value || !motionStore.shouldAnimate) return

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0f172a)

  // 创建相机
  const aspect = container.value.clientWidth / container.value.clientHeight
  camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000)
  camera.position.z = 15

  // 创建渲染器（alpha 透明，禁用抗锯齿提升性能）
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, preserveDrawingBuffer: false })
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
  renderer.setPixelRatio(window.devicePixelRatio > 1 ? 1 : 1) // 避免高分屏过度消耗
  container.value.appendChild(renderer.domElement)

  // 创建粒子系统
  createParticles()

  // 开始动画循环
  animate()
}

const createParticles = () => {
  if (!scene || !camera || !motionStore.shouldAnimate) return

  // 根据沉浸级别确定粒子数量
  const count = motionStore.particleCount
  if (count === 0) {
    // 移除已有粒子
    if (particles) {
      scene.remove(particles)
      particles.geometry.dispose()
      particles.material.dispose()
      particles = null
    }
    return
  }

  // 释放之前的粒子
  if (particles) {
    scene.remove(particles)
    particles.geometry.dispose()
    particles.material.dispose()
  }

  // 创建新粒子
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(count * 3)
  const velocities = new Float32Array(count * 3) // 存储速度

  for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 20
    positions[i + 1] = (Math.random() - 0.5) * 15
    positions[i + 2] = (Math.random() - 0.5) * 20

    // 随机向上的微小速度
    velocities[i] = (Math.random() - 0.5) * 0.002
    velocities[i + 1] = (Math.random() - 0.05) * 0.001 + 0.0005 // 略微向上
    velocities[i + 2] = (Math.random() - 0.5) * 0.002
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

  const material = new THREE.PointsMaterial({
    color: 0x0ea5e9,
    size: 0.05,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending
  })

  particles = new THREE.Points(geometry, material)
  scene.add(particles)

  // 存储速度的引用以便后续更新
  (particles as any).velocities = velocities
  (particles as any).positions = positions
}

const animate = () => {
  animationId = requestAnimationFrame(animate)

  if (!particles || !scene || !camera || !motionStore.shouldAnimate) return

  // 更新粒子位置（带速度）
  const positions = particles.geometry.attributes.position.array
  const velocities = (particles as any).velocities

  const speedFactor = motionStore.animationSpeedFactor

  for (let i = 0; i < positions.length; i += 3) {
    positions[i] += velocities[i] * speedFactor
    positions[i + 1] += velocities[i + 1] * speedFactor
    positions[i + 2] += velocities[i + 2] * speedFactor

    // 边界检查：回到顶部重置
    if (positions[i + 1] > 7) {
      positions[i + 1] = -7
      positions[i] = (Math.random() - 0.5) * 20
      positions[i + 2] = (Math.random() - 0.5) * 20
    }

    // 轻微的水平飘动
    positions[i] += Math.sin(Date.now() * 0.001 + i) * 0.0005
  }

  particles.geometry.attributes.position.needsUpdate = true

  // 缓慢旋转整个粒子场
  particles.rotation.y += 0.0001 * speedFactor
  particles.rotation.x += 0.00005 * speedFactor

  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

// 监听沉浸级别变化，重新创建粒子
watch(() => motionStore.immersionLevel, () => {
  createParticles()
})

// 响应式调整大小
const handleResize = () => {
  if (!container.value || !camera || !renderer) return
  const width = container.value.clientWidth
  const height = container.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

window.addEventListener('resize', handleResize)

onMounted(async () => {
  // 动态加载 three.js（仅在客户端）
  if (typeof window !== 'undefined' && !THREE) {
    THREE = await import('three')
  }
  initThreeJS()
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) {
    renderer.dispose()
    renderer = null
  }
  if (particles) {
    particles.geometry.dispose()
    particles.material.dispose()
    particles = null
  }
  scene = null
  camera = null
  window.removeEventListener('resize', handleResize)
}
</script>

<template>
  <div ref="container" class="three-scene-container" />
</template>

<style scoped>
.three-scene-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  opacity: 0.6;
}

@media (prefers-reduced-motion: reduce) {
  .three-scene-container {
    display: none;
  }
}
</style>
