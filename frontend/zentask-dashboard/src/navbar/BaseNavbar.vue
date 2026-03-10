<script setup lang="ts">
import { BellIcon } from '@/icons'

interface Props {
  title: string
  avatarSrc?: string
  hasNotification?: boolean
}

withDefaults(defineProps<Props>(), {
  avatarSrc: 'https://i.pravatar.cc/100?img=12',
  hasNotification: true,
})
</script>

<template>
  <header
    class="flex h-16 w-full items-center justify-between border-b border-[#e5e5e5] px-6 pl-8 text-left font-inter text-base text-[#171717]"
  >
    <div class="flex items-center">
      <h1 class="leading-6 font-semibold">
        {{ title }}
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
          v-if="hasNotification"
          class="absolute right-0 top-0 h-3 w-3 rounded-full border border-white bg-[#5c01d5]"
        />
      </div>

      <img
        :src="avatarSrc"
        alt="Avatar"
        class="h-10 w-10 rounded-full object-cover"
      />
    </div>
  </header>
</template>