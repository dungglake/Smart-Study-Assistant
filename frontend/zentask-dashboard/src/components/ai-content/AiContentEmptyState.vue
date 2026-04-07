<script setup>
import { ref } from "vue";
import { DocumentUpload } from "@/icons";

const emit = defineEmits(["select-files", "files-selected"]);

const fileInput = ref(null);

const onFileChange = (event) => {
  const files = Array.from(event.target.files || []);
  emit("files-selected", files);
};

defineExpose({
  openFilePicker: () => {
    fileInput.value?.click();
  }
});
</script>

<template>
  <div
    class="w-full h-full relative rounded-3xl bg-white overflow-hidden flex flex-col items-start p-6 box-border gap-6 text-left text-lg text-gray-200 font-inter"
  >
    <div class="self-stretch flex items-center">
      <div class="flex-1 flex items-center gap-1.5">
        <div class="relative leading-7 font-semibold text-[#1f2937]">
          Add documents to convert
        </div>
      </div>
    </div>

    <div
      class="self-stretch flex-1 flex flex-col items-start gap-2 min-w-[96px] text-base text-darkslategray"
    >
      <div
        class="self-stretch flex-1 rounded-lg border border-dashed border-[#c7d2fe] overflow-hidden flex flex-col items-center justify-center p-4 min-h-[320px]"
      >
        <div
          class="w-full flex flex-col items-center py-3 px-4 box-border gap-3 max-w-full"
        >
          <div
            class="w-12 h-12 rounded-full bg-[#f5f5f5] flex items-center justify-center"
          >
            <img :src="DocumentUpload" alt="Document upload icon" class="w-6 h-6" />
          </div>

          <div class="flex items-center justify-center pt-2 text-center">
            <div class="relative leading-6 font-medium text-[#1f2937]">
              Drag and drop or select files to upload
            </div>
          </div>

          <div
            class="self-stretch flex items-center justify-center pt-1 text-center text-[#6b7280]"
          >
            <div class="flex-1 relative leading-6">
              Supported formats: PDF, .txt, Markdown, .docx
            </div>
          </div>

          <button
            type="button"
            class="mt-3 inline-flex items-center justify-center rounded-xl border border-[#d1d5db] bg-white px-4 py-2 text-sm font-medium text-[#111827] hover:bg-[#f9fafb] transition cursor-pointer"
            @click="$emit('select-files')"
          >
            Select files
          </button>

          <input
            ref="fileInput"
            type="file"
            class="hidden"
            multiple
            @change="onFileChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>