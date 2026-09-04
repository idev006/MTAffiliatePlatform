<script setup>
import { useProcessStore } from "../stores/process.js";

const process = useProcessStore();

function kindBadge(kind) {
  const classes = {
    process: "badge-info",
    registry: "badge-accent",
    payload: "badge-ghost",
  };
  return classes[kind] ?? "badge-ghost";
}
</script>

<template>
  <div class="space-y-3">
    <section class="card card-border bg-base-100 shadow-sm">
      <div class="card-body flex-row items-center justify-between gap-2 p-3">
        <div class="stat p-0">
          <p class="stat-title text-xs">Undelivered observations held locally</p>
          <p class="stat-value text-lg">
            {{ process.outboxCount }}<span class="text-xs font-normal text-base-content/60"> in outbox</span>
          </p>
        </div>
        <button id="flush" class="btn btn-outline btn-sm" @click="process.flushOutbox()">
          Flush Outbox
        </button>
      </div>
    </section>

    <section class="card card-border bg-base-100 shadow-sm">
      <div class="card-body gap-2 p-3">
      <h2 class="card-title text-xs uppercase tracking-wider text-base-content/60">
        Session activity
      </h2>
      <ul v-if="process.activity.length" class="list rounded-box bg-base-100">
        <li v-for="(entry, index) in [...process.activity].reverse()" :key="index" class="list-row px-0 py-1 text-xs">
          <span class="mr-1 font-mono text-[10px] text-base-content/50">{{ entry.at }}</span>
          <span class="badge badge-xs" :class="kindBadge(entry.kind)">{{ entry.kind }}</span>
          <span class="ml-1">{{ entry.text }}</span>
        </li>
      </ul>
      <p v-else class="text-xs text-base-content/50">No activity recorded this session.</p>
      </div>
    </section>
  </div>
</template>
