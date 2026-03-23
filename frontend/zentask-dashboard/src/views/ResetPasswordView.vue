<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Logo, LoginEyeOffIcon, LoginEyeOnIcon, LoginHeroShape, LoginGlowShape, LoginCardShape, LoginLogoText, Zentask, SmartStudyAssistant, LoginHeroImage,  } from '@/icons'

const route = useRoute()
const router = useRouter()

const uid = String(route.query.uid || '')
const token = String(route.query.token || '')

const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const errorMessage = ref('')
const successMessage = ref('')
const isLoading = ref(false)

const API_BASE_URL = 'http://127.0.0.1:8000/api/auth'
const RESET_CONFIRM_ENDPOINT = `${API_BASE_URL}/password-reset/confirm/`
const passwordChecks = computed(() => {
  const value = password.value

  return {
    minLength: value.length >= 8,
    hasUppercase: /[A-Z]/.test(value),
    hasLowercase: /[a-z]/.test(value),
    hasNumber: /\d/.test(value),
    hasSpecial: /[^A-Za-z0-9]/.test(value),
  }
})

const strengthScore = computed(() => {
  const checks = passwordChecks.value
  return Object.values(checks).filter(Boolean).length
})

const strengthText = computed(() => {
  if (!password.value) return ''
  if (strengthScore.value <= 2) return 'Weak'
  if (strengthScore.value <= 4) return 'Medium'
  return 'Strong'
})

const strengthClass = computed(() => {
  if (!password.value) return 'bg-[#e5e5e5]'
  if (strengthScore.value <= 2) return 'bg-red-500'
  if (strengthScore.value <= 4) return 'bg-yellow-500'
  return 'bg-green-600'
})

const passwordsMatch = computed(() => {
  return !!confirmPassword.value && password.value === confirmPassword.value
})

const isValid = computed(() => {
  return (
    !!password.value &&
    !!confirmPassword.value &&
    password.value === confirmPassword.value &&
    strengthScore.value >= 3
  )
})

const isDisabled = computed(() => {
  return !isValid.value || isLoading.value
})

const handleResetPassword = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (!uid || !token) {
    errorMessage.value = 'Invalid or expired reset link.'
    return
  }

  if (!password.value || !confirmPassword.value) {
    errorMessage.value = 'Please fill in all fields.'
    return
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  if (!isValid.value) {
    errorMessage.value =
      'Password must be at least 8 characters and include uppercase, lowercase, number, and special character.'
    return
  }

  try {
    isLoading.value = true

    const response = await fetch(RESET_CONFIRM_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uid,
        token,
        new_password: password.value,
        confirm_password: confirmPassword.value,
      }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      errorMessage.value =
        data?.detail ||
        data?.new_password?.[0] ||
        data?.confirm_password?.[0] || 
        'Invalid or expired link.'
      return
    }

    successMessage.value = 'Password updated successfully.'

    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (err) {
    errorMessage.value = 'Unable to connect to the server.'
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

          <div class="flex flex-col gap-6">
            <h1 class="text-2xl font-semibold leading-8">
              Update password
            </h1>

            <div class="flex flex-col gap-1">
              <label class="text-base font-medium text-[#404040]">
                New password
              </label>

              <div class="relative">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Enter new password"
                  class="h-10 w-full rounded-md border border-[#d4d4d4] px-3 pr-10 outline-none transition focus:border-[#5c01d5]"
                />

                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2"
                  @click="showPassword = !showPassword"
                >
                  <img
                    :src="showPassword ? LoginEyeOnIcon : LoginEyeOffIcon"
                    alt="Toggle password visibility"
                    class="h-5 w-5"
                  />
                </button>
              </div>

              <div v-if="password" class="mt-2 flex flex-col gap-2">
                <div class="h-2 w-full overflow-hidden rounded-full bg-[#e5e5e5]">
                  <div
                    class="h-full transition-all duration-300"
                    :class="strengthClass"
                    :style="{ width: `${(strengthScore / 5) * 100}%` }"
                  />
                </div>

                <p class="text-sm text-[#404040]">
                  Password strength:
                  <span class="font-medium">{{ strengthText }}</span>
                </p>
              </div>
            </div>

            <div class="flex flex-col gap-1">
              <label class="text-base font-medium text-[#404040]">
                Confirm password
              </label>

              <div class="relative">
                <input
                  v-model="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="Confirm password"
                  class="h-10 w-full rounded-md border border-[#d4d4d4] px-3 pr-10 outline-none transition focus:border-[#5c01d5]"
                />
              </div>

              <p
                v-if="confirmPassword"
                class="mt-1 text-sm"
                :class="passwordsMatch ? 'text-green-600' : 'text-red-500'"
              >
                {{ passwordsMatch ? 'Passwords match.' : 'Passwords do not match.' }}
              </p>
            </div>

            <p v-if="errorMessage" class="text-sm text-red-500">
              {{ errorMessage }}
            </p>

            <p v-if="successMessage" class="text-sm text-green-600">
              {{ successMessage }}
            </p>

            <div class="flex flex-col gap-3 text-center">
              <button
                type="button"
                :disabled="isDisabled"
                @click="handleResetPassword"
                class="flex items-center justify-center rounded-md p-3 text-white transition"
                :class="
                  isDisabled
                    ? 'cursor-not-allowed bg-[#5c01d5]/20'
                    : 'cursor-pointer bg-[#5c01d5] hover:opacity-90'
                "
              >
                <span>
                  {{ isLoading ? 'Updating...' : 'Set new password' }}
                </span>
              </button>

              <button
                type="button"
                @click="goToLogin"
                class="rounded-md p-3 text-[#5c01d5] cursor-pointer transition hover:underline"
              >
                Login
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT PANEL -->
      <div class="relative hidden lg:block flex-1 overflow-hidden">
        <!-- Background -->
        <div class="absolute inset-0 bg-[#E2E9FF]"></div>
        <div class="absolute inset-0 bg-[linear-gradient(18deg,rgba(226,233,255,0)_5%,rgba(212,183,248,0.28)_65%,rgba(93,5,214,0.42)_100%)]"></div>
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_88%_14%,rgba(93,5,214,0.45)_0%,rgba(93,5,214,0.16)_18%,transparent_36%)]"></div>
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_14%_88%,rgba(212,183,248,0.30)_0%,rgba(207,214,255,0)_55%)]"></div>

        <!-- Decorative shapes -->
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

        <!-- Main content -->
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

          <!-- Right content / hero -->
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