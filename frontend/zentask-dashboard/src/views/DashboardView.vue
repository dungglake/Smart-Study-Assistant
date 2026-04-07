<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
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
const isHistoryDropdownOpen = ref(false);
const historyDropdownRef = ref(null);
const hoveredBar = ref(null);
const activeChartDay = ref("Saturday");
const chartWrapRef = ref(null);
const chartRenderWidth = ref(860);
const isChartDropdownOpen = ref(false);

function selectHistoryFilter(value) {
  historyFilter.value = value;
  isHistoryDropdownOpen.value = false;
}

function selectChartFilter(value) {
  chartFilter.value = value;
  isChartDropdownOpen.value = false;
}

function handleClickOutside(event) {
  if (!historyDropdownRef.value?.contains(event.target)) {
    isHistoryDropdownOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleClickOutside);
});

function updateChartRenderWidth() {
  if (!chartWrapRef.value) return;
  chartRenderWidth.value = chartWrapRef.value.clientWidth;
}

onMounted(() => {
  updateChartRenderWidth();
  window.addEventListener("resize", updateChartRenderWidth);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", updateChartRenderWidth);
});

const summary = ref({
  studyTime: null,
  studyTimeTrend: "Pending API",
  subjects: null,
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
const tooltipPosition = computed(() => {
  if (!hoveredPoint.value) return null;

  const scaleX = chartRenderWidth.value / chartWidth;
  const scaleY = scaleX; 

  return {
    left: hoveredPoint.value.x * scaleX,
    top: (hoveredPoint.value.y - 138) * scaleY,
  };
});
const currentMonthLabel = computed(() => {
  if (!visibleDays.value.length) return "";

  const middleDay = visibleDays.value[7];
  const d = new Date(middleDay.fullDate);

  return d.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric"
  });
});

/* ===== MOCK DATA CHO STUDY TIME CHART ===== */
const chartData = ref([
  { day: "Monday", short: "Monday", hours: 4, subjects: ["UI/UX Design"] },
  { day: "Tuesday", short: "Tuesday", hours: 7, subjects: ["UI/UX Design", "Marketing"] },
  { day: "Wednesday", short: "Wednesday", hours: 5, subjects: ["Database"] },
  { day: "Thursday", short: "Thursday", hours: 9, subjects: ["Database", "AI Basics"] },
  { day: "Friday", short: "Friday", hours: 9, subjects: ["AI Basics", "Practice"] },
  { day: "Saturday", short: "Saturday", hours: 7.5, subjects: ["A", "B"] },
  { day: "Sunday", short: "Sunday", hours: 0, subjects: [] }
]);

const todaySchedule = ref([]);

const documentHistory = ref([]);

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

/* ===== AREA CHART LAYOUT ===== */
const chartWidth = 760;
const chartHeight = 430;
const chartPaddingTop = 40;
const chartPaddingRight = 36;
const chartPaddingBottom = 56;
const chartPaddingLeft = 60;
const chartMaxY = 12;

const innerWidth = computed(() => chartWidth - chartPaddingLeft - chartPaddingRight);
const innerHeight = computed(() => chartHeight - chartPaddingTop - chartPaddingBottom);

const xStep = computed(() => innerWidth.value / (chartData.value.length - 1));

const chartPoints = computed(() => {
  return chartData.value.map((item, index) => {
    const x = chartPaddingLeft + index * xStep.value;
    const y =
      chartPaddingTop +
      innerHeight.value -
      (item.hours / chartMaxY) * innerHeight.value;

    return {
      ...item,
      x,
      y,
    };
  });
});

function buildSmoothLinePath(points) {
  if (!points.length) return "";

  let path = `M ${points[0].x} ${points[0].y}`;

  for (let i = 0; i < points.length - 1; i++) {
    const current = points[i];
    const next = points[i + 1];
    const cx = (current.x + next.x) / 2;

    path += ` C ${cx} ${current.y}, ${cx} ${next.y}, ${next.x} ${next.y}`;
  }

  return path;
}

const linePath = computed(() => buildSmoothLinePath(chartPoints.value));

const areaPath = computed(() => {
  if (!chartPoints.value.length) return "";

  const first = chartPoints.value[0];
  const last = chartPoints.value[chartPoints.value.length - 1];
  const baseY = chartPaddingTop + innerHeight.value;

  const smoothLine = buildSmoothLinePath(chartPoints.value);

  return `${smoothLine} L ${last.x} ${baseY} L ${first.x} ${baseY} Z`;
});

const yTicks = computed(() => Array.from({ length: 13 }, (_, i) => 12 - i));

