<script setup lang="ts">
import { ref } from 'vue'
import SmartSchedulerNavbar from '@/navbar/SmartSchedulerNavbar.vue'

const isTimeConfigOpen = ref(false)
const isSubjectListOpen = ref(false)
const savedSubjects = ref([])
</script>

<template>
  <div class="min-h-screen w-full bg-[#f5f5f5]">
    <SmartSchedulerNavbar
      @open-time-config="isTimeConfigOpen = true"
      @open-subject-list="isSubjectListOpen = true"
    />

    <router-view v-slot="{ Component }">
      <component
        :is="Component"
        :is-time-config-open="isTimeConfigOpen"
        :is-subject-list-open="isSubjectListOpen"
        :subjects="savedSubjects"
        @close-time-config="isTimeConfigOpen = false"
        @close-subject-list="isSubjectListOpen = false"
        @save-subjects="savedSubjects = $event"
      />
    </router-view>
  </div>
</template>