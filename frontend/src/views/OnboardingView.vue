<template>
  <div class="onboarding-page">
    <OnboardingWizard
      :initial-creator-type="initialCreatorType"
      :auto-start="!alreadyOnboarded"
      @finish="onFinish"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import OnboardingWizard from '@/components/onboarding/OnboardingWizard.vue'
import { systemApi } from '@/api/system'

const router = useRouter()
const alreadyOnboarded = ref(false)
const initialCreatorType = ref('')

onMounted(async () => {
  try {
    const res = await systemApi.onboardingStatus()
    if (res.data.data?.onboarding_completed) {
      alreadyOnboarded.value = true
      router.push('/app')
      return
    }
    const saved = localStorage.getItem('oristudio-creator-type')
    if (saved) {
      initialCreatorType.value = saved
    }
  } catch {
    // Silently continue
  }
})

async function onFinish(payload: { creatorType: string; importCount: number }) {
  try {
    await systemApi.completeOnboarding({ creator_type: payload.creatorType })
  } catch {
    // Silently fail — localStorage already has the data
  }
  localStorage.setItem('oristudio-onboarded', 'true')
  router.push('/app')
}
</script>

<style scoped>
.onboarding-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg); padding: 40px 20px;
}
</style>
