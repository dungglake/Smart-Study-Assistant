<script setup lang="ts">
import { ref } from 'vue'
import BaseNavbar from '@/navbar/BaseNavbar.vue'
import {
  Gantt,
  Calendar,
  Overview,
  DropDown
} from '@/icons'

const activeTab = ref<'overview' | 'calendar' | 'gantt'>('overview')
</script>

<template>
  <div class="w-full bg-white">
    <BaseNavbar title="Chào mừng testuser đã quay lại!" />

    <div
      class="w-full border-b border-gainsboro box-border flex items-center py-0 pl-8 pr-6 gap-6 text-left text-[14px] text-dimgray font-inter"
    >
      <!-- Left tabs -->
      <div class="flex-1 flex items-center gap-6">
        <!-- Overview -->
        <div
          class="flex flex-col items-center pt-3 pb-1.5 border-b transition-all duration-150 cursor-pointer select-none"
          :class="activeTab === 'overview'
            ? 'border-gray text-gray'
            : 'border-transparent text-dimgray hover:text-gray'"
          @click="activeTab = 'overview'"
        >
          <div class="rounded-md flex items-center justify-center py-2 gap-2">
            <img :src="Overview" class="h-5 w-5 object-contain" alt="Overview" />
            <div class="leading-5 font-medium">Overview</div>
          </div>
        </div>

        <!-- Calendar -->
        <div
          class="flex flex-col items-center pt-3 pb-1.5 border-b transition-all duration-150 cursor-pointer select-none"
          :class="activeTab === 'calendar'
            ? 'border-gray text-gray'
            : 'border-transparent text-dimgray hover:text-gray'"
          @click="activeTab = 'calendar'"
        >
          <div class="rounded-md flex items-center justify-center py-2 gap-2">
            <img :src="Calendar" class="h-5 w-5 object-contain" alt="Calendar" />
            <div class="leading-5 font-medium">Calendar</div>
          </div>
        </div>

        <!-- Gantt -->
        <div
          class="flex flex-col items-center pt-3 pb-1.5 border-b transition-all duration-150 cursor-pointer select-none"
          :class="activeTab === 'gantt'
            ? 'border-gray text-gray'
            : 'border-transparent text-dimgray hover:text-gray'"
          @click="activeTab = 'gantt'"
        >
          <div class="rounded-md flex items-center justify-center py-2 gap-2">
            <img :src="Gantt" class="h-5 w-5 object-contain" alt="Gantt" />
            <div class="leading-5 font-medium">Gantt</div>
          </div>
        </div>
      </div>

      <!-- Date range -->
      <div
        class="w-[252px] rounded-md bg-white border border-lightgray box-border flex items-center py-1.5 px-2.5 gap-1.5 text-darkslategray"
      >
        <img :src="Calendar" class="h-5 w-5 object-contain" alt="Calendar" />
        <div class="flex-1 leading-5 font-medium">12/12/2025 - 04/01/2026</div>
        <img :src="DropDown" class="h-5 w-5 object-contain" alt="Dropdown" />
      </div>

      <!-- Add schedule button -->
      <div class="flex items-center text-white">
        <div class="rounded-l-md bg-[#5c01d5] flex items-center py-1.5 px-2.5">
          <div class="leading-5 font-medium">
            Thêm lịch học &amp; công việc
          </div>
        </div>
        <div
          class="rounded-r-md bg-[#5c01d5] border-l border-white/20 flex items-center justify-center p-1.5"
        >
          <img
            :src="DropDown"
            class="h-5 w-5 object-contain"
            alt="Dropdown"
          />
        </div>
      </div>
    </div>
  </div>
</template>