<script setup>
import { onMounted } from "vue";
import { useProcessStore } from "./stores/process.js";

const process = useProcessStore();

onMounted(() => {
  void process.init();
});
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header class="navbar sticky top-0 z-10 min-h-0 flex-col items-stretch border-b border-base-300 bg-base-100/95 p-0 backdrop-blur">
      <div class="flex items-center justify-between gap-2 px-3 pt-3">
        <h1 class="text-sm font-bold tracking-wide">Program 1 Worker</h1>
        <span
          id="registryStatus"
          class="badge badge-outline badge-sm max-w-40 truncate font-normal"
          :title="process.registryText"
        >
          {{ process.registryText }}
        </span>
      </div>
      <nav class="tabs tabs-border px-2 pt-2">
        <RouterLink
          to="/status"
          class="tab tab-sm font-semibold"
          active-class="tab-active"
          inactive-class=""
        >
          Status
        </RouterLink>
        <RouterLink
          to="/settings"
          class="tab tab-sm font-semibold"
          active-class="tab-active"
          inactive-class=""
        >
          Settings
        </RouterLink>
        <RouterLink
          to="/activity"
          class="tab tab-sm font-semibold"
          active-class="tab-active"
          inactive-class=""
        >
          Activity
        </RouterLink>
      </nav>
    </header>

    <main class="flex-1 px-3 py-3">
      <RouterView />
    </main>
  </div>
</template>
