import { createWorkerBridge } from "./lib/workerBridge.mjs";

// Browser-context singleton. Node tests exercise createWorkerBridge directly with
// a fake chrome object instead of importing this module.
export const bridge = createWorkerBridge(globalThis.chrome);
