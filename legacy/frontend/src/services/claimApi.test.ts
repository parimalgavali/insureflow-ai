import { describe, expect, it, vi } from "vitest";

import {
  createClaimApi,
  type BackendClaimTriageResponse,
  type BackendDocumentWorkspaceResponse,
  type BackendGovernanceAuditEventResponse,
  type BackendModelVersionResponse,
  type BackendPromptVersionResponse,
  type BackendRagQuestionResponse,
} from "./claimApi";
import {
  toClaimDetail,
  toDocumentIntelligenceSnapshot,
  toGovernanceAuditEvent,
  toGovernanceModelVersion,
  toGovernancePromptVersion,
  toRagAnswer,
  toTimelineEvents,
  toTriageSnapshot,
} from "./claimMapper";
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

const backendHumanReview = {
  id: "00000000-0000-4000-8000-000000000001",
  claimNumber: "CLM-LIVE-1",
  reviewerAdjusterId: "00000000-0000-4000-8000-000000000099",
  decision: "REQUEST_MORE_INFORMATION",
  overrideReason: null,
  notes: "Need police report before moving workflow.",
  reviewedAt: "2026-06-26T10:20:30Z",
};

const backendDocumentWorkspace: BackendDocumentWorkspaceResponse = {
  claimNumber: "CLM-LIVE-1",
  receivedDocuments: ["DAMAGE_PHOTOS", "REPAIR_INVOICE"],
  missingDocuments: ["POLICE_REPORT"],
  extractionHighlights: ["Repair invoice total is 9,000 EUR."],
  summarySections: [
    {
      title: "Claim overview",
      body: "High priority collision claim.",
    },
  ],
};

const backendRagAnswer: BackendRagQuestionResponse = {
  claimNumber: "CLM-LIVE-1",
  question: "Is this collision loss covered?",
  answer: "This collision loss appears potentially covered pending human review.",
  confidence: "MEDIUM",
  requiresHumanReview: true,
  sources: [
    {
      documentId: "CLAIM-CLM-LIVE-1",
      chunkId: "CLAIM-CLM-LIVE-1-LIVE-CONTEXT",
      documentType: "CLAIM_CONTEXT",
      sectionTitle: "Coverage validation",
      pageNumber: 1,
      score: 0.72,
    },
  ],
};

const backendModelVersion: BackendModelVersionResponse = {
  id: "00000000-0000-4000-8000-000000000101",
  modelName: "rule-based-triage",
  version: "1.0.0",
  modelType: "RULE_ENGINE",
  artifactUri: "registry://rule-based-triage/1.0.0",
  metrics: { coverage: 1 },
  active: true,
};

const backendPromptVersion: BackendPromptVersionResponse = {
  id: "00000000-0000-4000-8000-000000000102",
  promptName: "rag-adjuster-answer",
  version: "v1",
  template: "Answer with grounded claim evidence.",
  modelName: "deterministic-rag",
  active: true,
};

