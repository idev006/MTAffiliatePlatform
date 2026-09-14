const states = {
  CREATED: ["เตรียมงาน", "งานถูกบันทึกแล้ว รอเข้าคิว"],
  QUEUED: ["รอ worker", "เปิด worker ที่รองรับงานและตรวจการเชื่อมต่อ Back Office"],
  LEASED: ["worker รับงานแล้ว", "รอ worker เริ่มเก็บข้อมูล"],
  IN_PROGRESS: ["กำลังทำงาน", "ตรวจ checkpoint ล่าสุดและสถานะ worker หากไม่มีความคืบหน้า"],
  PAUSED: ["หยุดชั่วคราว", "ตรวจ checkpoint ก่อนดำเนินงานต่อ ข้อมูลหน่วยงานที่ยังไม่จบอาจยังไม่ถูกบันทึก"],
  VERIFYING: ["กำลังตรวจผล", "รอ Back Office ยืนยันผล ไม่ต้องสร้างงานซ้ำ"],
  COMPLETED: ["งานเสร็จสิ้น", "ตรวจข้อมูลสินค้าที่บันทึกจริง จำนวนงานไม่ใช่จำนวนสินค้าใหม่"],
  FAILED: ["งานมีข้อผิดพลาด", "เปิดรายละเอียดข้อผิดพลาดและ checkpoint ก่อนตัดสินใจกู้คืน"],
  NEEDS_HUMAN: ["ต้องการให้ผู้ใช้ดำเนินการ", "ตรวจรายละเอียดและหน้าเว็บไซต์ตามปกติ ก่อนดำเนินงานต่อ"],
  CANCELLED: ["ยกเลิกงานแล้ว", "ตรวจข้อมูลที่บันทึกไว้ งานนี้จะไม่ดำเนินต่อ"],
};

export function jobPresentation(state) {
  const [label, guidance] = states[state] || ["ยังไม่รู้สถานะ", "อ่านข้อมูลล่าสุดหรือตรวจรายละเอียดกับผู้ดูแล"];
  return { label, guidance };
}

export async function readJobPage(offset = 0, fetcher = fetch) {
  const response = await fetcher(`/api/v1/program1/discovery-jobs?limit=20&offset=${offset}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}
