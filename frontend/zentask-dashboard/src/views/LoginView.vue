<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  LoginEyeOffIcon,
  LoginLogoMark,
  LoginLogoText,
  LoginHeroImage,
  LoginHeroShape,
  LoginGlowShape,
  LoginCardShape,
  Vector,
  Vector1,
  Vector2,
  Vector3,
  Vector4,
  Vector5,
  Vector6,
  Vector7,
  Vector8,
  Vector9,
  Vector10,
  Vector11,
  Vector12,
  Vector13,
  Vector14,
  Vector15,
  Vector16,
  Vector17,
  Vector18,
  Vector19,
  Vector20,
  Vector21,
  Vector22,
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
                <img :src="LoginLogoText" alt="Logo text" class="h-6 w-auto" />
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
                          :src="LoginEyeOffIcon"
                          alt="Toggle password"
                          class="h-6 w-6"
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
                    class="h-[18px] w-[18px] rounded border border-[#d4d4d4]"
                  />
                  <span class="text-base leading-6 text-[#404040]">
                    Ghi nhớ đăng nhập
                  </span>
                </label>

                <button
                  type="button"
                  class="text-right text-base leading-6 text-[#404040]"
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
                    : 'bg-[#5c01d5] hover:opacity-90'
                "
              >
                <span class="text-base font-medium leading-6">Login</span>
              </button>
            </div>
          </div>
        </div>

        <!-- RIGHT PANEL -->
      <div class="relative hidden flex-1 overflow-hidden bg-[#f7f8ff] lg:block">
        <!-- Decorations -->
        <img
          :src="LoginHeroShape"
          alt="Login hero shape"
          class="absolute left-0 top-0 z-10 w-[320px] object-contain xl:w-[380px]"
        />

        <img
          :src="LoginGlowShape"
          alt="Decor left middle"
          class="absolute left-0 top-[520px] z-10 w-[180px] object-contain xl:w-[220px]"
        />

        <img
          :src="LoginCardShape"
          alt="Login card shape"
          class="absolute right-0 top-[110px] z-10 w-[240px] object-contain xl:w-[300px]"
        />

        <!-- Optional extra vectors -->
        <img :src="Vector" alt="" class="pointer-events-none absolute left-16 top-16 z-0 w-10 opacity-20" />
        <img :src="Vector1" alt="" class="pointer-events-none absolute left-32 top-32 z-0 w-12 opacity-20" />
        <img :src="Vector2" alt="" class="pointer-events-none absolute left-48 top-48 z-0 w-8 opacity-20" />
        <img :src="Vector3" alt="" class="pointer-events-none absolute left-64 top-64 z-0 w-14 opacity-20" />
        <img :src="Vector4" alt="" class="pointer-events-none absolute left-80 top-80 z-0 w-10 opacity-20" />
        <img :src="Vector5" alt="" class="pointer-events-none absolute left-96 top-96 z-0 w-12 opacity-20" />
        <img :src="Vector6" alt="" class="pointer-events-none absolute left-112 top-112 z-0 w-8 opacity-20" />
        <img :src="Vector7" alt="" class="pointer-events-none absolute left-128 top-128 z-0 w-14 opacity-20" />
        <img :src="Vector8" alt="" class="w-full h-[15.2px] relative max-w-full overflow-hidden" />
        <img :src="Vector9" alt="" class="pointer-events-none absolute left-160 top-160 z-0 w-12 opacity-20" />
        <img :src="Vector10" alt="" class="pointer-events-none absolute left-176 top-176 z-0 w-8 opacity-20" />
        <img :src="Vector11" alt="" class="pointer-events-none absolute left-192 top-192 z-0 w-14 opacity-20" />
        <img :src="Vector12" alt="" class="pointer-events-none absolute left-208 top-208 z-0 w-10 opacity-20" />
        <img :src="Vector13" alt="" class="pointer-events-none absolute left-224 top-224 z-0 w-12 opacity-20" />
        <img :src="Vector14" alt="" class="pointer-events-none absolute left-240 top-240 z-0 w-8 opacity-20" />
        <img :src="Vector15" alt="" class="w-full h-[35.1px] relative max-w-full overflow-hidden" />
        <img :src="Vector16" alt="" class="w-full h-[35.1px] relative max-w-full overflow-hidden" />
        <img :src="Vector17" alt="" class="w-full h-[35.1px] relative max-w-full overflow-hidden" />
        <img :src="Vector18" alt="" class="w-full h-[35.1px] relative max-w-full overflow-hidden" />
        <img :src="Vector19" alt="" class="w-full h-9 relative max-w-full overflow-hidden" />
        <img :src="Vector20" alt="" class="w-full h-[35.1px] relative max-w-full overflow-hidden" />
        <img :src="Vector21" alt="" class="w-full h-[35.1px] relative max-w-full overflow-hidden" />
        <img :src="Vector22" alt="" class="pointer-events-none absolute left-1/3 bottom-16 z-0 w-10 opacity-20" />

        <!-- Main student image -->
        <div class="relative flex h-full items-end justify-center">
          <img
            :src="LoginHeroImage"
            alt="Login hero image"
            class="relative z-20 max-h-[92vh] w-auto object-contain"
          />
        </div>
      </div>
    </div>
  </div>
</div>
</template>