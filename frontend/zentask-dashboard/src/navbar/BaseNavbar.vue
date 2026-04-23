<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  BellIcon,
  SettingIcon,
  TaskSquareIcon,
  BriefcaseIcon,
  LogoutIcon,
  DividerTop,
  DividerBottom,
} from '@/icons'

interface Props {
  title?: string
  avatarSrc?: string
  hasNotification?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  avatarSrc: '',
  hasNotification: true,
})

const router = useRouter()
const route = useRoute()

const isDropdownOpen = ref(false)
const isLoggingOut = ref(false)
const avatar = ref('')
const displayName = ref('')

const syncAvatar = () => {
  const saved = localStorage.getItem('avatar')
  avatar.value = saved || props.avatarSrc
}

const syncDisplayName = () => {
  const savedFullName = localStorage.getItem('full_name')?.trim()
  const savedEmail = localStorage.getItem('user_identifier')?.trim()
  displayName.value = savedFullName || savedEmail || ''
}

const navbarTitle = computed(() => {
  const propTitle = props.title?.trim()
  if (propTitle) return propTitle

  const routeTitle = (route.meta.navbarTitle as string)?.trim()
  if (routeTitle) return routeTitle

  const name = displayName.value?.trim()
  if (!name) return ''

  return `Welcome back, ${name}!`
})

const handleProfileUpdated = () => {
  syncDisplayName()
  syncAvatar()
}

onMounted(() => {
  syncDisplayName()
  syncAvatar()

  window.addEventListener('profile-updated', handleProfileUpdated)
  window.addEventListener('storage', handleProfileUpdated)
})

onBeforeUnmount(() => {
  window.removeEventListener('profile-updated', handleProfileUpdated)
  window.removeEventListener('storage', handleProfileUpdated)
})

const openDropdown = () => {
  isDropdownOpen.value = true
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const goToSettings = () => {
  router.push('/settings')
}

const goToCreateTask = () => {
  router.push('/create-task')
}

const goToMyWork = () => {
  router.push('/my-work')
}

const handleLogout = async () => {
  if (isLoggingOut.value) return

  const accessToken = localStorage.getItem('access_token')
  const refreshToken = localStorage.getItem('refresh_token')

  if (!accessToken || !refreshToken) {
    localStorage.clear()
    router.push('/login')
    return
  }

  isLoggingOut.value = true

  try {
    await fetch('http://127.0.0.1:8000/api/auth/logout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        refresh: refreshToken,
      }),
    })
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('full_name')
    localStorage.removeItem('user_identifier')

    router.push('/login')

    isLoggingOut.value = false
    isDropdownOpen.value = false
  }
}
</script>

<template>
  <header
    class="flex h-16 w-full items-center justify-between border-b border-[#e5e5e5] px-6 pl-8 text-left font-inter text-base text-[#171717]"
  >
    <div class="flex items-center">
      <h1 class="leading-6 font-semibold">
        {{ navbarTitle }}
      </h1>
    </div>

    <div class="flex items-center gap-4">
      <div class="relative h-10 w-10 rounded-full bg-white">
        <img
          :src="BellIcon"
          alt="Notification"
          class="absolute left-1/2 top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 object-contain"
        />
        <div
          v-if="props.hasNotification"
          class="absolute right-0 top-0 h-3 w-3 rounded-full border border-white bg-[#5c01d5]"
        />
      </div>

      <div
        class="relative flex items-center gap-3"
        @mouseenter="openDropdown"
        @mouseleave="closeDropdown"
      >
        <img
          :src="avatar"
          alt="Avatar"
          class="h-10 w-10 cursor-pointer rounded-full object-cover"
        />

        <transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-1"
        >
          <div
            v-if="isDropdownOpen"
            class="absolute right-0 top-[48px] z-50 w-[220px] rounded-xl border border-[#ececec] bg-white p-1 shadow-[0_10px_30px_rgba(0,0,0,0.08)]"
          >
            <div class="flex w-full flex-col items-start gap-1 p-1 text-left text-base text-[#404040] font-inter">
              <button
                type="button"
                @click="goToSettings"
                class="flex w-full items-center gap-2 rounded-num-6 bg-[#f5f5f5] p-2 text-[#171717] hover:bg-[#efefef] cursor-pointer"
              >
                <img :src="SettingIcon" class="h-5 w-5" />
                <div>Setting</div>
              </button>

              <img :src="DividerTop" class="h-px w-full" />

              <div class="flex w-full flex-col items-start">
                <div class="p-1 text-xs text-[#737373]">
                  Personal Tools
                </div>

                <button
                  @click="goToCreateTask"
                  class="flex w-full items-center gap-2 p-2 hover:bg-[#f7f7f7] cursor-pointer"
                >
                  <img :src="TaskSquareIcon" class="h-5 w-5" />
                  <div>Create Task</div>
                </button>

                <button
                  @click="goToMyWork"
                  class="flex w-full items-center gap-2 p-2 hover:bg-[#f7f7f7] cursor-pointer"
                >
                  <img :src="BriefcaseIcon" class="h-5 w-5" />
                  <div>My Work</div>
                </button>
              </div>

              <img :src="DividerBottom" class="h-px w-full" />

              <button
                @click="handleLogout"
                class="flex w-full items-center gap-2 p-2 hover:bg-[#f7f7f7] cursor-pointer text-[#d00000]"
              >
                <img :src="LogoutIcon" class="h-5 w-5" />
                <div>
                  {{ isLoggingOut ? 'Logging out...' : 'Log out' }}
                </div>
              </button>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </header>
</template>