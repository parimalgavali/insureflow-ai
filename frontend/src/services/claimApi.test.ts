import { describe, expect, it, vi } from "vitest";

import { createClaimApi, type BackendClaimTriageResponse } from "./claimApi";
import { toClaimDetail, toTimelineEvents, toTriageSnapshot } from "./claimMapper";
import { createClaimRepository } from "./claimRepository";

const backendClaim = {
  claimNumber: "CLM-LIVE-1",
  policyNumber: "POL-LIVE-1",
  customerNumber: "CUST-LIVE-1",
  claimType: "AUTO_COLLISION",
  status: "UNDER_REVIEW",
  lossDate: "2026-06-24",
  reportedAt: "2026-06-26T10:15:30Z",
  lossLocation: "Columbus, OH",
  description: "Rear-end collision with repair estimate.",
  estimatedLossAmount: 9000,
  coverageValidation: {
    covered: true,
    policyStatus: "ACTIVE",
    coverageType: "COLLISION",
    limitAmount: 25000,
    deductibleAmount: 500,
    exclusions: "[]",
    reasons: ["Coverage active on loss date"],
    warnings: [],
  },
};

const backendEvent = {
  eventType: "FNOL_SUBMITTED",
  eventSource: "Backend",
  description: "Claim submitted through FNOL intake.",
  payload: {},
  createdAt: "2026-06-26T10:15:30Z",
};

const backendTriage: BackendClaimTriageResponse = {
  claimNumber: "CLM-LIVE-1",
  modelName: "rule-based-triage",
  modelVersion: "1.0.0",
  severityScore: 0.91,
  severityLabel: "HIGH",
  fraudRiskScore: 0.48,
  fraudRiskLabel: "MEDIUM",
  litigationRiskScore: 0.2,
  litigationRiskLabel: "LOW",
  recommendedQueue: "Senior motor adjuster",
  reasonCodes: ["HIGH_DAMAGE_AMOUNT"],
  humanReviewRequired: true,
  explanation: "High damage amount requires senior review.",
  createdAt: "2026-06-26T10:16:30Z",
};

describe("claim API client", () => {
  it("bootstraps a dev token and sends bearer auth on live requests", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ token: "dev-token" }))
      .mockResolvedValueOnce(jsonResponse([backendClaim]));
    const api = createClaimApi({ baseUrl: "/api/v1", fetchImpl: fetchMock });

    const claims = await api.fetchClaimSummaries();

    expect(claims).toHaveLength(1);
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/v1/auth/dev-token",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/claims",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer dev-token" }),
      }),
    );
  });
});

describe("claim mapper", () => {
  it("maps backend claim, event, and triage DTOs into the workbench view model", () => {
    const claim = toClaimDetail({
      claim: backendClaim,
      events: [backendEvent],
      triage: backendTriage,
    });

    expect(claim.claimNumber).toBe("CLM-LIVE-1");
    expect(claim.priority).toBe("HIGH");
    expect(claim.customer.name).toBe("CUST-LIVE-1");
    expect(claim.policy.coverageStatus).toBe("Collision covered");
    expect(claim.estimatedLoss).toBe("9,000 EUR");
    expect(claim.timeline[0]).toMatchObject({
      type: "FNOL_SUBMITTED",
      source: "Backend",
    });
    expect(claim.triage.reasonCodes).toEqual(["HIGH_DAMAGE_AMOUNT"]);
  });

  it("maps timeline and triage DTOs independently", () => {
    expect(toTimelineEvents([backendEvent])[0].timestamp).toBe("2026-06-26 10:15");
    expect(toTriageSnapshot(backendTriage)).toMatchObject({
      severity: "HIGH",
      fraud: "MEDIUM",
      litigation: "LOW",
    });
  });
});

describe("claim repository", () => {
  it("returns demo claims in demo mode without calling the live API", async () => {
    const api = {
      fetchClaimSummaries: vi.fn(),
      fetchClaim: vi.fn(),
      fetchClaimEvents: vi.fn(),
      fetchClaimTriage: vi.fn(),
    };
    const repository = createClaimRepository({ mode: "demo", api });

    const claims = await repository.listClaims();

    expect(claims[0].claimNumber).toBe("CLM-20260626-000418");
    expect(api.fetchClaimSummaries).not.toHaveBeenCalled();
  });

  it("returns mapped backend claims in live mode", async () => {
    const api = {
      fetchClaimSummaries: vi.fn().mockResolvedValue([backendClaim]),
      fetchClaim: vi.fn().mockResolvedValue(backendClaim),
      fetchClaimEvents: vi.fn().mockResolvedValue([backendEvent]),
      fetchClaimTriage: vi.fn().mockResolvedValue(backendTriage),
    };
    const repository = createClaimRepository({ mode: "live", api });

    const claims = await repository.listClaims();
    const claim = await repository.getClaim("CLM-LIVE-1");

    expect(claims[0].claimNumber).toBe("CLM-LIVE-1");
    expect(claim?.triage.severity).toBe("HIGH");
    expect(api.fetchClaim).toHaveBeenCalledWith("CLM-LIVE-1");
  });
});

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as Response;
}
