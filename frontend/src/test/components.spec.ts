import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "../App.vue";
import ClaimQueue from "../components/ClaimQueue.vue";
import HumanReviewModal from "../components/HumanReviewModal.vue";
import RagAssistant from "../components/RagAssistant.vue";
import TriagePanel from "../components/TriagePanel.vue";
import { demoClaims } from "../demoData";

describe("ClaimQueue", () => {
  it("filters claims by customer name and emits selected claim", async () => {
    const wrapper = mount(ClaimQueue, {
      props: {
        claims: demoClaims,
        selectedClaimNumber: demoClaims[0].claimNumber,
      },
    });

    await wrapper.find('[aria-label="Search claims"]').setValue("Marta");

    expect(wrapper.text()).toContain("Marta Keller");
    expect(wrapper.text()).not.toContain("Jonas Weber");

    await wrapper.find('[data-test="claim-row"]').trigger("click");

    expect(wrapper.emitted("select")?.[0]).toEqual([demoClaims[0].claimNumber]);
  });
});

describe("App selection", () => {
  it("updates the detail workspace when a queue claim is selected", async () => {
    const wrapper = mount(App);

    await wrapper.find('[aria-label="Search claims"]').setValue("Jonas");
    await wrapper.find('[data-test="claim-row"]').trigger("click");

    expect(wrapper.text()).toContain("CLM-20260626-000219");
    expect(wrapper.text()).toContain("Jonas Weber");
    expect(wrapper.text()).toContain("Property water damage");
  });
});

describe("TriagePanel", () => {
  it("renders triage labels and reason codes", () => {
    const wrapper = mount(TriagePanel, {
      props: {
        triage: demoClaims[0].triage,
      },
    });

    expect(wrapper.text()).toContain("HIGH");
    expect(wrapper.text()).toContain("MEDIUM");
    expect(wrapper.text()).toContain("POLICE_REPORT_MISSING");
    expect(wrapper.text()).toContain("Human review required");
  });
});

describe("RagAssistant", () => {
  it("renders grounded answer sources", () => {
    const wrapper = mount(RagAssistant, {
      props: {
        rag: demoClaims[0].rag,
      },
    });

    expect(wrapper.text()).toContain("Based on the retrieved policy coverage section");
    expect(wrapper.text()).toContain("DOC-POLICY-001-CHUNK-0001");
  });
});

describe("HumanReviewModal", () => {
  it("captures action and reason before submitting review", async () => {
    const wrapper = mount(HumanReviewModal, {
      props: {
        claimNumber: demoClaims[0].claimNumber,
      },
    });

    await wrapper.find("select").setValue("REQUEST_DOCUMENTS");
    await wrapper.find("textarea").setValue("Need police report before coverage review.");
    await wrapper.find("form").trigger("submit.prevent");

    expect(wrapper.emitted("submit")?.[0]).toEqual([
      {
        action: "REQUEST_DOCUMENTS",
        reason: "Need police report before coverage review.",
      },
    ]);
  });
});
