<script setup>
import { computed, ref, onMounted, onBeforeUnmount, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { authJson } from "@/api/authFetch";
import {
  Book,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock,
  Document,
  BannerGlow,
  BannerDocs,
  ArrowDown,
} from "@/icons"

const route = useRoute();
const router = useRouter();

const chartFilter = ref("This week");
const historyFilter = ref("This week");
const isHistoryDropdownOpen = ref(false);
const historyDropdownRef = ref(null);
const hoveredBar = ref(null);
const activeChartDay = ref("Monday");
const chartWrapRef = ref(null);
const chartRenderWidth = ref(860);
const isChartDropdownOpen = ref(false);

const weekPlanSlots = ref([]);
const chartPlanSlots = ref([]);
const previousChartPlanSlots = ref([]);
const isScheduleLoading = ref(false);
const scheduleError = ref("");
const documentHistory = ref([])
const uploadInputRef = ref(null)
const isUploadingDocument = ref(false)

async function loadConversations() {
  try {
    const res = await authJson('/api/conversations/')
    documentHistory.value = res || []
  } catch (e) {
    documentHistory.value = []
  }
}

function handleConversationListUpdated() {
  loadConversations()
}

function goToAiContentExtractor() {
  router.push('/extractor')
}

function selectHistoryFilter(value) {
  historyFilter.value = value;
  isHistoryDropdownOpen.value = false;
}

function selectChartFilter(value) {
  chartFilter.value = value;
  isChartDropdownOpen.value = false;
  loadChartSchedule();
}

function handleClickOutside(event) {
  if (!historyDropdownRef.value?.contains(event.target)) {
    isHistoryDropdownOpen.value = false;
  }
}

function updateChartRenderWidth() {
  if (!chartWrapRef.value) return;
  chartRenderWidth.value = chartWrapRef.value.clientWidth;
}

onMounted(() => {
  loadConversations();

  document.addEventListener("click", handleClickOutside);
  window.addEventListener("resize", updateChartRenderWidth);
  window.addEventListener("planner-plan-updated", handlePlannerPlanUpdated);
  window.addEventListener("conversation-list-updated", handleConversationListUpdated);

  updateChartRenderWidth();
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleClickOutside);
  window.removeEventListener("resize", updateChartRenderWidth);
  window.removeEventListener("planner-plan-updated", handlePlannerPlanUpdated);
  window.removeEventListener("conversation-list-updated", handleConversationListUpdated);
});

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function parseQueryDate(value) {
  if (typeof value !== "string" || !value) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return today;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return today;
  }

  parsed.setHours(0, 0, 0, 0);
  return parsed;
}

function normalizeDate(date) {
  const next = new Date(date);
  next.setHours(0, 0, 0, 0);
  return next;
}

function getStartOfWeekMonday(date) {
  const next = normalizeDate(date);
  const day = next.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  next.setDate(next.getDate() + diff);
  return next;
}

function getEndOfWeekSunday(date) {
  const start = getStartOfWeekMonday(date);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return end;
}

function goToConversation(id) {
  router.push({
    path: '/extractor',
    query: {
      conversation_id: String(id),
    },
  })
}

function openUploadPicker() {
  uploadInputRef.value?.click()
}

async function handleDashboardFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  try {
    isUploadingDocument.value = true

    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', file.name)

    const res = await authJson('/api/materials/', {
      method: 'POST',
      body: formData,
    })

    const materialId = res?.material_id
    if (!materialId) {
      throw new Error('Upload failed: missing material_id')
    }

    await waitForConversationAndOpen(materialId)
  } catch (error) {
    console.error('Dashboard upload failed:', error)
    await loadConversations()
  } finally {
    isUploadingDocument.value = false
    if (uploadInputRef.value) {
      uploadInputRef.value.value = ''
    }
  }
}

