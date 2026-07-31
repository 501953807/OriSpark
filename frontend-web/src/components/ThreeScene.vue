<!-- src/components/ThreeScene.vue -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'
import { useMotionStore } from '@/stores/motion'

const container = ref<HTMLDivElement | null>(null)
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let particles: THREE.Points | null = null
let animationId: number | null = null
const motionStore = useMotionStore()

// Initialize Three.js scene
const initThreeJS = () => {
  if (!container.value || !motionStore.shouldAnimate) return

  // Create scene
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0f172a)

  // Create camera
  const aspect = container.value.clientWidth / container.value.clientHeight
  camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000)
  camera.position.z = 15

  // Create renderer (alpha transparent, disable antialias for performance)
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, preserveDrawingBuffer: false })
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1)) // Cap pixel ratio for performance
  container.value.appendChild(renderer.domElement)

  // Create particle system
  createParticles()

  // Start animation loop
  animate()
}

// Create/update particle system
const createParticles = () => {
  if (!scene || !camera || !motionStore.shouldAnimate) return

  const count = motionStore.particleCount
  if (count === 0) {
    // Remove existing particles
    if (particles) {
      scene.remove(particles)
      if (particles.geometry) particles.geometry.dispose()
      if (particles.material) particles.material.dispose()
      particles = null
    }
    return
  }

  // Dispose previous particles
  if (particles) {
    scene.remove(particles)
    if (particles.geometry) particles.geometry.dispose()
    if (particles.material) particles.material.dispose()
  }

  // Create new particle system
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(count * 3)
  const velocities = new Float32Array(count * 3) // Velocity for animation

  for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 20
    positions[i + 1] = (Math.random() - 0.5) * 15
    positions[i + 2] = (Math.random() - 0.5) * 20

    // Random upward velocity with some spread
    velocities[i] = (Math.random() - 0.5) * 0.002
    velocities[i + 1] = (Math.random() * 0.001 + 0.0005) // Slight upward drift
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

  // Store velocities and positions for animation update
  (particles as any).velocities = velocities
  (particles as any).positions = positions
}

// Animation loop
const animate = () => {
  animationId = requestAnimationFrame(animate)

  if (!particles || !scene || !camera || !motionStore.shouldAnimate) return

  // Update particle positions with velocity
  const positions = (particles as any).positions
  const velocities = (particles as any).velocities
  const speedFactor = motionStore.animationSpeedFactor

  for (let i = 0; i < positions.length; i += 3) {
    positions[i] += velocities[i] * speedFactor
    positions[i + 1] += velocities[i + 1] * speedFactor
    positions[i + 2] += velocities[i + 2] * speedFactor

    // Reset when particle reaches top
    if (positions[i + 1] > 7) {
      positions[i + 1] = -7
      positions[i] = (Math.random() - 0.5) * 20
      positions[i + 2] = (Math.random() - 0.5) * 20
    }

    // Add slight horizontal wave effect
    positions[i] += Math.sin(Date.now() * 0.001 + i) * 0.0005
  }

  particles.geometry.attributes.position.needsUpdate = true

  // Slowly rotate entire field
  particles.rotation.y += 0.0001 * speedFactor
  particles.rotation.x += 0.00005 * speedFactor

  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

// Handle resize
const handleResize = () => {
  if (!container.value || !camera || !renderer) return
  const width = container.value.clientWidth
  const height = container.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// Watch immersion level changes - recreate particles when needed
watch(() => motionStore.immersionLevel, () => {
  createParticles()
})

onMounted(() => {
  initThreeJS()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) {
    renderer.dispose()
    renderer = null
  }
  if (particles) {
    particles.geometry?.dispose()
    particles.material?.dispose()
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
