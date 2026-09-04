// Framework-free random-delay range logic: normalization, random pick, dual-thumb
// geometry and ordering enforcement. No chrome/DOM.

import {
  DEFAULT_DELAY_MAX_SECONDS,
  DEFAULT_DELAY_MIN_SECONDS,
  MAX_DELAY_SECONDS,
  MIN_DELAY_SECONDS,
} from "./panelCore.mjs";

export function boundedDelaySeconds(value, defaultValue) {
  const seconds = Number.parseInt(String(value ?? ""), 10);
  const safeSeconds = Number.isFinite(seconds) ? seconds : defaultValue;
  return Math.min(MAX_DELAY_SECONDS, Math.max(MIN_DELAY_SECONDS, safeSeconds));
}

export function normalizedDelayRangeMs(minValue, maxValue) {
  const first = boundedDelaySeconds(minValue, DEFAULT_DELAY_MIN_SECONDS);
  const second = boundedDelaySeconds(maxValue, DEFAULT_DELAY_MAX_SECONDS);
  const minSeconds = Math.min(first, second);
  const maxSeconds = Math.max(first, second);
  return {
    min_seconds: minSeconds,
    max_seconds: maxSeconds,
    min_ms: minSeconds * 1000,
    max_ms: maxSeconds * 1000,
  };
}

export function randomDelayMs(range, randomSource = Math.random) {
  const minMs = Math.min(range.min_ms, range.max_ms);
  const maxMs = Math.max(range.min_ms, range.max_ms);
  if (minMs === maxMs) return minMs;
  return Math.floor(minMs + randomSource() * (maxMs - minMs + 1));
}

export function delayRangeGeometry(range, limitSeconds = MAX_DELAY_SECONDS) {
  const minPercent = (range.min_seconds / limitSeconds) * 100;
  const widthPercent = ((range.max_seconds - range.min_seconds) / limitSeconds) * 100;
  return {
    leftPercent: `${Math.max(0, Math.min(100, minPercent))}%`,
    widthPercent: `${Math.max(0, Math.min(100, widthPercent))}%`,
  };
}

// Enforce min <= max when one thumb crosses the other while dragging.
export function syncDelayRangeValues(minValueRaw, maxValueRaw, updatedThumb) {
  let min = Number.parseInt(String(minValueRaw), 10);
  let max = Number.parseInt(String(maxValueRaw), 10);
  if (!Number.isFinite(min)) min = DEFAULT_DELAY_MIN_SECONDS;
  if (!Number.isFinite(max)) max = DEFAULT_DELAY_MAX_SECONDS;
  if (updatedThumb === "min" && min > max) max = min;
  if (updatedThumb === "max" && max < min) min = max;
  return { min_seconds: min, max_seconds: max };
}

export function delayRangeLabel(range) {
  return `Random from ${range.min_seconds} to ${range.max_seconds} s`;
}

export function delayRangePreview(range) {
  return `Next cycle delay: random ${range.min_seconds}-${range.max_seconds} s`;
}
