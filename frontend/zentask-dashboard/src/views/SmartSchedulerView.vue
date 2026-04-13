<script setup lang="ts">
import SmartSchedulerNavbar from '@/navbar/SmartSchedulerNavbar.vue'
</script>

<template>
  <div class="min-h-screen w-full bg-[#f5f5f5]">
    <SmartSchedulerNavbar />
    <router-view />
  </div>
</template>