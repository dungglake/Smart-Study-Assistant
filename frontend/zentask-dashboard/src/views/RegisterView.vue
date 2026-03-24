<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { LoginCardShape, LoginGlowShape, LoginHeroImage, LoginHeroShape, LoginLogoText, Logo, SmartStudyAssistant, Zentask, LoginEyeOnIcon, LoginEyeOffIcon, } from '@/icons'

const router = useRouter()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const stayLoggedIn = ref(false)

const errorMessage = ref('')
const successMessage = ref('')
const isLoading = ref(false)

const showPassword = ref(false)
const showConfirmPassword = ref(false)

const isValidEmail = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim())
})

const doPasswordsMatch = computed(() => {
  return password.value === confirmPassword.value
})

const isRegisterDisabled = computed(() => {
  return (
    !isValidEmail.value ||
    !password.value ||
    !confirmPassword.value ||
    !doPasswordsMatch.value ||
    isLoading.value
  )
})

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const toggleConfirmPassword = () => {
  showConfirmPassword.value = !showConfirmPassword.value
}

const handleRegister = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (isRegisterDisabled.value) return

  isLoading.value = true

  try {
    const response = await fetch('http://127.0.0.1:8000/api/auth/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value.trim().toLowerCase(),
        password: password.value,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      if (data.email?.[0]) {
        errorMessage.value = data.email[0]
      } else if (data.password?.[0]) {
        errorMessage.value = data.password[0]
      } else if (data.detail) {
        errorMessage.value = data.detail
      } else {
        errorMessage.value = 'Registration failed. Please double-check your information.'
      }
      return
    }

    successMessage.value = data.detail || 'Registration successful. Please log in.'

    if (stayLoggedIn.value) {
      localStorage.setItem('register_email', email.value.trim().toLowerCase())
    }

    setTimeout(() => {
      router.push('/login')
    }, 1200)
  } catch (error) {
    errorMessage.value = 'Cannot connect to server.'
  } finally {
    isLoading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}

const goToForgotPassword = () => {
  router.push('/forgot-password')
}
</script>