async function waitForConversationAndOpen(materialId) {
  let tries = 0

  while (tries < 60) {
    const list = await authJson('/api/conversations/')

    const found = Array.isArray(list)
      ? list.find((c) => Number(c.material) === Number(materialId))
      : null

    if (found) {
      documentHistory.value = list || []
      window.dispatchEvent(new CustomEvent('conversation-list-updated'))

      await router.push({
        path: '/extractor',
        query: {
          conversation_id: found.id,
        },
      })
      return
    }

    await new Promise((resolve) => setTimeout(resolve, 1000))
    tries++
  }

  throw new Error('Conversation was not created in time.')
}

const selectedDateObject = computed(() => parseQueryDate(route.query.date));
const selectedDate = computed(() => formatDate(selectedDateObject.value));
const currentBaseDate = computed(() => getStartOfWeekMonday(selectedDateObject.value));
const selectedWeekStart = computed(() => getStartOfWeekMonday(selectedDateObject.value));
const selectedWeekStartKey = computed(() => formatDate(selectedWeekStart.value));

function syncRouteDate(date) {
  router.replace({
    query: {
      date: formatDate(normalizeDate(date)),
    },
  });
}

function selectDate(date) {
  syncRouteDate(new Date(date));
}

function goPrevWeek() {
  const d = new Date(selectedWeekStart.value);
  d.setDate(d.getDate() - 7);
  syncRouteDate(d);
}

function goNextWeek() {
  const d = new Date(selectedWeekStart.value);
  d.setDate(d.getDate() + 7);
  syncRouteDate(d);
}

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
  const d = selectedDateObject.value;
  return d.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric"
  });
});

function getSlotDate(slot) {
  return String(slot.start || "").slice(0, 10);
}

function getLocalTimeParts(value) {
  const text = String(value || "");
  const timeText = text.includes("T")
    ? text.split("T")[1]
    : text.split(" ")[1] || "00:00";

  const [hour = "0", minute = "0"] = timeText.slice(0, 5).split(":");

  return {
    hour: Number(hour),
    minute: Number(minute),
  };
}

function getSlotStartMinutes(slot) {
  const { hour, minute } = getLocalTimeParts(slot.start);
  return hour * 60 + minute;
}

function formatTimeRange(start, end) {
  const format = (value) => {
    const { hour, minute } = getLocalTimeParts(value);
    return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  };

  return `${format(start)}-${format(end)}`;
}

function slotDurationHours(slot) {
  const startMinutes = getSlotStartMinutes({ start: slot.start });
  const endMinutes = getSlotStartMinutes({ start: slot.end });

  if (!Number.isFinite(startMinutes) || !Number.isFinite(endMinutes)) return 0;

  return Math.max(0, (endMinutes - startMinutes) / 60);
}

function formatHours(hours) {
  if (!hours) return "0 hours";
  const rounded = Math.round(hours * 10) / 10;
  return `${rounded} ${rounded === 1 ? "hour" : "hours"}`;
}

function formatSubjectPreview(subjects) {
  if (!subjects?.length) return "No data yet";
  if (subjects.length <= 2) return subjects.join(", ");
  return `${subjects.slice(0, 2).join(", ")} +${subjects.length - 2} more`;
}

async function fetchWeekPlan(weekStart) {
  const data = await authJson(`/api/planner/plan/week?week_start=${weekStart}`);
  return data?.plan || [];
}

async function loadWeekSchedule() {
  isScheduleLoading.value = true;
  scheduleError.value = "";

  try {
    weekPlanSlots.value = await fetchWeekPlan(selectedWeekStartKey.value);
  } catch (error) {
    weekPlanSlots.value = [];
    scheduleError.value = error?.message || "Cannot load generated schedule.";
  } finally {
    isScheduleLoading.value = false;
  }
}

