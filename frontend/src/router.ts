import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import ClaimDetailPage from "./pages/ClaimDetailPage.vue";
import ClaimsPage from "./pages/ClaimsPage.vue";
import DocumentsPage from "./pages/DocumentsPage.vue";
import GovernancePage from "./pages/GovernancePage.vue";
import HumanReviewPage from "./pages/HumanReviewPage.vue";
import IntegrationsPage from "./pages/IntegrationsPage.vue";
import SettingsPage from "./pages/SettingsPage.vue";

export const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/claims",
  },
  {
    path: "/claims",
    component: ClaimsPage,
  },
  {
    path: "/claims/:claimNumber",
    component: ClaimDetailPage,
  },
  {
    path: "/claims/:claimNumber/review",
    component: HumanReviewPage,
  },
  {
    path: "/documents",
    component: DocumentsPage,
  },
  {
    path: "/governance",
    component: GovernancePage,
  },
  {
    path: "/integrations",
    component: IntegrationsPage,
  },
  {
    path: "/settings",
    component: SettingsPage,
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
