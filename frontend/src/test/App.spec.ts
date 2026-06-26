import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "../App.vue";

describe("App", () => {
  it("opens directly to the adjuster workbench", () => {
    const wrapper = mount(App);

    expect(wrapper.text()).toContain("Claim Queue");
    expect(wrapper.text()).toContain("CLM-20260626-000418");
    expect(wrapper.text()).toContain("AI Triage");
    expect(wrapper.text()).toContain("RAG Assistant");
    expect(wrapper.text()).toContain("Human Review");
  });
});
