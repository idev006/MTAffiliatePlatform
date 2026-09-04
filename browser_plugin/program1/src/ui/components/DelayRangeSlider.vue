<script setup>
import { computed } from "vue";
import { useSettingsStore } from "../stores/settings.js";
import {
  delayRangeGeometry,
  delayRangePreview,
  syncDelayRangeValues,
} from "../lib/delayRange.mjs";

const settings = useSettingsStore();

const previewText = computed(() => delayRangePreview(settings.delayRangeMs));
const trackStyle = computed(() => {
  const geometry = delayRangeGeometry(settings.delayRangeMs);
  return {
    "--delay-range-left": geometry.leftPercent,
    "--delay-range-width": geometry.widthPercent,
  };
});

function onThumbInput(event, thumb) {
  const synced = syncDelayRangeValues(
    event.target.value,
    thumb === "min" ? settings.delayMaxSeconds : settings.delayMinSeconds,
    thumb,
  );
  settings.delayMinSeconds = synced.min_seconds;
  settings.delayMaxSeconds = synced.max_seconds;
}
</script>

<template>
  <div class="form-control">
    <div class="label py-1">
      <span class="label-text text-xs">Random delay range</span>
      <span class="label-text-alt font-bold">
        <span id="delayRangeLabel">{{ settings.delayMinSeconds }} s</span>
        -
        <span id="delayMaxReadout">{{ settings.delayMaxSeconds }} s</span>
      </span>
    </div>
    <div class="program1-dual-range" :style="trackStyle">
      <input
        id="delayMinSeconds"
        class="range range-primary range-sm program1-dual-range__input"
        type="range"
        min="0"
        max="600"
        step="5"
        :value="settings.delayMinSeconds"
        aria-label="Minimum delay (seconds)"
        title="Minimum delay (seconds)"
        @input="onThumbInput($event, 'min')"
      />
      <input
        id="delayMaxSeconds"
        class="range range-primary range-sm program1-dual-range__input program1-dual-range__input--max"
        type="range"
        min="0"
        max="600"
        step="5"
        :value="settings.delayMaxSeconds"
        aria-label="Maximum delay (seconds)"
        title="Maximum delay (seconds)"
        @input="onThumbInput($event, 'max')"
      />
    </div>
    <p id="delayPreview" class="text-[11px] text-base-content/50">{{ previewText }}</p>
  </div>
</template>

<style scoped>
.program1-dual-range {
  position: relative;
  height: 1.75rem;
}

.program1-dual-range::before,
.program1-dual-range::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 0.75rem;
  height: 0.375rem;
  border-radius: 9999px;
  pointer-events: none;
}

.program1-dual-range::before {
  background: color-mix(in oklab, var(--color-primary) 12%, var(--color-base-200));
}

.program1-dual-range::after {
  left: var(--delay-range-left);
  right: auto;
  width: var(--delay-range-width);
  background: var(--color-primary);
}

.program1-dual-range__input {
  position: absolute;
  inset: 0;
  width: 100%;
  background: transparent;
}

.program1-dual-range__input--max {
  pointer-events: none;
}

.program1-dual-range__input--max::-webkit-slider-thumb {
  pointer-events: auto;
}

.program1-dual-range__input--max::-moz-range-thumb {
  pointer-events: auto;
}
</style>