const backendAuditEvent: BackendGovernanceAuditEventResponse = {
  id: "00000000-0000-4000-8000-000000000103",
  actorType: "USER",
  actorId: "demo-adjuster",
  action: "GET /api/v1/claims/CLM-LIVE-1",
  entityType: "CLAIMS",
  entityId: "00000000-0000-0000-0000-000000000000",
  correlationId: "corr-governance-001",
  afterState: { status: 200, path: "/api/v1/claims/CLM-LIVE-1" },
  createdAt: "2026-06-26T10:21:30Z",
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

  it("lists and creates human reviews with bearer auth", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ token: "dev-token" }))
      .mockResolvedValueOnce(jsonResponse([backendHumanReview]))
      .mockResolvedValueOnce(jsonResponse(backendHumanReview));
    const api = createClaimApi({ baseUrl: "/api/v1", fetchImpl: fetchMock });

    const reviews = await api.fetchHumanReviews("CLM-LIVE-1");
    const created = await api.createHumanReview("CLM-LIVE-1", {
      reviewerAdjusterId: "00000000-0000-4000-8000-000000000099",
      decision: "REQUEST_MORE_INFORMATION",
      notes: "Need police report before moving workflow.",
    });

    expect(reviews).toHaveLength(1);
    expect(created.decision).toBe("REQUEST_MORE_INFORMATION");
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/claims/CLM-LIVE-1/human-reviews",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer dev-token" }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/v1/claims/CLM-LIVE-1/human-reviews",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("REQUEST_MORE_INFORMATION"),
      }),
    );
  });

  it("fetches document workspaces and asks grounded RAG questions with bearer auth", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ token: "dev-token" }))
      .mockResolvedValueOnce(jsonResponse(backendDocumentWorkspace))
      .mockResolvedValueOnce(jsonResponse(backendRagAnswer));
    const api = createClaimApi({ baseUrl: "/api/v1", fetchImpl: fetchMock });

    const workspace = await api.fetchDocumentWorkspace("CLM-LIVE-1");
    const answer = await api.askRagQuestion("CLM-LIVE-1", "Is this collision loss covered?");

    expect(workspace.missingDocuments).toEqual(["POLICE_REPORT"]);
    expect(answer.sources[0].sectionTitle).toBe("Coverage validation");
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/claims/CLM-LIVE-1/document-workspace",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer dev-token" }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/v1/claims/CLM-LIVE-1/rag-query",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ question: "Is this collision loss covered?" }),
      }),
    );
  });

  it("fetches governance registries and filtered audit events with bearer auth", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ token: "dev-token" }))
      .mockResolvedValueOnce(jsonResponse([backendModelVersion]))
      .mockResolvedValueOnce(jsonResponse([backendPromptVersion]))
      .mockResolvedValueOnce(jsonResponse([backendAuditEvent]));
    const api = createClaimApi({ baseUrl: "/api/v1", fetchImpl: fetchMock });

    const models = await api.fetchModelVersions();
    const prompts = await api.fetchPromptVersions();
    const audit = await api.fetchAuditEvents({
      entityType: "CLAIMS",
      actorId: "demo-adjuster",
      correlationId: "corr-governance-001",
    });

    expect(models[0].modelName).toBe("rule-based-triage");
    expect(prompts[0].promptName).toBe("rag-adjuster-answer");
    expect(audit[0].correlationId).toBe("corr-governance-001");
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/governance/model-versions",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer dev-token" }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "/api/v1/audit/events?entityType=CLAIMS&actorId=demo-adjuster&correlationId=corr-governance-001",
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

  it("maps document workspace and RAG DTOs into workbench widgets", () => {
    expect(toDocumentIntelligenceSnapshot(backendDocumentWorkspace)).toMatchObject({
      receivedDocuments: ["DAMAGE_PHOTOS", "REPAIR_INVOICE"],
      missingDocuments: ["POLICE_REPORT"],
    });
    expect(toRagAnswer(backendRagAnswer)).toMatchObject({
      question: "Is this collision loss covered?",
      confidence: "MEDIUM",
      sources: [
        {
          chunkId: "CLAIM-CLM-LIVE-1-LIVE-CONTEXT",
          sectionTitle: "Coverage validation",
        },
      ],
    });
  });

  it("maps governance registry and audit DTOs into dashboard widgets", () => {
    expect(toGovernanceModelVersion(backendModelVersion)).toMatchObject({
      name: "rule-based-triage",
      version: "1.0.0",
      active: true,
    });
    expect(toGovernancePromptVersion(backendPromptVersion)).toMatchObject({
      name: "rag-adjuster-answer",
      modelName: "deterministic-rag",
    });
    expect(toGovernanceAuditEvent(backendAuditEvent)).toMatchObject({
      actorId: "demo-adjuster",
      entityType: "CLAIMS",
      correlationId: "corr-governance-001",
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
      fetchHumanReviews: vi.fn(),
      createHumanReview: vi.fn(),
      fetchDocumentWorkspace: vi.fn(),
      askRagQuestion: vi.fn(),
      fetchModelVersions: vi.fn(),
      fetchPromptVersions: vi.fn(),
      fetchAuditEvents: vi.fn(),
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
      fetchHumanReviews: vi.fn().mockResolvedValue([backendHumanReview]),
      createHumanReview: vi.fn().mockResolvedValue(backendHumanReview),
      fetchDocumentWorkspace: vi.fn().mockResolvedValue(backendDocumentWorkspace),
      askRagQuestion: vi.fn().mockResolvedValue(backendRagAnswer),
      fetchModelVersions: vi.fn().mockResolvedValue([backendModelVersion]),
      fetchPromptVersions: vi.fn().mockResolvedValue([backendPromptVersion]),
      fetchAuditEvents: vi.fn().mockResolvedValue([backendAuditEvent]),
    };
    const repository = createClaimRepository({
      mode: "live",
      api,
      reviewerAdjusterId: "00000000-0000-4000-8000-000000000099",
    });

    const claims = await repository.listClaims();
    const claim = await repository.getClaim("CLM-LIVE-1");
    const created = await repository.submitHumanReview("CLM-LIVE-1", {
      action: "REQUEST_MORE_INFORMATION",
      reason: "Need police report before moving workflow.",
    });
    const reviews = await repository.listHumanReviews("CLM-LIVE-1");

    expect(claims[0].claimNumber).toBe("CLM-LIVE-1");
    expect(claim?.triage.severity).toBe("HIGH");
    expect(claim?.documents.missingDocuments).toEqual(["POLICE_REPORT"]);
    expect(claim?.rag.answer).toContain("collision loss");
    expect(created.decision).toBe("REQUEST_MORE_INFORMATION");
    expect(reviews[0].notes).toBe("Need police report before moving workflow.");
    expect(api.fetchClaim).toHaveBeenCalledWith("CLM-LIVE-1");
    expect(api.fetchDocumentWorkspace).toHaveBeenCalledWith("CLM-LIVE-1");
    expect(api.askRagQuestion).toHaveBeenCalledWith("CLM-LIVE-1", "What should the adjuster verify?");
  });

  it("returns a live governance dashboard with audit filters", async () => {
    const api = {
      fetchClaimSummaries: vi.fn().mockResolvedValue([backendClaim]),
      fetchClaim: vi.fn(),
      fetchClaimEvents: vi.fn(),
      fetchClaimTriage: vi.fn(),
      fetchHumanReviews: vi.fn(),
      createHumanReview: vi.fn(),
      fetchDocumentWorkspace: vi.fn(),
      askRagQuestion: vi.fn(),
      fetchModelVersions: vi.fn().mockResolvedValue([backendModelVersion]),
      fetchPromptVersions: vi.fn().mockResolvedValue([backendPromptVersion]),
      fetchAuditEvents: vi.fn().mockResolvedValue([backendAuditEvent]),
    };
    const repository = createClaimRepository({ mode: "live", api });

    const dashboard = await repository.getGovernanceDashboard({
      entityType: "CLAIMS",
      actorId: "demo-adjuster",
    });

    expect(dashboard.modelVersions[0].name).toBe("rule-based-triage");
    expect(dashboard.promptVersions[0].name).toBe("rag-adjuster-answer");
    expect(dashboard.auditEvents[0].actorId).toBe("demo-adjuster");
    expect(dashboard.aiEvidence[0].claimNumber).toBe("CLM-LIVE-1");
    expect(api.fetchAuditEvents).toHaveBeenCalledWith({
      entityType: "CLAIMS",
      actorId: "demo-adjuster",
    });
  });

  it("returns document workspaces and RAG answers in demo mode", async () => {
    const repository = createClaimRepository({ mode: "demo" });

    const documents = await repository.getDocumentWorkspace("CLM-20260626-000418");
    const rag = await repository.askRagQuestion("CLM-20260626-000418", "What is covered?");

    expect(documents?.missingDocuments).toContain("POLICE_REPORT");
    expect(rag?.sources.length).toBeGreaterThan(0);
  });

  it("returns a demo governance dashboard without calling the live API", async () => {
    const api = {
      fetchClaimSummaries: vi.fn(),
      fetchClaim: vi.fn(),
      fetchClaimEvents: vi.fn(),
      fetchClaimTriage: vi.fn(),
      fetchHumanReviews: vi.fn(),
      createHumanReview: vi.fn(),
      fetchDocumentWorkspace: vi.fn(),
      askRagQuestion: vi.fn(),
      fetchModelVersions: vi.fn(),
      fetchPromptVersions: vi.fn(),
      fetchAuditEvents: vi.fn(),
    };
    const repository = createClaimRepository({ mode: "demo", api });

    const dashboard = await repository.getGovernanceDashboard({ entityType: "CLAIMS" });

    expect(dashboard.modelVersions[0].name).toBe("rule-based-triage");
    expect(dashboard.promptVersions[0].name).toBe("rag-adjuster-answer");
    expect(dashboard.auditEvents[0].entityType).toBe("CLAIMS");
    expect(dashboard.aiEvidence[0].ragSourceCount).toBeGreaterThan(0);
    expect(api.fetchModelVersions).not.toHaveBeenCalled();
  });

  it("records demo human reviews in memory", async () => {
    const repository = createClaimRepository({ mode: "demo" });

    const created = await repository.submitHumanReview("CLM-20260626-000418", {
      action: "ACCEPT_AI_RECOMMENDATION",
      reason: "Coverage and document requirements reviewed.",
    });
    const reviews = await repository.listHumanReviews("CLM-20260626-000418");

    expect(created.decision).toBe("ACCEPT_AI_RECOMMENDATION");
    expect(reviews[0].notes).toBe("Coverage and document requirements reviewed.");
  });
});

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as Response;
}
