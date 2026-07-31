<!-- src/components/ThreeScene.vue -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import type { Scene, PerspectiveCamera, WebGLRenderer, Points, BufferGeometry } from 'three'
import { useMotionStore } from '@/stores/motion'

const container = ref<HTMLDivElement | null>(null)
let scene: any = null
let camera: any = null
let renderer: any = null
let particles: any = null
let animationId: number | null = null
let THREE: any = null
const motionStore = useMotionStore()

const initThreeJS = async () => {
  if (!container.value || !motionStore.shouldAnimate) return

  if (!THREE) {
    THREE = await import('three')
  }

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0f172a)

  const aspect = container.value.clientWidth / container.value.clientHeight
  camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000)
  camera.position.z = 15

  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, preserveDrawingBuffer: false })
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
  container.value.appendChild(renderer.domElement)

  createParticles()
  animate()
}

const createParticles = () => {
  if (!scene || !motionStore.shouldAnimate) return

  const count = motionStore.particleCount
  if (count === 0) {
    if (particles) {
      scene.remove(particles)
      particles.geometry.dispose()
      particles.material.dispose()
      particles = null
    }
    return
  }

  if (particles) {
    scene.remove(particles)
    particles.geometry.dispose()
    particles.material.dispose()
  }

  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(count * 3)
  const velocities = new Float32Array(count * 3)

  for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 20
    positions[i + 1] = (Math.random() - 0.5) * 15
    positions[i + 2] = (Math.random() - 0.5) * 20
    velocities[i] = (Math.random() - 0.5) * 0.002
    velocities[i + 1] = (Math.random() * 0.001 + 0.0005)
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
  ;(particles as any)._velocities = velocities
  ;(particles as any)._positions = positions
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  if (!particles || !scene || !camera || !motionStore.shouldAnimate) return

  const positions = (particles as any)._positions
  const velocities = (particles as any)._velocities
  const speedFactor = motionStore.animationSpeedFactor

  for (let i = 0; i < positions.length; i += 3) {
    positions[i] += velocities[i] * speedFactor
    positions[i + 1] += velocities[i + 1] * speedFactor
    positions[i + 2] += velocities[i + 2] * speedFactor
    if (positions[i + 1] > 7) {
      positions[i + 1] = -7
      positions[i] = (Math.random() - 0.5) * 20
      positions[i + 2] = (Math.random() - 0.5) * 20
    }
    positions[i] += Math.sin(Date.now() * 0.001 + i) * 0.0005
  }

  particles.geometry.attributes.position.needsUpdate = true
  particles.rotation.y += 0.0001 * speedFactor
  particles.rotation.x += 0.00005 * speedFactor

  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

const handleResize = () => {
  if (!container.value || !camera || !renderer) return
  const width = container.value.clientWidth
  const height = container.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

watch(() => motionStore.immersionLevel, () => {
  createParticles()
})

onMounted(() => {
  initThreeJS()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) { renderer.dispose(); renderer = null }
  if (particles) { particles.geometry.dispose(); particles.material.dispose(); particles = null }
  scene = null
  camera = null
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div ref="container" class="three-scene-container" />
</template>

<style scoped>
.three-scene-container {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 0;
  pointer-events: none;
}

@media (prefers-reduced-motion: reduce) {
  .three-scene-container { display: none; }
}
</style>
