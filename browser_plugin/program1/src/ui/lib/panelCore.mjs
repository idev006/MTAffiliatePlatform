// Framework-free panel logic: process view mapping, worker id tagging, status text.
// No chrome/DOM access — importable from Vue components and from node:test directly.

export const DEFAULT_TARGET_URL = "https://shopee.co.th/search?keyword=ssd";
export const DEFAULT_DELAY_MIN_SECONDS = 30;
export const DEFAULT_DELAY_MAX_SECONDS = 120;
export const DEFAULT_PAGE_LOAD_WAIT_SECONDS = 4;
export const DEFAULT_PAGE_RETRY_WAIT_SECONDS = 5;
export const DEFAULT_MAX_PAGE_RETRIES = 2;
export const MIN_DELAY_SECONDS = 0;
export const MAX_DELAY_SECONDS = 600;
export const MIN_PAGE_WAIT_SECONDS = 1;
export const MAX_PAGE_WAIT_SECONDS = 60;
export const MIN_PAGE_RETRIES = 0;
export const MAX_PAGE_RETRIES = 5;

export function boundedInteger(value, defaultValue, minValue, maxValue) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  const safe = Number.isFinite(parsed) ? parsed : defaultValue;
  return Math.min(maxValue, Math.max(minValue, safe));
}

export function withWorkerId(observations, workerIdValue) {
  const sourceWorkerId = String(workerIdValue || "").trim();
  if (!sourceWorkerId) return observations;
  return observations.map((observation) => ({
    ...observation,
    source_worker_id: sourceWorkerId,
  }));
}

export function captureStatus(captureResponse, queueResponse) {
  const acceptedObservationCount = queueResponse?.flush?.accepted_observation_count || 0;
  return {
    ok: Boolean(queueResponse?.ok),
    capture: {
      profile: captureResponse?.profile || null,
      observation_count: captureResponse?.observations?.length || 0,
    },
    queue: {
      queued: Boolean(queueResponse?.queued),
      queued_observation_count: queueResponse?.queued_observation_count || 0,
      sent_count: queueResponse?.flush?.sent_count || 0,
      accepted_observation_count: acceptedObservationCount,
      remaining_count: queueResponse?.flush?.remaining_count || 0,
      error: queueResponse?.flush?.error || queueResponse?.error || null,
    },
  };
}

export function createIndicators({
  autoRunCount = 0,
  sessionAcceptedTotal = 0,
  sessionStartedAt = null,
  acceptedDelta = 0,
  now = Date.now(),
}) {
  const startedAt = sessionStartedAt === null ? now : sessionStartedAt;
  const total = sessionAcceptedTotal + acceptedDelta;
  const elapsedHours = Math.max((now - startedAt) / 3600000, 1 / 3600);
  return {
    cycle_count: autoRunCount,
    session_accepted_count: total,
    rate_per_hour: Math.round(total / elapsedHours),
    last_event: new Date(now).toLocaleTimeString(),
  };
}

export function processViewFromCapture(captureResponse, queueResponse, indicators) {
  const summary = captureStatus(captureResponse, queueResponse);
  const error = summary.queue.error;
  return {
    state: summary.ok ? "DELIVERED" : "DELIVERY_BLOCKED",
    step: summary.ok
      ? "Captured, queued and delivered to Back Office"
      : "Captured and queued locally; delivery is blocked",
    captured_count: summary.capture.observation_count,
    queued_count: summary.queue.queued_observation_count,
    sent_count: summary.queue.sent_count,
    accepted_count: summary.queue.accepted_observation_count,
    outbox_count: summary.queue.remaining_count,
    error,
    ...indicators,
  };
}

export function processViewFromStatus(response, indicators) {
  return {
    state: response?.state || "ERROR",
    step: response?.backend_configured
      ? "Ready to capture the active Shopee page"
      : "Configure Backend URL before delivery",
    captured_count: 0,
    queued_count: 0,
    sent_count: 0,
    accepted_count: 0,
    outbox_count: response?.outbox_remaining_count || 0,
    error: response?.ok ? null : response?.error || "STATUS_UNAVAILABLE",
    ...indicators,
  };
}

const BLOCKED_STATES = [
  "CONFIG_REQUIRED",
  "DELIVERY_BLOCKED",
  "PAGE_UNSUPPORTED",
  "PAGE_BLOCKED_BY_ANTIBOT",
  "ERROR",
];
const READY_STATES = ["IDLE", "READY", "DELIVERED"];

// Semantic tone per worker process state. Views map the tone onto their own
// styling vocabulary (daisyUI badges, tailwind colors, ...).
export function stateTone(value) {
  if (READY_STATES.includes(value)) return "success";
  if (value === "RECOVERABLE") return "warning";
  if (["COLLECTING", "QUEUED"].includes(value)) return "info";
  if (BLOCKED_STATES.includes(value)) return "error";
  return "idle";
}

export function registryStatusText(response) {
  if (!response) return "Registry: unknown";
  if (response.ok && response.registered) {
    return `Registry: registered (${response.worker_id})`;
  }
  return `Registry: not registered${response.error ? ` - ${response.error}` : ""}`;
}

export function humanPageText(pagination) {
  if (!pagination) return "";
  const current = pagination.current_page === null ? "" : `page ${pagination.current_page + 1}`;
  const total = pagination.total_pages === null ? "" : ` of ${pagination.total_pages}`;
  return `${current}${total}`;
}
