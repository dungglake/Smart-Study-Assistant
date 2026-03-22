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

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const errorMessage = ref('')

const isLoginDisabled = computed(() => {
  return !username.value.trim() || !password.value.trim()
})

const handleLogin = () => {
  if (isLoginDisabled.value) return

  errorMessage.value = ''

  // demo login local
  // sau này bạn thay bằng API thật
  if (username.value === 'admin' && password.value === '123456') {
    localStorage.setItem('isLoggedIn', 'true')
    localStorage.setItem('username', username.value)
    router.push('/dashboard')
    return
  }

  errorMessage.value = 'Thông tin đăng nhập không đúng.'
}
</script>

<template>
  <div class="min-h-screen bg-white font-inter text-[#171717]">
    <div class="mx-auto flex min-h-screen max-w-[1440px] items-center justify-center">
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
                      v-model="username"
                      type="text"
                      placeholder="Nhập username"
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
                        placeholder="Nhập password"
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
                    Ghi nhớ đăng nhập
                  </span>
                </label>

                <button
                  type="button"
                  class="text-right text-base leading-6 text-[#404040] cursor-pointer hover:underline"
                >
                  Quên mật khẩu?
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
                <span class="text-base font-medium leading-6">Login</span>
              </button>
              <div class="pt-2 text-center">
                <button
                  type="button"
                  class="text-base font-medium leading-6 text-[#5c01d5] transition hover:underline hover:opacity-70 cursor-pointer"
                >
                  Register
                </button>
              </div>
            </div>
          </div>
        </div>

      <!-- RIGHT PANEL -->
      <div class="relative hidden flex-1 overflow-hidden lg:block">
        <div class="absolute inset-0 bg-[#E2E6FF]"></div>
        <div class="absolute inset-0 bg-[linear-gradient(10deg,rgba(207,214,255,0)_8%,rgba(212,183,248,0.35)_72%,rgba(93,5,214,0.45)_92%)]"></div>
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_92%_12%,rgba(93,5,214,0.55)_0%,rgba(93,5,214,0.22)_16%,transparent_34%)]"></div>
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_20%_85%,rgba(212,183,248,0.35)_0%,rgba(207,214,255,0)_60%)]"></div>

        <img
          :src="LoginHeroShape"
          alt="Top shape"
          class="pointer-events-none absolute left-0 top-0 z-10 w-[180px] lg:w-[240px] xl:w-[420px] object-contain"
        />

        <img
          :src="LoginGlowShape"
          alt="Bottom left glow"
          class="pointer-events-none absolute bottom-0 left-0 z-10 w-[140px] lg:w-[180px] xl:w-[220px] object-contain"
        />

        <img
          :src="LoginCardShape"
          alt="Right card shape"
          class="pointer-events-none absolute bottom-[40px] right-0 z-10 w-[170px] lg:w-[210px] xl:w-[340px] object-contain"
        />

        <!-- Logo -->
        <div class="absolute z-20 left-[6%] top-[110px] lg:left-[8%] lg:top-[130px] xl:left-[18%] xl:top-[210px]">
          <div class="flex items-center gap-2 lg:gap-3 xl:gap-4">
            <img
              :src="LoginLogoText"
              alt="Zentask mark"
              class="h-[68px] lg:h-[88px] xl:h-[120px] w-auto shrink-0 object-contain brightness-0 invert"
            />

            <div class="flex flex-col justify-center">
              <img
                :src="Zentask"
                alt="Zentask"
                class="block h-[22px] lg:h-[28px] xl:h-[36px] w-auto"
              />
              <img
                :src="SmartStudyAssistant"
                alt="Smart Study Assistant"
                class="mt-2 block h-[14px] lg:h-[17px] xl:h-[22px] w-auto"
              />
            </div>
          </div>
        </div>

        <!-- Character -->
        <div class="absolute bottom-0 right-0 z-20">
          <img
            :src="LoginHeroImage"
            alt="Login hero image"
            class="max-h-[68vh] lg:max-h-[75vh] xl:max-h-[85vh] w-auto object-contain translate-x-[-40px] lg:translate-x-[-20px]"
          />
        </div>
      </div>
    </div>
  </div>
</div>
</template>