function getMonthWeekStarts(baseDate) {
  const year = baseDate.getFullYear();
  const month = baseDate.getMonth();
  const monthStart = new Date(year, month, 1);
  const monthEnd = new Date(year, month + 1, 0);

  const starts = [];
  const cursor = getStartOfWeekMonday(monthStart);

  while (cursor <= monthEnd) {
    starts.push(formatDate(cursor));
    cursor.setDate(cursor.getDate() + 7);
  }

  return [...new Set(starts)];
}

function getPreviousWeekStartKey() {
  const previousWeek = new Date(selectedWeekStart.value);
  previousWeek.setDate(previousWeek.getDate() - 7);
  return formatDate(previousWeek);
}

function getPreviousMonthWeekStarts(baseDate) {
  const previousMonthDate = new Date(
    baseDate.getFullYear(),
    baseDate.getMonth() - 1,
    1
  );

  return getMonthWeekStarts(previousMonthDate);
}

function isSameMonth(dateValue, baseDate) {
  const d = new Date(dateValue);
  return (
    d.getFullYear() === baseDate.getFullYear() &&
    d.getMonth() === baseDate.getMonth()
  );
}

async function loadChartSchedule() {
  try {
    if (chartFilter.value === "This month") {
      const currentMonthDate = selectedDateObject.value;
      const previousMonthDate = new Date(
        currentMonthDate.getFullYear(),
        currentMonthDate.getMonth() - 1,
        1
      );

      const currentWeekStarts = getMonthWeekStarts(currentMonthDate);
      const previousWeekStarts = getPreviousMonthWeekStarts(currentMonthDate);

      const [currentResults, previousResults] = await Promise.all([
        Promise.all(currentWeekStarts.map((weekStart) => fetchWeekPlan(weekStart))),
        Promise.all(previousWeekStarts.map((weekStart) => fetchWeekPlan(weekStart))),
      ]);

      chartPlanSlots.value = currentResults
        .flat()
        .filter((slot) => isSameMonth(slot.start, currentMonthDate));

      previousChartPlanSlots.value = previousResults
        .flat()
        .filter((slot) => isSameMonth(slot.start, previousMonthDate));

      return;
    }

    const previousWeekStartKey = getPreviousWeekStartKey();

    const [currentWeekPlan, previousWeekPlan] = await Promise.all([
      fetchWeekPlan(selectedWeekStartKey.value),
      fetchWeekPlan(previousWeekStartKey),
    ]);

    chartPlanSlots.value = currentWeekPlan;
    previousChartPlanSlots.value = previousWeekPlan;
  } catch (error) {
    chartPlanSlots.value = [];
    previousChartPlanSlots.value = [];
    console.error("Cannot load chart schedule:", error);
  }
}

watch(
  selectedWeekStartKey,
  () => {
    loadWeekSchedule();
    loadChartSchedule();
  },
  { immediate: true }
);

watch(
  () => route.query.date,
  () => {
    loadChartSchedule();
  }
);

const todaySchedule = computed(() => {
  return weekPlanSlots.value
    .filter((slot) => getSlotDate(slot) === selectedDate.value)
    .sort((a, b) => getSlotStartMinutes(a) - getSlotStartMinutes(b))
    .map((slot) => ({
      subject: slot.subject_name || "Subject",
      time: formatTimeRange(slot.start, slot.end),
      type: "Practice",
    }));
});


const todayLabel = computed(() => {
  const d = selectedDateObject.value;
  return d.toLocaleDateString("en-GB", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  });
});

