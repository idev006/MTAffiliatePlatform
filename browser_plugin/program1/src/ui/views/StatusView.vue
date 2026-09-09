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
    <section class="card card-border bg-base-100 shadow-sm" aria-labelledby="receiptHeading">
      <div class="card-body gap-2 p-3">
        <div class="flex items-center justify-between gap-2">
          <h2 id="receiptHeading" class="text-sm font-semibold">ใบรับข้อมูลล่าสุดจาก Back Office</h2>
          <button class="btn btn-ghost btn-xs" @click="process.refreshStatus()">อ่านผลล่าสุด</button>
        </div>
        <template v-if="process.lastDeliveryReceipt">
          <span class="badge badge-success badge-sm">ส่งสำเร็จและได้รับใบรับ</span>
          <div class="metric-scroll" tabindex="0" role="region" aria-label="ใบรับข้อมูล เลื่อนแนวนอนเพื่อดูทุกคอลัมน์">
          <div class="stats rounded-none shadow-none" aria-live="polite">
            <MetricTile label="บันทึก observation ใหม่" value-id="receiptAccepted"
              :value="process.lastDeliveryReceipt.accepted_count" />
            <MetricTile label="observation ซ้ำตรงกัน" value-id="receiptDuplicate"
              :value="process.lastDeliveryReceipt.duplicate_count" />
            <MetricTile label="ยืนยันข้อมูลครบ" value-id="receiptAccounted"
              :value="process.lastDeliveryReceipt.accounted_count" />
            <MetricTile label="รายการที่ส่งในชุดนี้" value-id="receiptReceived"
              :value="process.lastDeliveryReceipt.received_count" />
          </div>
          </div>
          <p class="text-xs text-base-content/60">เลื่อนแนวนอนเพื่อดูทุกคอลัมน์ ↔</p>
          <p class="text-xs text-base-content/70">
            เป็นผลการบันทึกครั้งแรกของชุดข้อมูลนี้ การส่งซ้ำใช้ใบรับเดิม
            รายการใหม่อาจเป็นข้อมูลครั้งใหม่ของสินค้าเดิม จึงยังใช้ระบุจำนวนสินค้าใหม่ไม่ได้
          </p>
          <details class="text-xs">
            <summary class="cursor-pointer">รายละเอียดใบรับ</summary>
            <p class="break-all">ชุดข้อมูล: {{ process.lastDeliveryReceipt.batch_id }}</p>
            <p>ได้รับเมื่อ: {{ process.lastDeliveryReceipt.acknowledged_at }}</p>
          </details>
        </template>
        <p v-else class="text-xs text-base-content/70">ยังไม่มีใบรับที่ยืนยันสำหรับ Back Office นี้</p>
        <p v-if="process.outboxCount" class="text-xs text-warning">
          ยังมี {{ process.outboxCount }} ชุดรอส่ง ข้อมูลอยู่ในคิวของ worker
        </p>
      </div>
    </section>
    <section class="card card-border bg-base-100 shadow-sm">
      <div class="card-title flex items-center justify-between px-3 py-2 text-sm">
        <h2 class="text-xs font-bold uppercase tracking-wider text-base-content/60">Process telemetry</h2>
        <span id="state" class="badge badge-sm font-bold" :class="toneClass">{{ process.state }}</span>
      </div>
      <div class="metric-scroll" tabindex="0" role="region" aria-label="Process telemetry เลื่อนแนวนอนเพื่อดูทุกคอลัมน์">
      <div class="stats rounded-none shadow-none">
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
      </div>
      <p class="px-3 py-1 text-xs text-base-content/60">เลื่อนแนวนอนเพื่อดูทุกคอลัมน์ ↔</p>
      <div class="space-y-1 border-t border-base-300 px-3 py-2 text-xs">
        <p id="lastEvent" class="text-base-content/60">Last event: {{ process.lastEvent }}</p>
        <p id="step" class="break-words">{{ process.displayStep }}</p>
        <p v-if="process.lastError" id="lastError" class="break-words text-error">{{ process.lastError }}</p>
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
