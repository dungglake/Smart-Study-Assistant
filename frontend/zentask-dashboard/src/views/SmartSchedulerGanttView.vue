<script setup lang="ts">
const ganttRows = [
  { subject: 'UI/UX Design', start: '01 Jan', end: '07 Jan', progress: 0 },
  { subject: 'Marketing', start: '03 Jan', end: '09 Jan', progress: 0 },
  { subject: 'Database', start: '05 Jan', end: '11 Jan', progress: 0 },
]

const ganttDates = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
</script>

<template>
  <div class="px-8 pb-6 pt-8">
    <div class="rounded-[24px] bg-white p-6">
      <div class="mb-6 text-[18px] font-semibold leading-7 text-[#171717]">
        Gantt
      </div>

      <div class="overflow-hidden rounded-[16px] border border-[#e5e5e5]">
        <!-- header -->
        <div class="flex border-b border-[#e5e5e5] bg-[#fafafa]">
          <div class="w-[220px] border-r border-[#e5e5e5] px-4 py-3 font-medium text-[#171717]">
            Subject
          </div>
          <div class="flex flex-1">
            <div
              v-for="date in ganttDates"
              :key="date"
              class="flex-1 border-r border-[#e5e5e5] px-2 py-3 text-center text-sm text-[#737373]"
            >
              {{ date }}
            </div>
          </div>
        </div>

        <!-- rows -->
        <div
          v-for="row in ganttRows"
          :key="row.subject"
          class="flex border-b border-[#e5e5e5] last:border-b-0"
        >
          <div class="flex w-[220px] items-center border-r border-[#e5e5e5] px-4 py-4 text-[#171717]">
            {{ row.subject }}
          </div>

          <div class="relative flex flex-1">
            <div
              v-for="date in ganttDates"
              :key="`${row.subject}-${date}`"
              class="h-[64px] flex-1 border-r border-[#e5e5e5]"
            ></div>

            <!-- chưa có API/task nên chưa render thanh gantt thật -->
            <div class="absolute inset-0 flex items-center justify-center">
              <div class="rounded-full border border-dashed border-[#d4d4d4] bg-white px-4 py-2 text-xs text-[#737373]">
                No task data
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>