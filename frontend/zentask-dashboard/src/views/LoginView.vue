<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  LoginEyeOffIcon,
  LoginEyeOnIcon,
  LoginLogoMark,
  LoginLogoText,
  LoginHeroImage,
  LoginHeroShape,
  LoginGlowShape,
  LoginCardShape,
  Zentask,
  SmartStudyAssistant,
} from '@/icons'

const router = useRouter()
const showPassword = ref(false)
const rememberMe = ref(false)
const identifier = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const isValidEmail = computed(() => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(identifier.value.trim())
})

const isValidUsername = computed(() => {
  return identifier.value.trim().length >= 3
})

const isIdentifierValid = computed(() => {
  const value = identifier.value.trim()
  if (!value) return false
  return value.includes('@') ? isValidEmail.value : isValidUsername.value
})

const isLoginDisabled = computed(() => {
  return !isIdentifierValid.value || !password.value.trim() || isLoading.value
})

const goToRegister = () => {
  router.push('/register')
}

const goToForgotPassword = () => {
  router.push('/forgot-password')
}

const handleLogin = async () => {
  errorMessage.value = ''

  if (isLoginDisabled.value) return

  isLoading.value = true

  try {
    const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: identifier.value.trim(),
        password: password.value,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      errorMessage.value =
        data.detail ||
        data.username?.[0] ||
        data.password?.[0] ||
        'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.'
      return
    }

    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_identifier', identifier.value.trim())

    router.push('/dashboard')
  } catch (error) {
    errorMessage.value = 'Không thể kết nối tới server.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-white font-inter text-[#171717]">
    <div class="mx-auto flex min-h-screen items-center justify-center">
      <div class="flex min-h-screen w-full bg-white">
        <!-- Left -->
        <div class="flex flex-1 items-center justify-center px-8">
          <div class="w-full max-w-[450px]">
            <!-- Logo -->
            <div class="mb-8">
              <div class="mb-8 flex items-center gap-3">
                <img :src="LoginLogoMark" alt="Logo mark" class="h-12 w-auto" />
              </div>

              <div class="h-px w-full bg-[#e5e5e5]" />
            </div>

            <!-- Form -->
            <div class="flex flex-col gap-6">
              <div>
                <h1 class="text-2xl font-semibold leading-8">Login</h1>
              </div>

              <div class="flex flex-col gap-3 text-[#404040]">
                <!-- Username -->
                <div class="flex flex-col gap-1">
                  <label class="text-base font-medium leading-6">
                    Username
                  </label>

                  <div class="pt-1">
                    <input
                      v-model="identifier"
                      type="text"
                      placeholder="Enter username"
                      class="h-10 w-full rounded-md border border-[#d4d4d4] bg-white px-3 text-sm outline-none transition focus:border-[#5c01d5]"
                    />
                  </div>
                </div>

                <!-- Password -->
                <div class="flex flex-col gap-1">
                  <label class="text-base font-medium leading-6">
                    Password
                  </label>

                  <div class="pt-1">
                    <div class="flex h-10 items-center rounded-md border border-[#d4d4d4] bg-white px-3">
                      <input
                        v-model="password"
                        :type="showPassword ? 'text' : 'password'"
                        placeholder="Enter password"
                        class="flex-1 bg-transparent text-sm outline-none"
                        @keyup.enter="handleLogin"
                      />

                      <button
                        type="button"
                        class="ml-2"
                        @click="showPassword = !showPassword"
                      >
                        <img
                          :src="showPassword ? LoginEyeOnIcon : LoginEyeOffIcon"
                          alt="Toggle password"
                          class="h-6 w-6 cursor-pointer"
                        />
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Error -->
                <div v-if="errorMessage" class="text-sm text-red-500">
                  {{ errorMessage }}
                </div>
              </div>

              <!-- Remember / forgot -->
              <div class="flex items-center gap-3">
                <label class="flex flex-1 items-center gap-2">
                  <input
                    v-model="rememberMe"
                    type="checkbox"
                    class="h-[18px] w-[18px] rounded border border-[#d4d4d4] cursor-pointer"
                  />
                  <span class="text-base leading-6 text-[#404040]">
                    Stay logged in 
                  </span>
                </label>

                <button
                  type="button"
                  @click="goToForgotPassword"
                  class="text-right text-base leading-6 text-[#404040] cursor-pointer hover:underline"
                >
                  I forgot my password
                </button>
              </div>

              <!-- Login button -->
              <button
                type="button"
                :disabled="isLoginDisabled"
                @click="handleLogin"
                class="flex items-center justify-center rounded-md p-3 text-center text-white transition"
                :class="
                  isLoginDisabled
                    ? 'cursor-not-allowed bg-[#5c01d5]/20'
                    : 'cursor-pointer bg-[#5c01d5] hover:opacity-90'
                "
              >
                <span class="text-base font-medium leading-6">
                  {{ isLoading ? 'Logging in...' : 'Login' }}
                </span>
              </button>
              <div class="pt-2 text-center">
                <button
                  type="button"
                  @click="goToRegister"
                  class="text-base font-medium leading-6 text-[#5c01d5] transition hover:underline hover:opacity-70 cursor-pointer"
                >
                  Register
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
</div>
</template>