const chartData = computed(() => {
  if (chartFilter.value === "This month") {
    const year = selectedDateObject.value.getFullYear();
    const month = selectedDateObject.value.getMonth();
    const lastDay = new Date(year, month + 1, 0).getDate();

    return Array.from({ length: lastDay }, (_, index) => {
      const dayDate = new Date(year, month, index + 1);
      const key = formatDate(dayDate);
      const slots = chartPlanSlots.value.filter((slot) => getSlotDate(slot) === key);
      const subjects = [...new Set(slots.map((slot) => slot.subject_name).filter(Boolean))];
      const hours = slots.reduce((sum, slot) => sum + slotDurationHours(slot), 0);

      return {
        day: key,
        short: String(index + 1).padStart(2, "0"),
        label: dayDate.toLocaleDateString("en-US", { weekday: "long" }),
        hours,
        subjects,
      };
    });
  }

  const labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  const start = new Date(selectedWeekStart.value);

  return Array.from({ length: 7 }, (_, index) => {
    const d = new Date(start);
    d.setDate(start.getDate() + index);
    const key = formatDate(d);
    const slots = chartPlanSlots.value.filter((slot) => getSlotDate(slot) === key);
    const subjects = [...new Set(slots.map((slot) => slot.subject_name).filter(Boolean))];
    const hours = slots.reduce((sum, slot) => sum + slotDurationHours(slot), 0);

    return {
      day: labels[index],
      short: labels[index],
      label: labels[index],
      hours,
      subjects,
    };
  });
});

function getPlanStats(slots) {
  const totalHours = slots.reduce((sum, slot) => sum + slotDurationHours(slot), 0);
  const subjectCount = new Set(
    slots.map((slot) => slot.subject_name).filter(Boolean)
  ).size;

  return {
    totalHours,
    subjectCount,
  };
}

function formatTrend(current, previous) {
  if (previous === 0 && current === 0) {
    return "No change";
  }

  if (previous === 0 && current > 0) {
    return "100%";
  }

  const percent = ((current - previous) / previous) * 100;
  const rounded = Math.round(percent * 10) / 10;

  if (rounded === 0) {
    return "No change";
  }

  return `${Math.abs(rounded)}%`;
}

function getTrendDirection(current, previous) {
  if (current > previous) return "up";
  if (current < previous) return "down";
  return "same";
}

function getTrendClass(current, previous) {
  if (current > previous) return "bg-emerald-50 text-emerald-600";
  if (current < previous) return "bg-red-50 text-red-600";
  return "bg-gray-100 text-gray-600";
}

const summary = computed(() => {
  const currentStats = getPlanStats(chartPlanSlots.value);
  const previousStats = getPlanStats(previousChartPlanSlots.value);

  const currentHours = Math.round(currentStats.totalHours * 10) / 10;
  const previousHours = Math.round(previousStats.totalHours * 10) / 10;

  const subjectLabel =
    currentStats.subjectCount > 0
      ? `${currentStats.subjectCount} ${
          currentStats.subjectCount === 1 ? "subject" : "subjects"
        }`
      : "No data yet";

  return {
    studyTime: currentStats.totalHours
      ? formatHours(currentStats.totalHours)
      : "No data yet",

    studyTimeTrend: formatTrend(currentHours, previousHours),
    studyTimeTrendDirection: getTrendDirection(currentHours, previousHours),
    studyTimeTrendClass: getTrendClass(currentHours, previousHours),

    subjects: subjectLabel,

    subjectTrend: formatTrend(
      currentStats.subjectCount,
      previousStats.subjectCount
    ),
    subjectTrendDirection: getTrendDirection(
      currentStats.subjectCount,
      previousStats.subjectCount
    ),
    subjectTrendClass: getTrendClass(
      currentStats.subjectCount,
      previousStats.subjectCount
    ),
  };
});

/* ===== AREA CHART LAYOUT ===== */
const chartWidth = 760;
const chartHeight = 430;
const chartPaddingTop = 40;
const chartPaddingRight = 36;
const chartPaddingBottom = 56;
const chartPaddingLeft = 60;

const chartMaxY = computed(() => {
  const maxHours = Math.max(...chartData.value.map((item) => item.hours), 0);
  return Math.max(12, Math.ceil(maxHours));
});

const innerWidth = computed(() => chartWidth - chartPaddingLeft - chartPaddingRight);
const innerHeight = computed(() => chartHeight - chartPaddingTop - chartPaddingBottom);

const xStep = computed(() => {
  if (chartData.value.length <= 1) return innerWidth.value;
  return innerWidth.value / (chartData.value.length - 1);
});

