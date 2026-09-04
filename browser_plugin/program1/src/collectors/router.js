(function initProgram1CollectorRouter(global) {
  const ns = global.__mtaProgram1Collectors;
  if (!ns) throw new Error("PROGRAM1_COLLECTOR_CORE_REQUIRED");

  function buildPageContext() {
    let hostname = "";
    try { hostname = new URL(window.location.href).hostname; } catch (_error) {}
    return {
      url: window.location.href,
      hostname,
      surface: ns.inferShopeeSurfaceFromUrl(window.location.href),
      page_context: ns.readPageSurfaceContext(),
    };
  }

  function profileRef(profile) {
    return {
      profile_id: profile.profile_id,
      profile_version: profile.version,
      profile_evidence_stage: profile.evidence_stage,
      surface: profile.surface,
    };
  }

  function selectProfile({ minimumEvidenceStage = "LAB_VALIDATED" } = {}) {
    const ctx = buildPageContext();
    const matches = ns.profiles.filter((profile) => {
      try { return Boolean(profile.matches(ctx)); } catch (_error) { return false; }
    });
    if (!matches.length) {
      return { ok: false, error: "PAGE_UNSUPPORTED", context: ctx, matches: [] };
    }
    const allowed = matches.filter((profile) => ns.stageAtLeast(profile.evidence_stage, minimumEvidenceStage));
    if (!allowed.length) {
      return { ok: false, error: "PROFILE_NOT_ALLOWED_BY_EVIDENCE_STAGE", context: ctx, matches: matches.map(profileRef) };
    }
    allowed.sort((a, b) => (b.priority || 0) - (a.priority || 0) || a.profile_id.localeCompare(b.profile_id));
    const topPriority = allowed[0].priority || 0;
    const top = allowed.filter((profile) => (profile.priority || 0) === topPriority);
    if (top.length !== 1) {
      return { ok: false, error: "PROFILE_AMBIGUOUS", context: ctx, matches: top.map(profileRef) };
    }
    return { ok: true, profile: top[0], context: ctx };
  }

  function captureCurrentPage(options = {}) {
    const pageContext = ns.readPageSurfaceContext();
    if (ns.isPageBlockedByAntibot()) {
      return {
        ok: false,
        error: "PAGE_BLOCKED_BY_ANTIBOT",
        profile: null,
        profile_id: null,
        profile_version: null,
        profile_evidence_stage: null,
        surface: ns.inferShopeeSurfaceFromUrl(window.location.href),
        observations: [],
        page_context: pageContext,
        page_url: window.location.href,
      };
    }

    const selected = selectProfile(options);
    if (!selected.ok) {
      return {
        ok: false,
        error: selected.error,
        profile: null,
        profile_id: null,
        profile_version: null,
        profile_evidence_stage: null,
        surface: selected.context.surface,
        observations: [],
        pagination: ns.readPaginationInfo(),
        page_context: selected.context.page_context,
        page_url: window.location.href,
        profile_matches: selected.matches,
      };
    }

    const profile = selected.profile;
    const captured = profile.capture(selected.context) || {};
    const observations = Array.isArray(captured.observations) ? captured.observations : [];
    if (!observations.length) {
      return {
        ok: false,
        error: "PAGE_UNSUPPORTED",
        profile: profile.profile_id,
        ...profileRef(profile),
        observations: [],
        pagination: captured.pagination ?? ns.readPaginationInfo(),
        page_context: selected.context.page_context,
        page_url: window.location.href,
      };
    }
    return {
      ok: true,
      error: null,
      profile: profile.profile_id,
      ...profileRef(profile),
      observations,
      pagination: captured.pagination ?? null,
      page_context: selected.context.page_context,
      page_url: window.location.href,
    };
  }

  ns.buildPageContext = buildPageContext;
  ns.selectProfile = selectProfile;
  ns.captureCurrentPage = captureCurrentPage;
})(globalThis);