<script setup lang="ts">
import { ref } from 'vue'
import SmartSchedulerNavbar from '@/navbar/SmartSchedulerNavbar.vue'

const isTimeConfigOpen = ref(false)
const isSubjectListOpen = ref(false)
const isGeneratePopupOpen = ref(false)
const savedSubjects = ref<any[]>([])
const latestGeneratedSummary = ref<any>(null)

function openGeneratePopup() {
  isTimeConfigOpen.value = false
  isSubjectListOpen.value = false
  isGeneratePopupOpen.value = true
}

function openTimeConfig() {
  isGeneratePopupOpen.value = false
  isSubjectListOpen.value = false
  isTimeConfigOpen.value = true
}

function openSubjectList() {
  isGeneratePopupOpen.value = false
  isTimeConfigOpen.value = false
  isSubjectListOpen.value = true
}

function closeGeneratePopup() {
  isGeneratePopupOpen.value = false
}

function handleGeneratedSummary(payload: any) {
  latestGeneratedSummary.value = payload
}

function handleSaveSubjects(payload: any[]) {
  savedSubjects.value = payload
}
</script>

<template>
  <div class="min-h-screen w-full bg-[#f5f5f5]">
    <SmartSchedulerNavbar
      @open-time-config="openTimeConfig"
      @open-subject-list="openSubjectList"
      @open-generate-popup="openGeneratePopup"
    />

    <router-view v-slot="{ Component }">
      <component
        :is="Component"
        :is-time-config-open="isTimeConfigOpen"
        :is-subject-list-open="isSubjectListOpen"
        :subjects="savedSubjects"
        :is-generate-popup-open="isGeneratePopupOpen"
        :generated-summary="latestGeneratedSummary"
        @close-time-config="isTimeConfigOpen = false"
        @close-subject-list="isSubjectListOpen = false"
        @save-subjects="handleSaveSubjects"
        @close-generate-popup="closeGeneratePopup"
        @open-time-config="openTimeConfig"
        @open-subject-list="openSubjectList"
        @generated-summary="handleGeneratedSummary"
      />
    </router-view>
  </div>
</template>