const chartPoints = computed(() => {
  return chartData.value.map((item, index) => {
    const x = chartPaddingLeft + index * xStep.value;
    const y =
      chartPaddingTop +
      innerHeight.value -
      (item.hours / chartMaxY.value) * innerHeight.value;

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

function handlePlannerPlanUpdated() {
  loadWeekSchedule();
  loadChartSchedule();
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

const yTicks = computed(() => Array.from({ length: 7 }, (_, i) => {
  const step = chartMaxY.value / 6;
  return Math.round((chartMaxY.value - i * step) * 10) / 10;
}));

const hoveredPoint = computed(() => {
  const targetDay = hoveredBar.value || activeChartDay.value;
  return chartPoints.value.find(item => item.day === targetDay) || chartPoints.value[0] || null;
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
            {{ summary.studyTime }}
          </p>
          <span
            class="rounded-full text-sm px-3 py-1 font-medium inline-flex items-center gap-1"
            :class="summary.studyTimeTrendClass"
          >
            <img
              v-if="summary.studyTimeTrendDirection === 'up'"
              :src="CalendarDays"
              alt="increase"
              class="w-3 h-3"
            />

            <img
              v-else-if="summary.studyTimeTrendDirection === 'down'"
              :src="ArrowDown"
              alt="decrease"
              class="w-3 h-3"
            />

            {{ summary.studyTimeTrend }}
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
            {{ summary.subjects }}
          </p>
          <span
            class="rounded-full text-sm px-3 py-1 font-medium inline-flex items-center gap-1"
            :class="summary.subjectTrendClass"
          >
            <img
              v-if="summary.subjectTrendDirection === 'up'"
              :src="CalendarDays"
              alt="increase"
              class="w-3 h-3"
            />

            <img
              v-else-if="summary.subjectTrendDirection === 'down'"
              :src="ArrowDown"
              alt="decrease"
              class="w-3 h-3"
            />

            {{ summary.subjectTrend }}
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
              @click="goToAiContentExtractor"
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

              <g>
                <line
                  v-for="tick in yTicks"
                  :key="tick"
                  :x1="chartPaddingLeft"
                  :x2="chartWidth - chartPaddingRight"
                  :y1="chartPaddingTop + ((chartMaxY - tick) / chartMaxY) * innerHeight"
                  :y2="chartPaddingTop + ((chartMaxY - tick) / chartMaxY) * innerHeight"
                  stroke="#d9d9d9"
                  stroke-dasharray="3 4"
                  stroke-width="1"
                />
              </g>

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
                  :y="chartPaddingTop + ((chartMaxY - tick) / chartMaxY) * innerHeight + 5"
                  text-anchor="end"
                  fill="#171717"
                  font-size="12"
                >
                  {{ tick }}
                </text>
              </g>

              <path :d="areaPath" fill="url(#studyAreaFill)" />

              <path
                :d="linePath"
                fill="none"
                stroke="#6d28ff"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />

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

              <circle
                v-if="hoveredPoint"
                :cx="hoveredPoint.x"
                :cy="hoveredPoint.y"
                r="6"
                fill="#6d28ff"
                stroke="#ffffff"
                stroke-width="2"
              />

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
                    {{ hoveredPoint.label || hoveredPoint.day }}
                  </div>

                  <div class="mt-3 text-[14px] leading-6 text-[#171717]">
                    <div>Study time: {{ Math.round(hoveredPoint.hours * 10) / 10 }} hours</div>
                    <div>
                      Subjects:
                      {{ formatSubjectPreview(hoveredPoint.subjects) }}
                    </div>
                  </div>

                  <div
                    class="absolute left-1/2 top-full h-4 w-4 -translate-x-1/2 -translate-y-1/2 rotate-45 border-b border-r border-[#d9d9d9] bg-white"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="scheduleError" class="mt-5 text-sm text-red-500">
            {{ scheduleError }}
          </div>
        </div>
      </div>

      <div class="rounded-3xl bg-white p-6 shadow-sm border border-gray-100">
        <div class="mb-6">
          <h3 class="text-xl font-semibold">Today's study schedule</h3>
          <p class="text-sm text-gray-500 mt-1">{{ todayLabel }}</p>
        </div>

        <div v-if="isScheduleLoading" class="h-[320px] flex items-center justify-center text-gray-500">
          Loading generated schedule...
        </div>

        <div v-else-if="todaySchedule.length" class="space-y-4 max-h-[420px] overflow-y-auto pr-1">
          <div
            v-for="(item, index) in todaySchedule"
            :key="index"
            class="rounded-2xl p-5 border"
            :class="
              index % 2 === 0
                ? 'bg-[#5C01D5]/[0.04] border-[#5C01D5]/10'
                : 'bg-[#6460F4]/[0.04] border-[#6460F4]/10'
            "
          >
            <div class="pb-2 border-b border-black">
              <h4 class="font-bold text-gray-900 text-xl">
                {{ item.subject }}
              </h4>
            </div>

            <div class="pt-3 space-y-2 text-sm text-gray-700">
              <p>Time: {{ item.time }}</p>
              <div class="flex items-center gap-2">
                <span>Type:</span>
                <span class="px-3 py-1 rounded-full bg-violet-600 text-white text-xm font-medium">
                  {{ item.type }}
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
          <p class="text-sm mt-1">Apply scheduler to show subjects for the selected day.</p>
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

      <div v-if="documentHistory.length" class="overflow-x-auto pb-2">
        <div class="flex gap-6 min-w-max">
          <div
            v-for="(doc, index) in documentHistory"
            :key="doc.id"
            class="w-[280px] rounded-2xl p-3 flex flex-col justify-between h-[170px] overflow-hidden font-inter text-left"
            :class="
              index % 2 === 0
                ? 'bg-[#5c01d51a] text-[#404040]'
                : 'bg-[#6460f41a] text-[#404040]'
            "
          >
            <div class="flex flex-col gap-2">
              <div class="text-base font-medium leading-6 line-clamp-2">
                {{ doc.title || doc.material_title }}
              </div>

              <div class="text-sm opacity-80">
                {{ new Date(doc.created_at).toLocaleString() }}
              </div>
            </div>

            <button
              @click="goToConversation(doc.id)"
              class="mt-3 self-start rounded-lg bg-[#171717] text-white px-3 py-1.5 text-sm font-medium hover:bg-black/80 transition cursor-pointer"
            >
              View details
            </button>
          </div>

          <div
            @click="openUploadPicker"
            class="w-[280px] rounded-2xl border border-dashed border-gray-300 p-4 h-[170px] flex flex-col items-center justify-center text-center text-[#404040] cursor-pointer hover:bg-gray-50 transition"
          >
            <img :src="Document" class="w-15 h-15 mb-3 opacity-30" />
            <p class="text-sm font-medium">
              {{ isUploadingDocument ? 'Uploading...' : 'Add new document' }}
            </p>
          </div>
        </div>
      </div>

      <div
        v-else
        class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6"
      >
        <div
          @click="openUploadPicker"
          class="rounded-2xl border border-dashed border-gray-300 p-4 min-h-[170px] flex flex-col items-center justify-center text-center text-[#404040] cursor-pointer hover:bg-gray-50 transition"
        >
          <img :src="Document" alt="add icon" class="w-15 h-15 mb-3 opacity-30" />
          <p class="text-sm font-medium">{{ isUploadingDocument ? 'Uploading...' : 'Add new document' }}</p>
        </div>
      </div>
    </div>
  </div>
  <input
    ref="uploadInputRef"
    type="file"
    class="hidden"
    accept=".pdf,.txt,.docx,.md"
    @change="handleDashboardFileUpload"
  />
</template>