<template>
 <div class="w-full min-h-screen relative bg-white overflow-hidden flex items-start justify-start text-left text-num-16 text-gray font-inter">
    <div class="w-full min-h-screen bg-white flex items-stretch max-w-full">
      <div class="min-h-screen flex-[0.94] overflow-hidden flex flex-col items-center justify-center py-num-0 px-8 gap-8">
        <div class="flex w-[450px] flex-col items-start gap-8">
          <div class="flex h-12 w-[244px] flex-col items-start overflow-hidden">
            <div class="flex h-12 w-full flex-col items-center justify-center overflow-hidden">
              <div class="relative h-12 w-full">
                <img :src="Logo" alt="Zentask" class="h-12 w-auto" />
              </div>
            </div>
          </div>

          <div class="h-px w-full bg-[#e5e5e5]" />
        </div>

        <div class="flex w-[450px] flex-col items-center justify-center gap-6 overflow-hidden rounded">
          <div class="flex w-full flex-col items-start text-[24px]">
            <div class="flex w-full items-start">
              <div class="flex-1 text-[24px] font-semibold leading-8">Create an account</div>
            </div>
          </div>

          <div class="flex w-full flex-col items-start gap-3 text-[#404040]">
            <div class="flex w-full flex-col items-start gap-1">
              <div class="flex w-full flex-col items-start">
                <div class="flex w-full items-center justify-between">
                  <div class="flex items-center">
                    <div class="font-medium leading-6">Email</div>
                  </div>
                </div>
              </div>

              <div class="flex w-full flex-col items-start pt-1">
                <input
                  v-model="email"
                  type="email"
                  placeholder="Enter your email"
                  class="h-10 w-full rounded-md border border-[#d4d4d4] bg-white px-3 py-2 outline-none focus:border-[#5c01d5]"
                />
              </div>
            </div>

            <div class="flex w-full flex-col items-start gap-1">
              <div class="flex w-full flex-col items-start">
                <div class="flex w-full items-center justify-between">
                  <div class="flex items-center">
                    <div class="font-medium leading-6">Password</div>
                  </div>
                </div>
              </div>

              <div class="flex w-full flex-col items-start pt-1">
                <div class="flex h-10 w-full items-center rounded-md border border-[#d4d4d4] bg-white px-3">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="Enter your password"
                    class="flex-1 bg-transparent outline-none"
                  />
                  <button
                    type="button"
                    class="text-sm text-[#737373]"
                    @click="togglePassword"
                  >
                    <img
                      :src="showPassword ? LoginEyeOnIcon : LoginEyeOffIcon"
                      alt="toggle password"
                      class="h-5 w-5 opacity-70 hover:opacity-100"
                    />
                  </button>
                </div>
              </div>
            </div>

            <div class="flex w-full flex-col items-start gap-1">
              <div class="flex w-full flex-col items-start">
                <div class="flex w-full items-center justify-between">
                  <div class="flex items-center">
                    <div class="font-medium leading-6">Repeat Password</div>
                  </div>
                </div>
              </div>

              <div class="flex w-full flex-col items-start pt-1">
                <div class="flex h-10 w-full items-center rounded-md border border-[#d4d4d4] bg-white px-3">
                  <input
                    v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    placeholder="Repeat your password"
                    class="flex-1 bg-transparent outline-none"
                  />
                  <button
                    type="button"
                    class="text-sm text-[#737373]"
                    @click="toggleConfirmPassword"
                  >
                    <img
                      :src="showConfirmPassword ? LoginEyeOnIcon : LoginEyeOffIcon"
                      alt="toggle password"
                      class="h-5 w-5 opacity-70 hover:opacity-100"
                    />
                  </button>
                </div>
              </div>
            </div>

            <p
              v-if="confirmPassword && !doPasswordsMatch"
              class="text-sm leading-5 text-red-500"
            >
              The password entered again does not match.
            </p>

            <p v-if="errorMessage" class="text-sm leading-5 text-red-500">
              {{ errorMessage }}
            </p>

            <p v-if="successMessage" class="text-sm leading-5 text-green-600">
              {{ successMessage }}
            </p>
          </div>

          <div class="flex w-full items-start gap-3">
            <div class="flex flex-1 flex-col items-start justify-center">
              <label class="flex w-full items-center gap-2">
                <span class="flex items-start">
                  <span class="relative h-6 w-[18px] overflow-hidden">
                    <input
                      v-model="stayLoggedIn"
                      type="checkbox"
                      class="absolute left-0 top-[3px] h-[18px] w-[18px] rounded border border-[#d4d4d4] cursor-pointer"
                    />
                  </span>
                </span>

                <span class="flex-1 leading-6">Stay logged in</span>
              </label>
            </div>

            <button
              type="button"
              @click="goToForgotPassword"
              class="flex-1 text-right leading-6 text-[#404040] hover:underline cursor-pointer"
            >
              I forgot my password
            </button>
          </div>

          <div class="flex w-full flex-col items-start gap-3 text-center text-white">
            <button
              type="button"
              :disabled="isRegisterDisabled"
              @click="handleRegister"
              class="flex w-full items-center justify-center rounded-md p-3 transition"
              :class="
                isRegisterDisabled
                  ? 'cursor-not-allowed bg-[#5c01d5]/20'
                  : 'cursor-pointer bg-[#5c01d5] hover:opacity-90'
              "
            >
              <span class="text-base font-medium leading-6">
                {{ isLoading ? 'Registering...' : 'Register' }}
              </span>
            </button>

            <button
              type="button"
              @click="goToLogin"
              class="flex w-full items-center justify-center rounded-md p-3 text-[#5c01d5] hover:underline transition cursor-pointer"
            >
              <span class="text-base font-medium leading-6">Login</span>
            </button>
          </div>
        </div>
      </div>

      <!-- RIGHT PANEL -->
      <div class="relative hidden lg:block flex-1 self-stretch min-h-screen overflow-hidden">
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
        <div class="relative z-20 grid h-full min-h-screen grid-cols-12">
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