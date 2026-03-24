<script setup lang="ts">
import { Edit, DropDown } from '@/icons'
</script>

<template>
    <div class="flex w-full flex-col gap-6 bg-[#f5f5f5] p-8">
      <!-- Profile -->
      <section class="rounded-[24px] bg-white p-6">
        <h2 class="text-[18px] font-semibold text-[#171717]">Profile</h2>

        <div class="mt-6">
          <div class="relative h-[100px] w-[100px]">
            <img"
              alt="Profile"
              class="h-[100px] w-[100px] rounded-full object-cover"
            />

            <button
              type="button"
              class="absolute bottom-0 right-0 flex h-8 w-8 items-center justify-center rounded-full bg-[#5c01d5]"
            >
              <img :src="Edit" alt="Edit" class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div class="mt-6 flex max-w-[450px] flex-col gap-3">
          <div>
            <label class="mb-1 block text-[16px] font-medium text-[#404040]">Full Name</label>
            <input
              type="text"
              value="Cuongta"
              class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 text-[16px] text-[#171717] outline-none"
            />
          </div>

          <div>
            <label class="mb-1 block text-[16px] font-medium text-[#404040]">Email</label>
            <input
              type="email"
              value="demo.email@gmail.com"
              class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 text-[16px] text-[#171717] outline-none"
            />
          </div>

          <div>
            <label class="mb-1 block text-[16px] font-medium text-[#404040]">Password</label>
            <input
              type="password"
              placeholder="Enter Current Password"
              class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 text-[16px] text-[#171717] outline-none"
            />
          </div>

          <div>
            <input
              type="password"
              placeholder="Enter New Password"
              class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 text-[16px] text-[#171717] outline-none"
            />
          </div>

          <div>
            <input
              type="password"
              placeholder="Repeat New Password"
              class="h-11 w-full rounded-md border border-[#d4d4d4] px-3 text-[16px] text-[#171717] outline-none"
            />
          </div>
        </div>
      </section>

      <!-- Language & Region -->
      <section class="rounded-[24px] bg-white p-6">
        <h2 class="text-[18px] font-semibold text-[#171717]">Language & Region</h2>

        <div class="mt-6 flex max-w-[450px] flex-col gap-3">
          <div>
            <label class="mb-1 block text-[16px] font-medium text-[#404040]">Language</label>
            <div class="relative">
              <select
                class="h-11 w-full appearance-none rounded-md border border-[#d4d4d4] bg-white px-3 pr-10 text-[16px] text-[#171717] outline-none"
              >
                <option>English</option>
                <option>Vietnamese</option>
              </select>

              <img
                :src="DropDown"
                alt="Open"
                class="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2"
              />
            </div>
          </div>

          <div>
            <label class="mb-1 block text-[16px] font-medium text-[#404040]">Region</label>
            <div class="relative">
              <select
                class="h-11 w-full appearance-none rounded-md border border-[#d4d4d4] bg-white px-3 pr-10 text-[16px] text-[#171717] outline-none"
              >
                <option>Asia/Bangkok</option>
                <option>Asia/Ho_Chi_Minh</option>
                <option>UTC</option>
              </select>

              <img
                :src="DropDown"
                alt="Open"
                class="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2"
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  </template>