<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Edit, DropDown, LoginEyeOnIcon, LoginEyeOffIcon } from '@/icons'

const API_BASE_URL = 'http://127.0.0.1:8000/api/auth'

const fileInputRef = ref<HTMLInputElement | null>(null)
const avatarPreview = ref('')

const fullName = ref('')
const email = ref('')

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const language = ref('English')
const region = ref('Asia/Bangkok')

const isLoading = ref(false)
const isSaving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const initialState = ref({
  fullName: '',
  email: '',
  language: 'English',
  region: 'Asia/Bangkok',
})

const openFilePicker = () => {
  fileInputRef.value?.click()
}

const handleAvatarChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    avatarPreview.value = String(reader.result || '')
    localStorage.setItem('settings_avatar_preview', avatarPreview.value)
  }
  reader.readAsDataURL(file)
}

const hasProfileChanges = computed(() => {
  return (
    fullName.value !== initialState.value.fullName ||
    email.value !== initialState.value.email ||
    language.value !== initialState.value.language ||
    region.value !== initialState.value.region ||
    !!avatarPreview.value !== !!localStorage.getItem('settings_avatar_preview')
  )
})

const hasPasswordChanges = computed(() => {
  return !!currentPassword.value || !!newPassword.value || !!confirmPassword.value
})

const passwordMismatch = computed(() => {
  if (!hasPasswordChanges.value) return false
  return newPassword.value !== confirmPassword.value
})

const canSave = computed(() => {
  if (isSaving.value) return false
  if (!hasProfileChanges.value && !hasPasswordChanges.value) return false
  if (hasPasswordChanges.value) {
    return (
      !!currentPassword.value.trim() &&
      !!newPassword.value.trim() &&
      !!confirmPassword.value.trim() &&
      !passwordMismatch.value
    )
  }
  return true
})

const loadLocalSettings = () => {
  const savedAvatar = localStorage.getItem('settings_avatar_preview')
  const savedLanguage = localStorage.getItem('settings_language')
  const savedRegion = localStorage.getItem('settings_region')

  if (savedAvatar) avatarPreview.value = savedAvatar
  if (savedLanguage) language.value = savedLanguage
  if (savedRegion) region.value = savedRegion
}

const fetchProfile = async () => {
  const accessToken = localStorage.getItem('access_token')
  if (!accessToken) return

  isLoading.value = true

  try {
    const response = await fetch(`${API_BASE_URL}/me/`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })

    if (!response.ok) {
      return
    }

    const data = await response.json()

    fullName.value = data.full_name || ''
    email.value = data.email || ''

    initialState.value = {
      fullName: data.full_name || '',
      email: data.email || '',
      language: language.value,
      region: region.value,
    }
  } catch {
    // BE chưa bật thì bỏ qua, không hiện lỗi
    const savedEmail = localStorage.getItem('user_identifier')
    if (savedEmail) {
      email.value = savedEmail
      initialState.value.email = savedEmail
    }
  } finally {
    isLoading.value = false
  }
}

const saveProfile = async () => {
  const accessToken = localStorage.getItem('access_token')
  if (!accessToken) throw new Error('You are not logged in.')

  const response = await fetch(`${API_BASE_URL}/me/`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      full_name: fullName.value.trim(),
      email: email.value.trim(),
    }),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      data.detail ||
        data.email?.[0] ||
        'Failed to update user information.'
    )
  }

  initialState.value.fullName = data.user?.full_name ?? fullName.value.trim()
  initialState.value.email = data.user?.email ?? email.value.trim()

  localStorage.setItem('settings_language', language.value)
  localStorage.setItem('settings_region', region.value)
  initialState.value.language = language.value
  initialState.value.region = region.value
}

