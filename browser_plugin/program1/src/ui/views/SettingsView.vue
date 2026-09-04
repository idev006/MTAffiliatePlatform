<script setup>
import { useSettingsStore } from "../stores/settings.js";
import DelayRangeSlider from "../components/DelayRangeSlider.vue";

const settings = useSettingsStore();

async function onSave() {
  await settings.save();
}
</script>

<template>
  <div class="space-y-3">
    <fieldset class="fieldset rounded-box border border-base-300 bg-base-100 p-3 shadow-sm">
      <legend class="fieldset-legend text-xs uppercase tracking-wider text-base-content/60">
        Connection &amp; Target
      </legend>
      <label class="fieldset-label" for="backendUrl">Backend URL</label>
      <input
        id="backendUrl"
        v-model="settings.backendUrl"
        class="input input-bordered input-sm w-full"
        type="text"
        placeholder="http://127.0.0.1:8000"
      />
      <label class="fieldset-label" for="workerId">Worker ID</label>
      <input
        id="workerId"
        v-model="settings.workerId"
        class="input input-bordered input-sm w-full"
        type="text"
        placeholder="worker-01"
      />
      <label class="fieldset-label" for="targetUrl">Target Page URL</label>
      <input
        id="targetUrl"
        v-model="settings.targetUrl"
        class="input input-bordered input-sm w-full"
        type="text"
        placeholder="https://shopee.co.th/search?keyword=..."
      />
      <label class="fieldset-label cursor-pointer justify-between gap-3 py-2">
        <span>Advance target page after delivery</span>
        <input
          id="advanceAfterDelivery"
          v-model="settings.advanceAfterDelivery"
          type="checkbox"
          class="toggle toggle-primary toggle-sm"
        />
      </label>
      <label class="fieldset-label cursor-pointer justify-between gap-3 py-2">
        <span>Resume auto-run when panel reopens</span>
        <input
          id="autoResume"
          v-model="settings.autoResume"
          type="checkbox"
          class="toggle toggle-primary toggle-sm"
        />
      </label>
    </fieldset>

    <section class="card card-border bg-base-100 shadow-sm">
      <div class="card-body gap-1 p-3">
      <h2 class="card-title text-xs uppercase tracking-wider text-base-content/60">
        Auto-cycle delay
      </h2>
      <p class="label label-text mb-2 text-xs text-base-content/60">
        Random delay range between pages (seconds)
      </p>
      <DelayRangeSlider />
      </div>
    </section>

    <fieldset class="fieldset rounded-box border border-base-300 bg-base-100 p-3 shadow-sm">
      <legend class="fieldset-legend text-xs uppercase tracking-wider text-base-content/60">
        Recovery
      </legend>
      <div class="grid grid-cols-3 gap-2">
        <label class="fieldset-label flex-col items-stretch gap-1">
          <span>Load wait</span>
          <input
            id="pageLoadWaitSeconds"
            v-model.number="settings.pageLoadWaitSeconds"
            class="input input-bordered input-sm"
            type="number"
            min="1"
            max="60"
          />
        </label>
        <label class="fieldset-label flex-col items-stretch gap-1">
          <span>Retry wait</span>
          <input
            id="pageRetryWaitSeconds"
            v-model.number="settings.pageRetryWaitSeconds"
            class="input input-bordered input-sm"
            type="number"
            min="1"
            max="60"
          />
        </label>
        <label class="fieldset-label flex-col items-stretch gap-1">
          <span>Retries</span>
          <input
            id="maxPageRetries"
            v-model.number="settings.maxPageRetries"
            class="input input-bordered input-sm"
            type="number"
            min="0"
            max="5"
          />
        </label>
      </div>
    </fieldset>

    <button id="save" class="btn btn-primary btn-sm w-full" @click="onSave">Save Settings</button>
  </div>
</template>
