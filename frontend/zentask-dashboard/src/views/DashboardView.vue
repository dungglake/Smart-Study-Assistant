<script setup>
import { computed, ref } from "vue";
import {
  Book,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock,
  Document,
  Plus,
  BannerGlow,
  BannerDocs
} from "@/icons"

const chartFilter = ref("This week");
const historyFilter = ref("This week");
const hoveredBar = ref(null);

const summary = ref({
  studyTime: null, // ví dụ API sau này: "156 hours 45 minutes"
  studyTimeTrend: "Pending API",
  subjects: null, // ví dụ API sau này: "6 Subjects"
  subjectTrend: "Pending API"
});

const currentBaseDate = ref(new Date("2026-01-01"));
const selectedDate = ref("2026-01-03");

const visibleDays = computed(() => {
  const base = new Date(currentBaseDate.value);
  const days = [];
  const labels = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"];

  for (let i = -3; i < 11; i++) {
    const d = new Date(base);
    d.setDate(base.getDate() + i);

    const jsDay = d.getDay();
    const mappedIndex = jsDay === 0 ? 6 : jsDay - 1;

    days.push({
      label: labels[mappedIndex],
      day: String(d.getDate()).padStart(2, "0"),
      fullDate: formatDate(d),
      isSunday: jsDay === 0,
      isMuted: i < 0
    });
  }

  return days;
});

const currentMonthLabel = computed(() => {
  const d = new Date(selectedDate.value);
  return d.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric"
  });
});

const chartData = ref([
  { day: "Mon", fullLabel: "Monday", hours: 3, subjects: [] },
  { day: "Tue", fullLabel: "Tuesday", hours: 5, subjects: [] },
  { day: "Wed", fullLabel: "Wednesday", hours: 4, subjects: [] },
  { day: "Thu", fullLabel: "Thursday", hours: 6, subjects: [] },
  { day: "Fri", fullLabel: "Friday", hours: 2, subjects: [] },
  { day: "Sat", fullLabel: "Saturday", hours: 7, subjects: [] },
  { day: "Sun", fullLabel: "Sunday", hours: 1, subjects: [] }
]);

const todaySchedule = ref([]);
// sau này API có thể trả:
// [
//   { subject: "Database Administration", time: "2:00 PM - 4:00 PM", type: "Practice" }
// ]

const documentHistory = ref([]);
// sau này API có thể trả:
// [
//   { title: "UI Creation Process From Wireframe Using AI", date: "01/01/2026 7:00 PM" }
// ]

const todayLabel = computed(() => {
  const d = new Date(selectedDate.value);
  return d.toLocaleDateString("en-GB", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  });
});

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function selectDate(date) {
  selectedDate.value = date;
}

function goPrevWeek() {
  const d = new Date(currentBaseDate.value);
  d.setDate(d.getDate() - 7);
  currentBaseDate.value = d;
}

