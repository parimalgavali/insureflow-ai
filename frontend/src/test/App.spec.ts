import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

import App from "../App.vue";
import { routes } from "../router";

async function mountAppAt(path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes,
  });
  router.push(path);
  await router.isReady();

  const wrapper = mount(App, {
    global: {
      plugins: [router],
    },
  });
  await flushPromises();

  return {
    router,
    wrapper,
  };
}

describe("App", () => {
  it("redirects the root route to the claim queue", async () => {
    const { router, wrapper } = await mountAppAt("/");

    expect(router.currentRoute.value.path).toBe("/claims");
    expect(wrapper.text()).toContain("Claim Queue");
    expect(wrapper.text()).toContain("CLM-20260626-000418");
  });

  it("renders the claim detail route with workbench widgets", async () => {
    const { wrapper } = await mountAppAt("/claims/CLM-20260626-000418");

    expect(wrapper.text()).toContain("Adjuster Workbench");
    expect(wrapper.text()).toContain("CLM-20260626-000418");
    expect(wrapper.text()).toContain("AI Triage");
    expect(wrapper.text()).toContain("RAG Assistant");
    expect(wrapper.text()).toContain("Human Review");
  });

  it("renders the route-backed human review page", async () => {
    const { wrapper } = await mountAppAt("/claims/CLM-20260626-000418/review");

    expect(wrapper.text()).toContain("Human Review");
    expect(wrapper.text()).toContain("CLM-20260626-000418");
    expect(wrapper.find("form").exists()).toBe(true);
  });

  it("records a human review from the route-backed review page", async () => {
    const { wrapper } = await mountAppAt("/claims/CLM-20260626-000418/review");

    await wrapper.find("select").setValue("ACCEPT_AI_RECOMMENDATION");
    await wrapper.find("textarea").setValue("Coverage and AI recommendation reviewed.");
    await wrapper.find("form").trigger("submit.prevent");
    await flushPromises();

    expect(wrapper.text()).toContain("Review History");
    expect(wrapper.text()).toContain("ACCEPT_AI_RECOMMENDATION");
    expect(wrapper.text()).toContain("Coverage and AI recommendation reviewed.");
  });

  it("exposes navigation for the main product pages", async () => {
    const { wrapper } = await mountAppAt("/claims");

    expect(wrapper.find('a[href="/claims"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/documents"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/governance"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/integrations"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/settings"]').exists()).toBe(true);
  });
});
