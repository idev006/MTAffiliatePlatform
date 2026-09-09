<script setup>
import { ref, onMounted, nextTick } from "vue";

const items = ref([]), total = ref(0), offset = ref(0), loading = ref(false), error = ref("");
const selected = ref(null), history = ref([]), historyError = ref(""), historyLoading = ref(false);
const historySection = ref(null);
const limit = 20;
let historyRequest = 0;
function safeLink(value) {
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : null; }
  catch { return null; }
}
function shown(value) { return value == null ? "ยังไม่มีข้อมูล" : value; }
function time(value) { return value ? new Date(value).toLocaleString("th-TH") : "ยังไม่มีข้อมูล"; }
async function read(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
async function load(next = offset.value) {
  loading.value = true; error.value = ""; selected.value = null; historyRequest++;
  try {
    const result = await read(`/api/v1/program1/products?limit=${limit}&offset=${next}`);
    items.value = result.items; total.value = result.total; offset.value = next;
  } catch (failure) { error.value = `อ่านข้อมูลไม่ได้ (${failure.message}) กรุณาลองใหม่`; }
  finally { loading.value = false; }
}
async function inspect(item) {
  selected.value = item; history.value = []; historyError.value = ""; historyLoading.value = true;
  const request = ++historyRequest;
  await nextTick();
  historySection.value?.scrollIntoView({ block: "start" });
  try {
    const key = [item.platform, item.shop_id, item.item_id].map(encodeURIComponent).join("/");
    const result = await read(`/api/v1/program1/products/${key}/observations?limit=100`);
    if (request === historyRequest) history.value = result;
  } catch (failure) { if (request === historyRequest) historyError.value = `อ่านประวัติไม่ได้ (${failure.message})`; }
  finally { if (request === historyRequest) historyLoading.value = false; }
}
onMounted(() => load());
</script>

<template>
  <main class="mx-auto max-w-7xl space-y-5 p-4 sm:p-6">
    <header class="flex flex-wrap items-start justify-between gap-3">
      <div><p class="text-sm text-base-content/60">Program 1 · Back Office</p><h1 class="text-2xl font-bold">ตรวจข้อมูลสินค้า</h1><p class="mt-1 text-sm">ข้อมูลล่าสุดที่บันทึกจริง พร้อมประวัติและแหล่งที่มา</p></div>
      <button class="btn btn-outline btn-sm" :disabled="loading" @click="load()">อ่านข้อมูลล่าสุด</button>
    </header>
    <p class="text-sm text-base-content/70">หนึ่งแถวต่อรหัสสินค้าที่ระบบบันทึกไว้ ภาพเป็น URL อ้างอิงเท่านั้น ยังไม่ได้ดาวน์โหลดไฟล์หรือยืนยันสิทธิ์ใช้งาน</p>
    <p v-if="loading" role="status" class="flex items-center gap-2"><span class="loading loading-spinner loading-sm"></span>กำลังอ่านข้อมูลจาก Back Office</p>
    <div v-else-if="error" role="alert" class="alert alert-error"><span>{{ error }}</span><button class="btn btn-sm" @click="load()">ลองใหม่</button></div>
    <template v-else>
      <p role="status" class="text-sm">มี {{ total }} รหัสสินค้าในข้อมูลที่บันทึก</p>
      <p v-if="!items.length" class="rounded-box border border-base-300 p-6">ไม่มีรายการในหน้านี้ ให้เก็บข้อมูลผ่าน worker หรือกลับไปหน้าแรก <button v-if="offset" class="btn btn-sm" @click="load(0)">หน้าแรก</button></p>
      <div v-else class="max-w-full overflow-x-auto rounded-box border border-base-300 focus-visible:outline-2 focus-visible:outline-primary" tabindex="0" role="region" aria-label="ตารางสินค้า เลื่อนแนวนอนเพื่อดูทุกคอลัมน์">
        <table class="table table-zebra min-w-[960px]">
          <caption class="p-3 text-left text-xs">เลื่อนแนวนอนเพื่อดูทุกคอลัมน์ ↔ · เลือกประวัติเพื่อตรวจ observations</caption>
          <thead><tr><th scope="col">สินค้า / รหัส</th><th scope="col">ราคาที่บันทึก</th><th scope="col">คะแนนที่บันทึก</th><th scope="col">ภาพหลัก</th><th scope="col">เก็บเมื่อ</th><th scope="col">ตรวจสอบ</th></tr></thead>
          <tbody><tr v-for="item in items" :key="item.observation_id">
            <td class="min-w-64 max-w-96 whitespace-normal break-words"><p class="font-semibold">{{ item.product_name }}</p><p class="text-xs text-base-content/60">{{ item.platform }} / {{ item.shop_id }} / {{ item.item_id }}</p><a v-if="safeLink(item.product_url)" :href="safeLink(item.product_url)" class="link text-xs" target="_blank" rel="noopener noreferrer">เปิดแหล่งสินค้า ↗</a></td>
            <td>{{ shown(item.price_current) }}</td><td>{{ shown(item.rating) }}</td>
            <td><a v-if="safeLink(item.primary_image_url)" :href="safeLink(item.primary_image_url)" class="link" target="_blank" rel="noopener noreferrer">เปิดภาพอ้างอิง ↗</a><span v-else class="text-base-content/60">ยังไม่มีภาพอ้างอิง</span></td>
            <td class="whitespace-nowrap">{{ time(item.collected_at) }}</td><td><button class="btn btn-sm btn-outline" @click="inspect(item)">ประวัติ</button></td>
          </tr></tbody>
        </table>
      </div>
      <nav class="flex items-center gap-3" aria-label="หน้าข้อมูลสินค้า"><button class="btn btn-sm" :disabled="offset === 0" @click="load(Math.max(0, offset-limit))">ก่อนหน้า</button><span class="text-sm">หน้า {{ Math.floor(offset/limit)+1 }}</span><button class="btn btn-sm" :disabled="offset+limit >= total" @click="load(offset+limit)">ถัดไป</button></nav>
    </template>
    <section ref="historySection" v-if="selected && !loading && !error" class="space-y-3 rounded-box border border-base-300 p-4" aria-label="ประวัติสินค้า">
      <h2 class="text-lg font-semibold">ประวัติ: {{ selected.product_name }}</h2>
      <p class="text-xs text-base-content/60">สูงสุด 100 observations ล่าสุด เรียงใหม่ไปเก่า ไม่ใช่จำนวนสินค้าใหม่</p>
      <p v-if="historyLoading" role="status">กำลังอ่านประวัติ…</p>
      <div v-else-if="historyError" role="alert" class="alert alert-error">{{ historyError }}<button class="btn btn-sm" @click="inspect(selected)">ลองใหม่</button></div>
      <div v-else class="max-w-full overflow-x-auto" tabindex="0" role="region" aria-label="ตารางประวัติ เลื่อนแนวนอน">
        <table class="table min-w-[800px]"><thead><tr><th>Observation</th><th>เก็บเมื่อ</th><th>Worker / งานต้นทาง</th><th>ภาพอ้างอิง</th></tr></thead><tbody><tr v-for="row in history" :key="row.observation_id"><td>{{ row.observation_id }}</td><td>{{ time(row.collected_at) }}</td><td>{{ shown(row.source_worker_id) }} / {{ shown(row.source_job_id) }}</td><td><a v-if="safeLink(row.primary_image_url)" class="link" :href="safeLink(row.primary_image_url)" target="_blank" rel="noopener noreferrer">เปิดภาพ ↗</a><span v-else>ยังไม่มีภาพอ้างอิง</span></td></tr></tbody></table>
        <p v-if="!history.length">ไม่พบประวัติ</p>
      </div>
    </section>
  </main>
</template>