function goNextWeek() {
  const d = new Date(currentBaseDate.value);
  d.setDate(d.getDate() + 7);
  currentBaseDate.value = d;
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>

<template>
  <div class="w-full min-h-screen bg-[#f5f5f7] p-8 text-gray-900">
    <div class="grid grid-cols-1 xl:grid-cols-[300px_300px_1fr] gap-6 mb-6">
      <div class="rounded-3xl bg-white p-4 shadow-sm border border-gray-100 h-[120px]">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
            <img :src="Clock" alt="clock icon" class="w-5 h-5" />
          </div>
          <h2 class="text-lg font-semibold">STUDY TIME</h2>
        </div>

        <div class="flex items-center gap-3">
          <p class="text-base text-gray-700">
            {{ summary.studyTime || "No data yet" }}
          </p>
          <span
            class="rounded-full bg-emerald-50 text-emerald-600 text-sm px-3 py-1 font-medium"
          >
            {{ summary.studyTimeTrend || "Pending API" }}
          </span>
        </div>
      </div>

      <div class="rounded-3xl bg-white p-4 shadow-sm border border-gray-100 h-[120px]">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
            <img :src="Book" alt="book icon" class="w-5 h-5" />
          </div>
          <h2 class="text-lg font-semibold">SUBJECTS</h2>
        </div>

        <div class="flex items-center gap-3">
          <p class="text-base text-gray-700">
            {{ summary.subjects || "No data yet" }}
          </p>
          <span
            class="rounded-full bg-emerald-50 text-emerald-600 text-sm px-3 py-1 font-medium"
          >
            {{ summary.subjectTrend || "Pending API" }}
          </span>
        </div>
      </div>

      <div class="relative h-[120px]">
        <div
          class="rounded-3xl bg-white border border-violet-200 shadow-[0_0_12px_rgba(92,1,213,0.08)_inset] p-4 relative overflow-hidden h-full"
        >
          <div class="relative z-[3] max-w-[70%] translate-y-1">
            <h2
              class="text-[18px] font-bold bg-gradient-to-r from-violet-700 to-indigo-500 bg-clip-text text-transparent leading-6 whitespace-nowrap"
            >
              Convert all documents to Text using AI
            </h2>

            <button
              class="mt-6 px-3 py-1.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition"
            >
              Free conversion
            </button>
          </div>

          <div
            class="absolute right-0 top-0 h-full w-[40%] from-white to-violet-50 z-[0]"
          ></div>
        </div>

        <img
          :src="BannerGlow"
          alt="banner glow"
          class="absolute -right-0 -top-3 h-[120%] w-[52%] object-cover pointer-events-none select-none z-[1]"
        />

        <img
          :src="BannerDocs"
          alt="document illustration"
          class="absolute right-3.5 -bottom-5 w-[150px] md:w-[170px] pointer-events-none select-none z-[4]"
        />
      </div>
    </div>

    <div class="rounded-3xl bg-white p-6 shadow-sm border border-gray-100 mb-6">
      <div class="flex items-center justify-center gap-3 mb-6">
        <button
          class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition"
          @click="goPrevWeek"
        >
          <img :src="ChevronLeft" alt="previous" class="w-5 h-5" />
        </button>

        <div class="text-base font-medium">
          {{ currentMonthLabel }}
        </div>

        <button
          class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition"
          @click="goNextWeek"
        >
          <img :src="ChevronRight" alt="next" class="w-5 h-5" />
        </button>
      </div>

      <div class="grid grid-cols-7 md:grid-cols-14 gap-3">
        <div
          v-for="day in visibleDays"
          :key="day.fullDate"
          class="rounded-full p-2 flex flex-col items-center gap-2 transition cursor-pointer hover:bg-violet-50"
          :class="[
            day.isMuted ? 'opacity-30' : '',
            selectedDate === day.fullDate ? 'bg-amber-100' : ''
          ]"
          @click="selectDate(day.fullDate)"
        >
          <div
            class="text-sm font-semibold"
            :class="day.isSunday ? 'text-red-500' : 'text-gray-700'"
          >
            {{ day.label }}
          </div>

          <div
            class="w-10 h-10 rounded-full flex items-center justify-center text-sm"
            :class="
              selectedDate === day.fullDate
                ? 'bg-violet-600 text-white'
                : 'bg-gray-100 text-gray-700'
            "
          >
            {{ day.day }}
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-6 mb-6">
      <div class="rounded-3xl bg-white p-6 shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-semibold">Study time</h3>

          <select
            v-model="chartFilter"
            class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 outline-none"
          >
            <option>This week</option>
            <option>This month</option>
          </select>
        </div>

        <div class="relative">
          <div class="grid grid-cols-7 gap-4 items-end h-80">
            <div
              v-for="item in chartData"
              :key="item.day"
              class="flex flex-col items-center justify-end h-full relative"
            >
              <div
                class="w-full max-w-[54px] rounded-t-2xl bg-gradient-to-t from-violet-600 to-indigo-400 cursor-pointer transition hover:opacity-90 relative"
                :style="{ height: `${item.hours * 22}px` }"
                @mouseenter="hoveredBar = item.day"
                @mouseleave="hoveredBar = null"
              >
                <div
                  v-if="hoveredBar === item.day"
                  class="absolute bottom-[calc(100%+12px)] left-1/2 -translate-x-1/2 bg-white border border-gray-200 shadow-lg rounded-2xl p-3 text-sm w-48 z-10"
                >
                  <div class="inline-flex px-2 py-1 rounded-full bg-violet-100 text-violet-700 font-medium mb-2">
                    {{ item.fullLabel }}
                  </div>
                  <p class="text-gray-800">Study time: {{ item.hours }} hours</p>
                  <p class="text-gray-800">
                    Subjects:
                    {{ item.subjects?.length ? item.subjects.join(", ") : "No data yet" }}
                  </p>
                </div>
              </div>

              <div class="mt-3 text-sm text-gray-600">{{ item.day }}</div>
            </div>
          </div>

          <div class="mt-5 text-sm text-gray-500">
            * Visualization is currently using mock/placeholder data because API has not been connected yet.
          </div>
        </div>
      </div>

      <div class="rounded-3xl bg-white p-6 shadow-sm border border-gray-100">
        <div class="mb-6">
          <h3 class="text-xl font-semibold">Today's study schedule</h3>
          <p class="text-sm text-gray-500 mt-1">{{ todayLabel }}</p>
        </div>

        <div v-if="todaySchedule.length" class="space-y-4 max-h-[420px] overflow-y-auto pr-1">
          <div
            v-for="(item, index) in todaySchedule"
            :key="index"
            class="rounded-2xl p-4 bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-100"
          >
            <div class="pb-2 border-b border-gray-200">
              <h4 class="font-semibold text-gray-900">
                {{ item.subject || "Subject pending API" }}
              </h4>
            </div>

            <div class="pt-3 space-y-2 text-sm text-gray-700">
              <p>Time: {{ item.time || "Pending API" }}</p>
              <div class="flex items-center gap-2">
                <span>Type:</span>
                <span class="px-3 py-1 rounded-full bg-violet-600 text-white text-xs font-medium">
                  {{ item.type || "Pending API" }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div
          v-else
          class="h-[320px] flex flex-col items-center justify-center text-center text-gray-500"
        >
          <img :src="CalendarDays" alt="calendar icon" class="w-10 h-10 mb-3 opacity-30" />
          <p class="font-medium">No schedule data yet</p>
          <p class="text-sm mt-1">This section will display subjects after API integration.</p>
        </div>
      </div>
    </div>

    <div class="rounded-3xl bg-white p-6 shadow-sm border border-gray-100">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-semibold">Document Extraction History</h3>

        <select
          v-model="historyFilter"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-600 outline-none"
        >
          <option>This week</option>
          <option>This month</option>
        </select>
      </div>

      <div v-if="documentHistory.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
        <div
          v-for="(doc, index) in documentHistory"
          :key="index"
          class="rounded-2xl p-4 text-white flex flex-col justify-between min-h-[170px]"
          :class="index % 2 === 0 ? 'bg-violet-600' : 'bg-indigo-500'"
        >
          <div>
            <h4 class="font-medium line-clamp-2">{{ doc.title }}</h4>
            <p class="text-sm mt-2 text-white/80">{{ doc.date }}</p>
          </div>

          <button
            class="mt-4 px-3 py-2 rounded-lg bg-gray-900 text-sm font-medium hover:bg-gray-800 transition self-start"
          >
            View details
          </button>
        </div>

        <div
          class="rounded-2xl border border-dashed border-gray-300 p-4 min-h-[170px] flex flex-col items-center justify-center text-center text-gray-500 cursor-pointer hover:bg-gray-50 transition"
        >
          <img :src="Plus" alt="add icon" class="w-10 h-10 mb-3 opacity-30" />
          <p class="text-sm font-medium">Add new document</p>
        </div>
      </div>

      <div
        v-else
        class="min-h-[220px] flex flex-col items-center justify-center text-center text-gray-500"
      >
        <img :src="Document" alt="document icon" class="w-10 h-10 mb-3 opacity-30" />
        <p class="font-medium">No extraction history yet</p>
        <p class="text-sm mt-1">
          This section is ready but will display real data only after API integration.
        </p>
      </div>
    </div>
  </div>
</template>