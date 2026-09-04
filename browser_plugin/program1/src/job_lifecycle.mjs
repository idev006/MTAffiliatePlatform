export function createProgram1JobLifecycle({
  postJson,
  getJson,
  loadState,
  saveState,
  now = () => new Date().toISOString(),
}) {
  async function activeState() {
    return (await loadState()) || null;
  }

  async function persist(next) {
    await saveState(next);
    return next;
  }

  async function leaseAndStart(workerId) {
    const existing = await activeState();
    if (existing && existing.job_id) {
      return { ok: true, leased: false, reason: "ACTIVE_JOB_EXISTS", active_job: existing };
    }

    const leased = await postJson("/api/v1/jobs/lease-next", { worker_id: workerId });
    if (!leased) {
      return { ok: true, leased: false, reason: "NO_COMPATIBLE_JOB", active_job: null };
    }

    const leasedState = await persist({
      job_id: leased.job_id,
      job_type: leased.job_type,
      payload_ref: leased.payload_ref,
      lease_token: leased.lease_token,
      lease_until: leased.lease_until,
      state: leased.state,
      work_package: null,
      last_checkpoint: null,
      last_error: null,
      updated_at: now(),
    });

    try {
      const workPackage = await getJson(
        `/api/v1/program1/discovery-jobs/${encodeURIComponent(leased.job_id)}/work-package`,
      );
      const started = await postJson(
        `/api/v1/jobs/${encodeURIComponent(leased.job_id)}/start`,
        { worker_id: workerId, lease_token: leased.lease_token },
      );
      const startedState = await persist({
        ...leasedState,
        lease_token: started.lease_token,
        lease_until: started.lease_until,
        state: started.state,
        work_package: workPackage,
        last_error: null,
        updated_at: now(),
      });
      return { ok: true, leased: true, active_job: startedState };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failedState = await persist({
        ...leasedState,
        last_error: message,
        updated_at: now(),
      });
      return { ok: false, leased: true, error: message, active_job: failedState };
    }
  }

  async function renew(workerId) {
    const current = await activeState();
    if (!current?.job_id) {
      return { ok: true, renewed: false, reason: "NO_ACTIVE_JOB", active_job: null };
    }
    try {
      const renewed = await postJson(
        `/api/v1/jobs/${encodeURIComponent(current.job_id)}/renew`,
        { worker_id: workerId, lease_token: current.lease_token },
      );
      const next = await persist({
        ...current,
        lease_token: renewed.lease_token,
        lease_until: renewed.lease_until,
        state: renewed.state,
        last_error: null,
        updated_at: now(),
      });
      return { ok: true, renewed: true, active_job: next };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const next = await persist({ ...current, last_error: message, updated_at: now() });
      return { ok: false, renewed: false, error: message, active_job: next };
    }
  }

  async function checkpoint(workerId, checkpointType, payload = {}) {
    const current = await activeState();
    if (!current?.job_id) {
      throw new Error("NO_ACTIVE_JOB");
    }
    const updated = await postJson(
      `/api/v1/jobs/${encodeURIComponent(current.job_id)}/checkpoint`,
      {
        worker_id: workerId,
        lease_token: current.lease_token,
        checkpoint_type: checkpointType,
        payload,
      },
    );
    const next = await persist({
      ...current,
      lease_token: updated.lease_token,
      lease_until: updated.lease_until,
      state: updated.state,
      last_checkpoint: {
        checkpoint_type: checkpointType,
        payload,
        created_at: now(),
      },
      last_error: null,
      updated_at: now(),
    });
    return { ok: true, active_job: next };
  }

  async function verifyAndComplete(workerId) {
    const current = await activeState();
    if (!current?.job_id) {
      throw new Error("NO_ACTIVE_JOB");
    }
    const verifying = await postJson(
      `/api/v1/jobs/${encodeURIComponent(current.job_id)}/verify`,
      { worker_id: workerId, lease_token: current.lease_token },
    );
    await persist({
      ...current,
      lease_token: verifying.lease_token,
      lease_until: verifying.lease_until,
      state: verifying.state,
      last_error: null,
      updated_at: now(),
    });
    const completed = await postJson(
      `/api/v1/jobs/${encodeURIComponent(current.job_id)}/complete`,
      { worker_id: workerId, lease_token: verifying.lease_token },
    );
    await persist(null);
    return { ok: true, completed_job: completed, active_job: null };
  }

  async function reconcile(workerId) {
    const current = await activeState();
    if (!current?.job_id) {
      return { ok: true, reconciled: false, reason: "NO_ACTIVE_JOB", active_job: null };
    }
    try {
      const authoritative = await getJson(
        `/api/v1/jobs/${encodeURIComponent(current.job_id)}`,
      );
      if (["COMPLETED", "FAILED", "NEEDS_HUMAN", "CANCELLED", "SKIPPED_DUPLICATE"].includes(
        authoritative.state,
      )) {
        await persist(null);
        return {
          ok: true,
          reconciled: true,
          terminal: true,
          authoritative_job: authoritative,
          active_job: null,
        };
      }
      if (!["LEASED", "IN_PROGRESS", "VERIFYING"].includes(authoritative.state)) {
        const next = await persist({
          ...current,
          state: authoritative.state,
          last_error: `RECONCILIATION_REQUIRED_${authoritative.state}`,
          updated_at: now(),
        });
        return {
          ok: false,
          reconciled: true,
          terminal: false,
          error: next.last_error,
          authoritative_job: authoritative,
          active_job: next,
        };
      }
      return renew(workerId);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const next = await persist({ ...current, last_error: message, updated_at: now() });
      return { ok: false, reconciled: false, error: message, active_job: next };
    }
  }

  return {
    activeState,
    leaseAndStart,
    renew,
    checkpoint,
    verifyAndComplete,
    reconcile,
  };
}
