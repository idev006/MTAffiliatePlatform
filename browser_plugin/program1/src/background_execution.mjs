function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function normalizedTarget(workPackage, settings, runState) {
  const targets = workPackage?.discovery_plan?.collection_targets || [];
  const candidate =
    runState?.current_target_url ||
    targets[0] ||
    settings?.target_url ||
    "";
  const value = String(candidate || "").trim();
  if (!value) throw new Error("DISCOVERY_TARGET_REQUIRED");
  const url = new URL(value);
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error("DISCOVERY_TARGET_NOT_WEB_URL");
  }
  return url.toString();
}

export function createBackgroundExecutionController({
  lifecycle,
  getSettings,
  loadRunState,
  saveRunState,
  ensurePermission,
  getTab,
  createTab,
  focusTab,
  navigateTab,
  injectCollector,
  captureTab,
  deliverBatch,
  scheduleWake,
  cancelWake,
  randomDelayMs,
  randomUUID,
  now = () => Date.now(),
}) {
  async function persist(patch) {
    const current = (await loadRunState()) || {};
    const next = {
      ...current,
      ...patch,
      updated_at: new Date(now()).toISOString(),
    };
    await saveRunState(next);
    return next;
  }

  async function stop(reason, { error = null, terminal = false } = {}) {
    await cancelWake();
    return persist({
      desired: false,
      in_flight: false,
      next_run_at: null,
      last_step: reason,
      last_error: error,
      terminal,
    });
  }

  async function ensureJob(workerId) {
    let active = await lifecycle.activeState();
    if (active?.job_id) return active;
    const leased = await lifecycle.leaseAndStart(workerId);
    if (!leased.ok) throw new Error(leased.error || "JOB_LEASE_FAILED");
    if (!leased.leased) return null;
    return leased.active_job;
  }

  async function ensureTargetTab(targetUrl, runState) {
    const permitted = await ensurePermission(targetUrl);
    if (!permitted) throw new Error("PAGE_PERMISSION_REQUIRED");

    if (runState?.active_target_tab_id != null) {
      try {
        const tab = await getTab(runState.active_target_tab_id);
        if (tab?.id != null) {
          if (tab.url !== targetUrl) {
            await navigateTab(tab.id, targetUrl);
            return { tab_id: tab.id, url: targetUrl, needs_wait: true };
          }
          await focusTab(tab.id);
          return {
            tab_id: tab.id,
            url: targetUrl,
            needs_wait: tab.status === "loading",
          };
        }
      } catch (_error) {
        // Fall through to a fresh controlled tab.
      }
    }
    const tab = await createTab(targetUrl);
    if (tab?.id == null) throw new Error("TARGET_TAB_CREATE_FAILED");
    return { tab_id: tab.id, url: targetUrl, needs_wait: true };
  }

  async function scheduleNext(settings, runState) {
    const minSeconds = Math.max(
      0,
      Number.parseInt(String(settings?.delay_min_seconds ?? 30), 10) || 0,
    );
    const maxSeconds = Math.max(
      minSeconds,
      Number.parseInt(String(settings?.delay_max_seconds ?? 120), 10) || minSeconds,
    );
    const delayMs = randomDelayMs(minSeconds * 1000, maxSeconds * 1000);
    const when = now() + delayMs;
    await scheduleWake(when);
    return persist({
      ...runState,
      desired: true,
      in_flight: false,
      next_run_at: new Date(when).toISOString(),
      last_step: `Next background cycle scheduled in ${Math.ceil(delayMs / 1000)}s`,
      last_error: null,
    });
  }

  async function start() {
    const settings = await getSettings();
    if (!settings?.backend_url) {
      throw new Error("BACKEND_URL_NOT_CONFIGURED");
    }
    if (!settings?.worker_id) {
      throw new Error("WORKER_ID_NOT_CONFIGURED");
    }
    const active = await ensureJob(settings.worker_id);
    if (!active) {
      return stop("No compatible discovery job available");
    }
    const target = normalizedTarget(active.work_package, settings, await loadRunState());
    const state = await persist({
      desired: true,
      terminal: false,
      current_target_url: target,
      last_error: null,
      last_step: "Background run starting",
    });
    await scheduleWake(now());
    return { ok: true, active_job: active, run_state: state };
  }

  async function runOneCycle() {
    const settings = await getSettings();
    const current = (await loadRunState()) || {};
    if (!current.desired) {
      return { ok: true, skipped: true, reason: "RUN_NOT_DESIRED" };
    }
    if (current.in_flight) {
      return { ok: true, skipped: true, reason: "CYCLE_ALREADY_IN_FLIGHT" };
    }
    if (!settings?.worker_id || !settings?.backend_url) {
      const stopped = await stop("Background run stopped: worker not configured", {
        error: "WORKER_NOT_CONFIGURED",
      });
      return { ok: false, run_state: stopped, error: "WORKER_NOT_CONFIGURED" };
    }

    await persist({
      in_flight: true,
      cycle_count: (current.cycle_count || 0) + 1,
      last_step: "Reconciling active discovery job",
      last_error: null,
    });

    try {
      const reconciled = await lifecycle.reconcile(settings.worker_id);
      if (!reconciled.ok && reconciled.reason !== "NO_ACTIVE_JOB") {
        throw new Error(reconciled.error || "JOB_RECONCILIATION_FAILED");
      }
      const active = await ensureJob(settings.worker_id);
      if (!active) {
        const stopped = await stop("Background run finished: no compatible job");
        return { ok: true, completed: true, run_state: stopped };
      }

      const beforeTarget = await loadRunState();
      const targetUrl = normalizedTarget(active.work_package, settings, beforeTarget);
      const tab = await ensureTargetTab(targetUrl, beforeTarget);
      await persist({
        active_target_tab_id: tab.tab_id,
        current_target_url: targetUrl,
        last_step: `Collecting ${targetUrl}`,
      });

      const loadWaitMs =
        Math.max(
          1,
          Number.parseInt(String(settings?.page_load_wait_seconds ?? 4), 10) || 4,
        ) * 1000;
      if (tab.needs_wait) {
        const when = now() + loadWaitMs;
        await scheduleWake(when);
        const waiting = await persist({
          in_flight: false,
          next_run_at: new Date(when).toISOString(),
          last_step: "Waiting for target page to load",
          last_error: null,
        });
        return { ok: true, waiting: true, run_state: waiting };
      }

      await injectCollector(tab.tab_id);
      const capture = await captureTab(tab.tab_id);
      if (!capture?.ok) {
        const failure = capture?.error || "COLLECTION_FAILED";
        const maxRetries = Math.max(
          0,
          Number.parseInt(String(settings?.max_page_retries ?? 2), 10) || 0,
        );
        const retryAttempt = current.page_retry_attempt || 0;
        if (
          failure === "PAGE_UNSUPPORTED" &&
          capture?.page_context?.listing_shell_present &&
          retryAttempt < maxRetries
        ) {
          const retryWaitMs =
            Math.max(
              1,
              Number.parseInt(
                String(settings?.page_retry_wait_seconds ?? 5),
                10,
              ) || 5,
            ) * 1000;
          const when = now() + retryWaitMs;
          await scheduleWake(when);
          const retrying = await persist({
            in_flight: false,
            page_retry_attempt: retryAttempt + 1,
            next_run_at: new Date(when).toISOString(),
            last_step: `Page not ready; retry ${retryAttempt + 1}/${maxRetries}`,
            last_error: null,
          });
          return { ok: true, retrying: true, capture, run_state: retrying };
        }
        const stopped = await stop(
          `Background run stopped: ${failure}`,
          { error: failure },
        );
        return { ok: false, error: failure, capture, run_state: stopped };
      }

      const observations = (capture.observations || []).map((observation) => ({
        ...observation,
        source_worker_id: settings.worker_id,
        source_job_id: active.job_id,
      }));
      const batchId = randomUUID();
      const delivery = await deliverBatch({
        batch_id: batchId,
        observations,
        job_id: active.job_id,
        worker_id: settings.worker_id,
        lease_token: active.lease_token,
      });
      if (!delivery?.ok) {
        const stopped = await stop("Background run paused: delivery blocked", {
          error: delivery?.error || delivery?.flush?.error || "DELIVERY_BLOCKED",
        });
        return { ok: false, delivery, run_state: stopped };
      }

      await lifecycle.checkpoint(
        settings.worker_id,
        "OBSERVATION_BATCH_ACK",
        {
          batch_id: batchId,
          received_count: observations.length,
          accepted_count: delivery?.flush?.accepted_observation_count ?? observations.length,
          page_url: capture.page_url || targetUrl,
          pagination: capture.pagination || null,
        },
      );

      await persist({ page_retry_attempt: 0 });
      const stateAfterAck = await loadRunState();
      const nextCycleCount = stateAfterAck?.cycle_count || 0;
      const nextAccepted =
        (stateAfterAck?.session_accepted_count || 0) +
        (delivery?.flush?.accepted_observation_count || 0);

      if (capture.pagination?.has_next === false) {
        const completed = await lifecycle.verifyAndComplete(settings.worker_id);
        const stopped = await stop(
          "Background run completed: reached last page",
          { terminal: true },
        );
        await persist({
          cycle_count: nextCycleCount,
          session_accepted_count: nextAccepted,
          last_completed_job_id: completed?.completed_job?.job_id || active.job_id,
        });
        return {
          ok: true,
          completed: true,
          active_job: null,
          delivery,
          capture,
          run_state: stopped,
        };
      }

      const nextUrl = capture.pagination?.next_url;
      if (!nextUrl) {
        const stopped = await stop("Background run stopped: next page is ambiguous", {
          error: "PAGINATION_NEXT_URL_MISSING",
        });
        return { ok: false, error: "PAGINATION_NEXT_URL_MISSING", run_state: stopped };
      }

      await navigateTab(tab.tab_id, nextUrl);
      const afterAdvance = await persist({
        current_target_url: nextUrl,
        active_target_tab_id: tab.tab_id,
        cycle_count: nextCycleCount,
        session_accepted_count: nextAccepted,
        last_step: `Advanced to next page: ${nextUrl}`,
        last_error: null,
      });
      const scheduled = await scheduleNext(settings, afterAdvance);
      return { ok: true, completed: false, capture, delivery, run_state: scheduled };
    } catch (error) {
      const message = errorMessage(error);
      const stopped = await stop(`Background run stopped: ${message}`, { error: message });
      return { ok: false, error: message, run_state: stopped };
    }
  }

  async function resumeAfterWake() {
    const current = (await loadRunState()) || {};
    if (!current.desired) return { ok: true, skipped: true, reason: "RUN_NOT_DESIRED" };
    return runOneCycle();
  }

  return {
    start,
    stop,
    runOneCycle,
    resumeAfterWake,
  };
}
