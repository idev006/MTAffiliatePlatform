import { createRouter, createWebHashHistory } from "vue-router";
import StatusView from "./views/StatusView.vue";
import SettingsView from "./views/SettingsView.vue";
import ActivityView from "./views/ActivityView.vue";

// Hash history: the panel loads as a static extension page (chrome-extension://…/dist/sidepanel.html)
// with no server-side routes, so path history is not available.
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/status" },
    { path: "/status", name: "status", component: StatusView },
    { path: "/settings", name: "settings", component: SettingsView },
    { path: "/activity", name: "activity", component: ActivityView },
  ],
});
