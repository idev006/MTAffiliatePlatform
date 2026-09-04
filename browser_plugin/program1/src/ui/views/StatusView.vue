<script setup>
import { computed } from "vue";
import { useProcessStore } from "../stores/process.js";
import { stateTone } from "../lib/panelCore.mjs";
import MetricTile from "../components/MetricTile.vue";

const process = useProcessStore();

const toneClass = computed(() => {
  const classes = {
    success: "badge-success",
    info: "badge-info",
    warning: "badge-warning",
    error: "badge-error",
    idle: "badge-ghost",
  };
  return classes[stateTone(process.state)] ?? "badge-ghost";
});
</script>

<template>
  <div class="space-y-3">
    <section class="card card-border bg-base-100 shadow-sm">
      <div class="card-title flex items-center justify-between px-3 py-2 text-sm">
        <h2 class="text-xs font-bold uppercase tracking-wider text-base-content/60">Process</h2>
        <span id="state" class="badge badge-sm font-bold" :class="toneClass">{{ process.state }}</span>
      </div>
      <div class="stats grid grid-cols-2 rounded-none shadow-none">
        <MetricTile label="Captured Obs" value-id="capturedCount" :value="process.capturedCount" />
        <MetricTile label="Accepted Obs" value-id="acceptedCount" :value="process.acceptedCount" />
        <MetricTile label="Queued Obs" value-id="queuedCount" :value="process.queuedCount" />
        <MetricTile label="Delivered Batches" value-id="sentCount" :value="process.sentCount" />
        <MetricTile label="Outbox" value-id="outboxCount" :value="process.outboxCount" />
        <MetricTile label="Cycle" value-id="cycleCount" :value="process.cycleCount" />
        <MetricTile
          label="Session Accepted"
          value-id="sessionAcceptedCount"
          :value="process.sessionAcceptedCount"
        />
        <MetricTile label="Rate Obs/Hr" value-id="ratePerHour" :value="process.ratePerHour" />
      </div>
      <div class="space-y-1 border-t border-base-300 px-3 py-2 text-xs">
        <p id="lastEvent" class="text-base-content/60">Last event: {{ process.lastEvent }}</p>
        <p id="step">{{ process.displayStep }}</p>
        <p v-if="process.lastError" id="lastError" class="text-error">{{ process.lastError }}</p>
      </div>
    </section>

    <section class="card card-border bg-base-100 shadow-sm">
      <div class="card-body gap-2 p-3">
      <div class="join w-full">
        <button id="openTarget" class="btn btn-outline btn-sm flex-1" @click="process.openTargetPage()">
          Open Target Page
        </button>
        <button id="capture" class="btn btn-outline btn-sm flex-1" @click="process.manualCapture()">
          Capture Current Page
        </button>
      </div>
      <div class="join w-full">
        <button
          id="startAuto"
          class="btn btn-primary btn-sm flex-1"
          :disabled="process.autoRunning"
          @click="process.startAutoRun()"
        >
          Start Auto Run
        </button>
        <button
          id="stopAuto"
          class="btn btn-error btn-outline btn-sm flex-1"
          :disabled="!process.autoRunning"
          @click="process.stopAutoRun()"
        >
          Stop Auto Run
        </button>
      </div>
      <div
        v-if="process.autoRunning"
        class="alert alert-info p-2 text-xs"
      >
        Auto run is active — the worker captures the target listing page by page until the last page
        or Stop is pressed.
      </div>
      </div>
    </section>

    <details class="collapse collapse-arrow border border-base-300 bg-base-100 shadow-sm">
      <summary class="collapse-title min-h-0 px-3 py-2 text-xs font-semibold text-base-content/70">
        Last result payload
      </summary>
      <pre id="status" class="collapse-content max-h-64 overflow-auto whitespace-pre-wrap px-3 pb-3 text-[10px] leading-snug">{{
        process.lastPayloadText || "No payload yet"
      }}</pre>
    </details>
  </div>
</template>
