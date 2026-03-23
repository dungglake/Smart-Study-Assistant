<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Logo, LoginHeroImage, LoginHeroShape, LoginGlowShape, LoginCardShape, LoginLogoText, Zentask, SmartStudyAssistant } from '@/icons'

const route = useRoute()
const router = useRouter()

const email = ref(String(route.query.email || ''))
const errorMessage = ref('')
const successMessage = ref('')
const isLoading = ref(false)

const API_BASE_URL = 'http://127.0.0.1:8000/api/auth'
const REQUEST_RESET_ENDPOINT = `${API_BASE_URL}/password-reset/`

const isValidEmail = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim())
})

const isResendDisabled = computed(() => {
  return !email.value.trim() || !isValidEmail.value || isLoading.value
})

const handleResendLink = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (isResendDisabled.value) return

  try {
    isLoading.value = true

    const response = await fetch(REQUEST_RESET_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value.trim(),
      }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      errorMessage.value =
        data?.detail ||
        data?.email?.[0] ||
        'Unable to resend the link. Please try again.'
      return
    }

    successMessage.value = 'A new password reset link has been sent.'
  } catch (error) {
    errorMessage.value = 'Unable to connect to the server. Please try again.'
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-white font-inter text-[#171717]">
    <div class="flex min-h-screen">
      <div class="flex flex-1 items-center justify-center px-8">
        <div class="w-full max-w-[450px]">
          <div class="mb-8">
            <div class="flex h-12 items-center">
              <img :src="Logo" alt="Logo" class="h-12 w-auto" />
            </div>
            <div class="mt-8 h-px w-full bg-[#e5e5e5]" />
          </div>

          <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-3">
              <h1 class="text-left text-2xl font-semibold leading-8">
                Do you need us to resend the link?
              </h1>

              <p class="text-left text-base leading-6 text-[#404040]">
                Please allow 30 seconds for the email to arrive before requesting another link.
              </p>
            </div>

            <div class="flex flex-col gap-3">
              <p v-if="errorMessage" class="text-left text-sm text-red-500">
                {{ errorMessage }}
              </p>

              <p v-if="successMessage" class="text-left text-sm text-green-600">
                {{ successMessage }}
              </p>
            </div>

            <div class="flex flex-col gap-3 text-center">
              <button
                type="button"
                :disabled="isResendDisabled"
                @click="handleResendLink"
                class="flex items-center justify-center rounded-md p-3 text-white transition"
                :class="
                  isResendDisabled
                    ? 'cursor-not-allowed bg-[#5c01d5]/20'
                    : 'cursor-pointer bg-[#5c01d5] hover:opacity-90'
                "
              >
                <span class="text-base font-medium leading-6">
                  {{ isLoading ? 'Resending...' : 'Resend link' }}
                </span>
              </button>

              <button
                type="button"
                @click="goToLogin"
                class="rounded-md p-3 text-[#5c01d5] cursor-pointer transition hover:underline"
              >
                <span class="text-base font-medium leading-6">Login</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT PANEL -->
      <div class="relative hidden lg:block flex-1 overflow-hidden">
        <div class="absolute inset-0 bg-[#E2E9FF]"></div>
        <div class="absolute inset-0 bg-[linear-gradient(18deg,rgba(226,233,255,0)_5%,rgba(212,183,248,0.28)_65%,rgba(93,5,214,0.42)_100%)]"></div>
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_88%_14%,rgba(93,5,214,0.45)_0%,rgba(93,5,214,0.16)_18%,transparent_36%)]"></div>
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_14%_88%,rgba(212,183,248,0.30)_0%,rgba(207,214,255,0)_55%)]"></div>

        <img
          :src="LoginHeroShape"
          alt="Top shape"
          class="pointer-events-none absolute left-0 top-0 z-10 w-[180px] min-[1440px]:w-[250px] 2xl:w-[320px] object-contain"
        />

        <img
          :src="LoginGlowShape"
          alt="Bottom left glow"
          class="pointer-events-none absolute bottom-0 left-0 z-10 w-[120px] min-[1440px]:w-[160px] 2xl:w-[220px] object-contain"
        />

        <img
          :src="LoginCardShape"
          alt="Right card shape"
          class="pointer-events-none absolute bottom-[4%] right-0 z-10 w-[100px] min-[1440px]:w-[160px] 2xl:w-[240px] object-contain"
        />

        <div class="relative z-20 grid h-full grid-cols-12">
          <div class="col-span-5 flex items-center justify-center translate-x-[66%] translate-y-[-18%] scale-135">
            <div class="max-w-full">
              <div class="flex items-center gap-3 min-[1440px]:gap-4">
                <img
                  :src="LoginLogoText"
                  alt="Zentask mark"
                  class="h-[60px] min-[1440px]:h-[78px] 2xl:h-[104px] w-auto shrink-0 object-contain brightness-0 invert"
                />

                <div class="flex flex-col justify-center">
                  <img
                    :src="Zentask"
                    alt="Zentask"
                    class="block h-[22px] min-[1440px]:h-[28px] 2xl:h-[36px] w-auto"
                  />
                  <img
                    :src="SmartStudyAssistant"
                    alt="Smart Study Assistant"
                    class="mt-2 block h-[14px] min-[1440px]:h-[18px] 2xl:h-[22px] w-auto"
                  />
                </div>
              </div>
            </div>
          </div>

          <div class="col-span-7 flex items-end justify-end pr-[2%] min-[1440px]:pr-[3%] 2xl:pr-[4%]">
            <img
              :src="LoginHeroImage"
              alt="Login hero image"
              class="relative z-20 h-auto w-auto max-h-[70vh] min-[1440px]:max-h-[76vh] 2xl:max-h-[82vh] max-w-[95%] object-contain"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>