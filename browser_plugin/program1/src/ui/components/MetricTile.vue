<script setup>
defineProps({
  label: { type: String, required: true },
  valueId: { type: String, default: "" },
  value: { type: [String, Number], default: 0 },
});
</script>

<template>
  <div class="stat border-t border-base-300 px-3 py-2">
    <span class="stat-title text-[11px]">{{ label }}</span>
    <span :id="valueId || undefined" class="stat-value text-lg leading-tight">{{ value }}</span>
  </div>
</template>