const changePassword = async () => {
  const accessToken = localStorage.getItem('access_token')
  if (!accessToken) throw new Error('You are not logged in.')

  const response = await fetch(`${API_BASE_URL}/change-password/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      current_password: currentPassword.value,
      new_password: newPassword.value,
      confirm_password: confirmPassword.value,
    }),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      data.detail ||
        data.current_password?.[0] ||
        data.confirm_password?.[0] ||
        data.new_password?.[0] ||
        'Password change failed..'
    )
  }

  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}

const handleSave = async () => {
  if (!canSave.value) return

  isSaving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    if (hasProfileChanges.value) {
      await saveProfile()
    }

    if (hasPasswordChanges.value) {
      await changePassword()
    }

    successMessage.value = 'Changes saved successfully.'
  } catch (error: any) {
    errorMessage.value = error.message || 'An error occurred.'
  } finally {
    isSaving.value = false
  }
}

onMounted(async () => {
  loadLocalSettings()

  const savedEmail = localStorage.getItem('user_identifier')
  if (savedEmail) {
    email.value = savedEmail
    initialState.value.email = savedEmail
  }

  await fetchProfile()
})
</script>

<template>
  <div class="min-h-[calc(100vh-64px)] w-full bg-[#f5f5f5] p-8">
    <div class="flex w-full flex-col gap-6">
      <section class="rounded-[24px] bg-white p-6">
        <h2 class="text-[18px] font-semibold text-[#171717]">Profile</h2>

        <div v-if="isLoading" class="mt-6 text-sm text-[#737373]">
          Loading information...
        </div>

        <template v-else>
          <div class="mt-6">
            <div class="relative h-[100px] w-[100px]">
              <img
                :src="avatarPreview || 'https://via.placeholder.com/100x100.png?text=Avatar'"
                alt="Profile"
                class="h-[100px] w-[100px] rounded-full object-cover"
              />

              <button
                type="button"
                @click="openFilePicker"
                class="absolute bottom-0 right-0 flex h-8 w-8 items-center justify-center rounded-full bg-[#5c01d5] cursor-pointer"
              >
                <img :src="Edit" alt="Edit" class="h-4 w-4" />
              </button>

              <input
                ref="fileInputRef"
                type="file"
                accept="image/*"
                class="hidden"
                @change="handleAvatarChange"
              />
            </div>
          </div>

          <div class="mt-6 flex max-w-[450px] flex-col gap-3">
            <div>
              <label class="mb-1 block text-[16px] font-medium text-[#404040]">
                Full Name
              </label>
              <input
                v-model="fullName"
                type="text"
                placeholder="Enter your full name"
                class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 text-[16px] text-[#171717] outline-none"
              />
            </div>

            <div>
              <label class="mb-1 block text-[16px] font-medium text-[#404040]">
                Email
              </label>
              <input
                v-model="email"
                type="email"
                placeholder="Enter your email"
                class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 text-[16px] text-[#171717] outline-none"
              />
            </div>

            <div>
              <label class="mb-1 block text-[16px] font-medium text-[#404040]">
                Password
              </label>

              <div class="relative">
                <input
                  v-model="currentPassword"
                  :type="showCurrentPassword ? 'text' : 'password'"
                  placeholder="Enter Current Password"
                  class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 pr-10 text-[16px] text-[#171717] outline-none"
                />

                <button
                  type="button"
                  @click="showCurrentPassword = !showCurrentPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <img
                    :src="showCurrentPassword ? LoginEyeOnIcon : LoginEyeOffIcon"
                    alt="toggle current password"
                    class="h-5 w-5 opacity-70"
                  />
                </button>
              </div>
            </div>

            <div>
              <div class="relative">
                <input
                  v-model="newPassword"
                  :type="showNewPassword ? 'text' : 'password'"
                  placeholder="Enter New Password"
                  class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 pr-10 text-[16px] text-[#171717] outline-none"
                />

                <button
                  type="button"
                  @click="showNewPassword = !showNewPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <img
                    :src="showNewPassword ? LoginEyeOnIcon : LoginEyeOffIcon"
                    alt="toggle new password"
                    class="h-5 w-5 opacity-70"
                  />
                </button>
              </div>
            </div>

            <div>
              <div class="relative">
                <input
                  v-model="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="Repeat New Password"
                  class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 pr-10 text-[16px] text-[#171717] outline-none"
                />

                <button
                  type="button"
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <img
                    :src="showConfirmPassword ? LoginEyeOnIcon : LoginEyeOffIcon"
                    alt="toggle confirm password"
                    class="h-5 w-5 opacity-70"
                  />
                </button>
              </div>
            </div>

            <p v-if="passwordMismatch" class="text-sm text-red-500">
              The new password and the confirm password do not match.
            </p>
          </div>
        </template>
      </section>

      <section class="rounded-[24px] bg-white p-6">
        <h2 class="text-[18px] font-semibold text-[#171717]">Language & Region</h2>

        <div class="mt-6 flex max-w-[450px] flex-col gap-3">
          <div>
            <label class="mb-1 block text-[16px] font-medium text-[#404040]">
              Language
            </label>
            <div class="relative">
              <select
                v-model="language"
                class="h-11 w-full appearance-none rounded-md border border-[#d4d4d4] bg-white px-3 pr-10 text-[16px] text-[#171717] outline-none cursor-pointer"
              >
                <option>English</option>
                <option>Vietnamese</option>
              </select>

              <img
                :src="DropDown"
                alt="Open"
                class="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2"
              />
            </div>
          </div>

          <div>
            <label class="mb-1 block text-[16px] font-medium text-[#404040]">
              Region
            </label>
            <div class="relative">
              <select
                v-model="region"
                class="h-11 w-full appearance-none rounded-md border border-[#d4d4d4] bg-white px-3 pr-10 text-[16px] text-[#171717] outline-none cursor-pointer"
              >
                <option>Asia/Bangkok</option>
                <option>Asia/Ho_Chi_Minh</option>
                <option>UTC</option>
              </select>

              <img
                :src="DropDown"
                alt="Open"
                class="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2"
              />
            </div>
          </div>
        </div>

        <div class="mt-6">
          <p v-if="errorMessage" class="mb-3 text-sm text-red-500">
            {{ errorMessage }}
          </p>

          <p v-if="successMessage" class="mb-3 text-sm text-green-600">
            {{ successMessage }}
          </p>

          <button
            type="button"
            :disabled="!canSave"
            @click="handleSave"
            class="rounded-md px-6 py-3 text-white transition"
            :class="
              canSave
                ? 'bg-[#5c01d5] hover:opacity-90 cursor-pointer'
                : 'cursor-not-allowed bg-[#5c01d5]/20'
            "
          >
            {{ isSaving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>