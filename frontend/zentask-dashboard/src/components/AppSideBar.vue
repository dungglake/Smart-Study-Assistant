<script setup lang="ts">
import { Icon, icons } from "@/icons/iconsax"
</script>

<template>
  <div
    class="w-full h-full relative flex flex-col items-start justify-between py-num-12 px-4 box-border text-left text-num-14 text-darkslategray font-inter"
  >
    <div class="self-stretch flex flex-col items-start gap-8">

      <!-- SEARCH -->
      <div class="self-stretch flex flex-col items-start relative isolate">
        <div
          class="self-stretch rounded-num-6 bg-white border-lightgray border-solid border flex items-center py-2 px-num-12 gap-1.5"
        >

          <Icon :iconName="icons.search" type="Linear" size="20" />

          <div class="relative leading-num-20 font-medium">
            Search...
          </div>

        </div>
      </div>

      <!-- MENU -->
      <div class="self-stretch flex flex-col items-start gap-3 text-dimgray">

        <!-- DASHBOARD -->
        <div class="self-stretch border-mediumblue border-l flex items-center text-mediumblue">
          <div class="flex-1 rounded-num-6 flex items-center py-num-12 px-num-10 gap-1.5">

            <Icon :iconName="icons.dashboard" type="Bold" size="20" />

            <div class="relative leading-num-20 font-medium">
              Dashboard
            </div>

          </div>
        </div>

        <!-- SCHEDULER -->
        <div class="flex-1 rounded-num-6 flex items-center py-num-12 px-num-10 gap-1.5">

          <Icon :iconName="icons.scheduler" type="Linear" size="20" />

          <div class="leading-num-20 font-medium">
            Smart Scheduler
          </div>

        </div>

        <!-- EXTRACTOR -->
        <div class="flex-1 rounded-num-6 flex items-center py-num-12 px-num-10 gap-1.5">

          <Icon :iconName="icons.extractor" type="Linear" size="20" />

          <div class="leading-num-20 font-medium">
            AI Content Extractor
          </div>

        </div>

      </div>
    </div>

    <!-- FOOTER -->
    <div class="self-stretch flex flex-col items-start justify-center text-dimgray">

      <!-- FEEDBACK -->
      <div class="flex-1 rounded-num-6 flex items-center py-1.5 px-num-10 gap-1.5">

        <Icon :iconName="icons.feedback" type="Linear" size="20" />

        <div class="flex items-start">
          <div class="leading-num-20 font-medium">
            Feedback
          </div>

          <Icon :iconName="icons.arrow" type="Linear" size="14" />
        </div>

      </div>

      <!-- SUPPORT -->
      <div class="flex-1 rounded-num-6 flex items-center py-1.5 px-num-10 gap-1.5">

        <Icon :iconName="icons.support" type="Linear" size="20" />

        <div class="flex items-start">
          <div class="leading-num-20 font-medium">
            Hỗ trợ
          </div>

          <Icon :iconName="icons.arrow" type="Linear" size="14" />
        </div>

      </div>

    </div>
  </div>
</template>