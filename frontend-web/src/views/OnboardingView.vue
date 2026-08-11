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
import { useGlobalState } from '@/stores/useGlobalState'

const router = useRouter()
const alreadyOnboarded = ref(false)
const initialCreatorType = ref('')

onMounted(async () => {
  try {
    const globalState = useGlobalState()
    const res = await systemApi.onboardingStatus()
    if (res.data.data?.onboarding_completed) {
      globalState.markOnboarded()
      alreadyOnboarded.value = true
      router.push('/app')
      return
    }
    if (globalState.creatorType) {
      initialCreatorType.value = globalState.creatorType
    }
  } catch {
    // Silently continue
  }
})

async function onFinish(payload: { creatorType: string; participantRole: string; importCount: number }) {
  try {
    await systemApi.completeOnboarding({
      creator_type: payload.creatorType,
      participant_role: payload.participantRole,
    })
  } catch {
    // Silently fail
  }
  const globalState = useGlobalState()
  globalState.setCreatorType(payload.creatorType)
  globalState.setParticipantRole(payload.participantRole)
  globalState.markOnboarded()
  router.push('/app')
}
</script>

<style scoped>
.onboarding-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg); padding: 40px 20px;
}
</style>
