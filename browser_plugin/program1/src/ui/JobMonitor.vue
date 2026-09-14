<script setup>
import { ref, onMounted } from "vue";
import { jobPresentation, readJobPage } from "./jobMonitor.mjs";

const items = ref([]), total = ref(0), offset = ref(0), loading = ref(false), error = ref("");
function time(value) { return value ? new Date(value).toLocaleString("th-TH") : "ยังไม่มีข้อมูล"; }
async function load(next = offset.value) {
  loading.value = true; error.value = "";
  try {
    const page = await readJobPage(next);
    items.value = page.items; total.value = page.total; offset.value = page.offset;
  } catch (failure) {
    error.value = `อ่านสถานะงานไม่ได้ (${failure.message}) ยังยืนยันสถานะล่าสุดไม่ได้ การอ่านนี้ไม่ได้เปลี่ยนงาน กรุณาลองอ่านใหม่`;
  } finally { loading.value = false; }
}
onMounted(() => load());
</script>

<template>
  <section aria-label="ติดตามงานค้นหาสินค้า" class="space-y-3 border-b border-base-300 pb-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div><h2 class="text-xl font-bold">ติดตามงานค้นหาสินค้า</h2><p class="text-sm">สถานะที่ Back Office บันทึกไว้ · กดอ่านล่าสุดเพื่อตรวจความคืบหน้า</p></div>
      <button class="btn btn-sm btn-outline" :disabled="loading" @click="load()">อ่านสถานะงานล่าสุด</button>
    </div>
    <p v-if="loading" role="status">กำลังอ่านงานจาก Back Office…</p>
    <div v-else-if="error" role="alert" class="alert alert-error"><span>{{ error }}</span><button class="btn btn-sm" @click="load()">อ่านสถานะใหม่</button></div>
    <template v-else>
      <p role="status" class="text-sm">{{ total }} งานค้นหาสินค้า · ไม่ใช่จำนวนสินค้าใหม่หรือรายการที่ส่งสำเร็จ</p>
      <p v-if="!items.length" class="p-4 border border-base-300 rounded-box">ไม่มีงานในหน้านี้ การเก็บหน้าปัจจุบันด้วยมืออาจไม่มีงานค้นหาที่ผูกไว้ <button v-if="offset" class="btn btn-sm" @click="load(0)">หน้าแรก</button></p>
      <div v-else class="max-w-full overflow-x-auto border border-base-300 rounded-box" tabindex="0" role="region" aria-label="ตารางงาน เลื่อนแนวนอนเพื่อดูทุกคอลัมน์">
        <table class="table table-zebra min-w-[900px]">
          <caption class="p-3 text-left text-xs">เลื่อนแนวนอนเพื่อดูทุกคอลัมน์ ↔ · เปิดรายละเอียดเพื่อตรวจจุดบันทึกล่าสุด</caption>
          <thead><tr><th scope="col">งาน</th><th scope="col">สถานะ / สิ่งที่รอ</th><th scope="col">Worker</th><th scope="col">อัปเดตเมื่อ</th><th scope="col">หลักฐานและข้อผิดพลาด</th></tr></thead>
          <tbody><tr v-for="job in items" :key="job.job_id">
            <td class="max-w-60 break-words whitespace-normal">{{ job.job_id }}</td>
            <td class="min-w-64 max-w-80 whitespace-normal"><p class="font-semibold">{{ jobPresentation(job.state).label }}</p><p class="text-sm">{{ jobPresentation(job.state).guidance }}</p></td>
            <td>{{ job.assigned_worker_id || "ยังไม่ได้มอบหมาย" }}</td>
            <td class="whitespace-nowrap">{{ time(job.updated_at) }}</td>
            <td><details class="min-w-64"><summary class="cursor-pointer link">ดูรายละเอียด</summary>
              <dl class="text-sm space-y-2 mt-2"><dt>สถานะระบบ / รุ่นข้อมูล</dt><dd>{{ job.state }} / {{ job.job_version }}</dd><dt>ข้อผิดพลาดที่บันทึก</dt><dd>{{ job.failure_code || "ไม่มีรหัสข้อผิดพลาดที่บันทึก" }} {{ job.failure_detail }}</dd><dt>จุดบันทึกล่าสุด</dt><dd v-if="job.checkpoint"><p>{{ time(job.checkpoint.created_at) }} · {{ job.checkpoint.checkpoint_type }}</p><pre class="max-w-96 overflow-x-auto">{{ JSON.stringify(job.checkpoint.payload, null, 2) }}</pre></dd><dd v-else>ยังไม่มี checkpoint ที่บันทึก</dd></dl>
            </details></td>
          </tr></tbody>
        </table>
      </div>
      <nav class="flex items-center gap-3" aria-label="หน้ารายการงาน"><button class="btn btn-sm" :disabled="offset === 0" @click="load(Math.max(0, offset - 20))">ก่อนหน้า</button><span>หน้า {{ Math.floor(offset / 20) + 1 }}</span><button class="btn btn-sm" :disabled="offset + 20 >= total" @click="load(offset + 20)">ถัดไป</button></nav>
    </template>
  </section>
</template>