const hoveredPoint = computed(() => {
  const targetDay = hoveredBar.value || activeChartDay.value;
  return chartPoints.value.find(item => item.day === targetDay) || null;
});

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
              class="mt-6 px-3 py-1.5 rounded-lg bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition cursor-pointer"
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
          class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition cursor-pointer"
          @click="goPrevWeek"
        >
          <img :src="ChevronLeft" alt="previous" class="w-5 h-5" />
        </button>

        <div class="text-base font-medium">
          {{ currentMonthLabel }}
        </div>

        <button
          class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center transition cursor-pointer"
          @click="goNextWeek"
        >
          <img :src="ChevronRight" alt="next" class="w-5 h-5" />
        </button>
      </div>

      <div class="grid grid-cols-7 md:grid-cols-14 gap-3">
        <div
          v-for="day in visibleDays"
          :key="day.fullDate"
          class="rounded-full px-2 py-4 flex flex-col items-center gap-2 transition cursor-pointer hover:bg-violet-50"
          :class="[
            day.isMuted ? 'opacity-30' : '',
            selectedDate === day.fullDate ? 'w-[56px] bg-amber-50' : 'w-[56px]'
          ]"
          @click="selectDate(day.fullDate)"
        >
          <div
            class="text-sm font-bold"
            :class="day.isSunday ? 'text-red-500' : 'text-gray-700'"
          >
            {{ day.label }}
          </div>

          <div
            class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold"
            :class="
              selectedDate === day.fullDate
                ? 'bg-violet-600 text-white'
                : day.isSunday
                  ? 'bg-gray-100 text-red-500'
                  : 'bg-gray-100 text-gray-700'
            "
          >
            {{ day.day }}
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[1.6fr_1.12fr] gap-6 mb-6">
      <div class="rounded-3xl bg-white p-6 shadow-sm border border-gray-100">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-semibold">Study time</h3>

          <div class="relative">
            <button
              type="button"
              @click="isChartDropdownOpen = !isChartDropdownOpen"
              class="flex h-10 min-w-[128px] items-center justify-between rounded-lg border border-gray-200 bg-white pl-4 pr-3 text-sm text-gray-600 outline-none transition hover:border-violet-300 hover:bg-violet-50 cursor-pointer"
            >
              <span>{{ chartFilter }}</span>

              <img
                :src="ChevronRight"
                alt="dropdown"
                class="h-4 w-4 transition"
                :class="isChartDropdownOpen ? 'rotate-[270deg] opacity-100' : 'rotate-90 opacity-60'"
              />
            </button>

            <div
              v-if="isChartDropdownOpen"
              class="absolute right-0 top-[calc(100%+8px)] z-20 min-w-[128px] rounded-xl border border-gray-200 bg-white p-1 shadow-lg"
            >
              <button
                type="button"
                @click="selectChartFilter('This week')"
                class="flex w-full rounded-lg px-3 py-2 text-left text-sm transition cursor-pointer"
                :class="
                  chartFilter === 'This week'
                    ? 'bg-violet-50 text-blue-700'
                    : 'text-gray-700 hover:bg-violet-50 hover:text-blue-700'
                "
              >
                This week
              </button>

              <button
                type="button"
                @click="selectChartFilter('This month')"
                class="flex w-full rounded-lg px-3 py-2 text-left text-sm transition cursor-pointer"
                :class="
                  chartFilter === 'This month'
                    ? 'bg-violet-50 text-blue-700'
                    : 'text-gray-700 hover:bg-violet-50 hover:text-blue-700'
                "
              >
                This month
              </button>
            </div>
          </div>
        </div>

        <div class="relative">
          <div ref="chartWrapRef" class="w-full overflow-x-auto pb-1">
            <svg
              :viewBox="`0 0 ${chartWidth} ${chartHeight}`"
              class=" block w-full min-w-[760px]"
            >
              <defs>
                <linearGradient id="studyAreaFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#7c3aed" stop-opacity="0.28" />
                  <stop offset="100%" stop-color="#7c3aed" stop-opacity="0.12" />
                </linearGradient>
              </defs>

              <!-- Grid -->
              <g>
                <line
                  v-for="tick in yTicks"
                  :key="tick"
                  :x1="chartPaddingLeft"
                  :x2="chartWidth - chartPaddingRight"
                  :y1="chartPaddingTop + ((12 - tick) / 12) * innerHeight"
                  :y2="chartPaddingTop + ((12 - tick) / 12) * innerHeight"
                  stroke="#d9d9d9"
                  stroke-dasharray="3 4"
                  stroke-width="1"
                />
              </g>

              <!-- Y labels -->
              <g>
                <text
                  x="8"
                  y="10"
                  fill="#171717"
                  font-size="14"
                  font-weight="500"
                >
                  Hours
                </text>

                <text
                  v-for="tick in yTicks"
                  :key="`label-${tick}`"
                  x="44"
                  :y="chartPaddingTop + ((12 - tick) / 12) * innerHeight + 5"
                  text-anchor="end"
                  fill="#171717"
                  font-size="12"
                >
                  {{ tick }}
                </text>
              </g>

              <!-- Area -->
              <path
                :d="areaPath"
                fill="url(#studyAreaFill)"
              />

              <!-- Line -->
              <path
                :d="linePath"
                fill="none"
                stroke="#6d28ff"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />

              <!-- Points hover zone -->
              <g v-for="(point, index) in chartPoints" :key="`hover-zone-${point.day}`">
                <rect
                  :x="index === 0 ? chartPaddingLeft : point.x - xStep / 2"
                  :y="chartPaddingTop"
                  :width="index === 0 || index === chartPoints.length - 1 ? xStep / 2 : xStep"
                  :height="innerHeight"
                  fill="transparent"
                  class="cursor-pointer"
                  @mouseenter="hoveredBar = point.day"
                  @mouseleave="hoveredBar = null"
                  @click="activeChartDay = point.day"
                />
              </g>

              <!-- Active point -->
              <circle
                v-if="hoveredPoint"
                :cx="hoveredPoint.x"
                :cy="hoveredPoint.y"
                r="6"
                fill="#6d28ff"
                stroke="#ffffff"
                stroke-width="2"
              />

              <!-- X labels -->
              <g>
                <text
                  v-for="point in chartPoints"
                  :key="`x-${point.day}`"
                  :x="point.x"
                  :y="chartHeight - 16"
                  text-anchor="middle"
                  fill="#171717"
                  font-size="14"
                >
                  {{ point.short }}
                </text>
              </g>
            </svg>

            <!-- Tooltip HTML overlay -->
            <div
              v-if="hoveredPoint && tooltipPosition"
              class="pointer-events-none absolute z-10"
              :style="{
                left: `${tooltipPosition.left}px`,
                top: `${tooltipPosition.top}px`
              }"
            >
              <div class="relative -translate-x-1/2">
                <div
                  class="relative w-[185px] rounded-[20px] border border-[#d9d9d9] bg-white px-4 py-3 shadow-[0_4px_14px_rgba(0,0,0,0.10)]"
                >
                  <div class="inline-flex rounded-full bg-[#6d28ff] px-4 py-1 text-white text-[12px] font-medium">
                    {{ hoveredPoint.day }}
                  </div>

                  <div class="mt-3 text-[14px] leading-6 text-[#171717]">
                    <div>Study time: {{ Math.round(hoveredPoint.hours) }} hours</div>
                    <div>
                      Subjects:
                      {{
                        hoveredPoint.subjects?.length
                          ? hoveredPoint.subjects.join(" and ")
                          : "No data yet"
                      }}
                    </div>
                  </div>

                  <div
                    class="absolute left-1/2 top-full h-4 w-4 -translate-x-1/2 -translate-y-1/2 rotate-45 border-b border-r border-[#d9d9d9] bg-white"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-5 text-sm text-gray-500">
            * Visualization is currently using mock data and can be replaced with API data later.
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

        <div class="relative" ref="historyDropdownRef">
          <button
            type="button"
            @click="isHistoryDropdownOpen = !isHistoryDropdownOpen"
            class="flex h-10 min-w-[128px] items-center justify-between rounded-lg border border-gray-200 bg-white pl-3 pr-3 text-sm text-gray-600 outline-none transition hover:border-violet-300 hover:bg-violet-50 cursor-pointer"
          >
            <span>{{ historyFilter }}</span>

            <img
              :src="ChevronRight"
              alt="dropdown"
              class="h-4 w-4 transition"
              :class="isHistoryDropdownOpen ? 'rotate-[270deg] opacity-100' : 'rotate-90 opacity-60'"
            />
          </button>

          <div
            v-if="isHistoryDropdownOpen"
            class="absolute right-0 top-[calc(100%+8px)] z-20 min-w-[128px] rounded-xl border border-gray-200 bg-white p-1 shadow-lg"
          >
            <button
              type="button"
              @click="selectHistoryFilter('This week')"
              class="flex w-full rounded-lg px-3 py-2 text-left text-sm transition cursor-pointer"
              :class="
                historyFilter === 'This week'
                  ? 'bg-violet-50 text-blue-700'
                  : 'text-gray-700 hover:bg-violet-50 hover:text-blue-700'
              "
            >
              This week
            </button>

            <button
              type="button"
              @click="selectHistoryFilter('This month')"
              class="flex w-full rounded-lg px-3 py-2 text-left text-sm transition cursor-pointer"
              :class="
                historyFilter === 'This month'
                  ? 'bg-violet-50 text-blue-700'
                  : 'text-gray-700 hover:bg-violet-50 hover:text-blue-700'
              "
            >
              This month
            </button>
          </div>
        </div>
      </div>

      <div v-if="documentHistory.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
        <div
          v-for="(doc, index) in documentHistory"
          :key="index"
          class="rounded-2xl bg-[#f3ecff] p-4 flex flex-col justify-between min-h-[170px]"
        >
          <div>
            <h4 class="font-medium line-clamp-2 text-[#2f2f2f]">{{ doc.title }}</h4>
            <p class="text-sm mt-2 text-[#6b7280]">{{ doc.date }}</p>
          </div>

          <button
            class="mt-4 px-3 py-2 rounded-lg bg-gray-900 text-sm font-medium text-white hover:bg-gray-800 transition self-start"
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