import { demoClaims } from "../demoData";
import type {
  ClaimDetail,
  DataMode,
  DocumentIntelligenceSnapshot,
  GovernanceDashboard,
  GovernanceFilters,
  HumanReviewRecord,
  HumanReviewSubmission,
  RagAnswer,
} from "../types";
import { createClaimApi, type ClaimApi } from "./claimApi";
import {
  toClaimDetail,
  toDocumentIntelligenceSnapshot,
  toGovernanceAuditEvent,
  toGovernanceModelVersion,
  toGovernancePromptVersion,
  toRagAnswer,
} from "./claimMapper";

export interface ClaimRepository {
  readonly mode: DataMode;
  listClaims(): Promise<ClaimDetail[]>;
  getClaim(claimNumber: string): Promise<ClaimDetail | null>;
  getDocumentWorkspace(claimNumber: string): Promise<DocumentIntelligenceSnapshot | null>;
  askRagQuestion(claimNumber: string, question: string): Promise<RagAnswer | null>;
  getGovernanceDashboard(filters?: GovernanceFilters): Promise<GovernanceDashboard>;
  listHumanReviews(claimNumber: string): Promise<HumanReviewRecord[]>;
  submitHumanReview(claimNumber: string, review: HumanReviewSubmission): Promise<HumanReviewRecord>;
}

interface ClaimRepositoryOptions {
  mode?: DataMode;
  api?: ClaimApi;
  reviewerAdjusterId?: string;
}

export function createClaimRepository(options: ClaimRepositoryOptions = {}): ClaimRepository {
  const mode = options.mode ?? dataModeFromEnvironment();
  const api = options.api ?? createClaimApi();
  const reviewerAdjusterId = options.reviewerAdjusterId ?? reviewerAdjusterIdFromEnvironment();
  const demoReviews = new Map<string, HumanReviewRecord[]>();

  if (mode === "demo") {
    return {
      mode,
      async listClaims() {
        return demoClaims;
      },
      async getClaim(claimNumber: string) {
        return demoClaims.find((claim) => claim.claimNumber === claimNumber) ?? null;
      },
      async getDocumentWorkspace(claimNumber: string) {
        return demoClaims.find((claim) => claim.claimNumber === claimNumber)?.documents ?? null;
      },
      async askRagQuestion(claimNumber: string, question: string) {
        const claim = demoClaims.find((candidate) => candidate.claimNumber === claimNumber);
        if (!claim) {
          return null;
        }
        return {
          ...claim.rag,
          question,
        };
      },
      async getGovernanceDashboard(filters: GovernanceFilters = {}) {
        return demoGovernanceDashboard(filters);
      },
      async listHumanReviews(claimNumber: string) {
        return demoReviews.get(claimNumber) ?? [];
      },
      async submitHumanReview(claimNumber: string, review: HumanReviewSubmission) {
        const record: HumanReviewRecord = {
          id: `demo-review-${Date.now()}`,
          claimNumber,
          reviewerAdjusterId: "demo-adjuster",
          decision: review.action,
          overrideReason: review.action === "OVERRIDE_AI_RECOMMENDATION" ? review.reason : null,
          notes: review.reason,
          reviewedAt: new Date().toISOString(),
        };
        demoReviews.set(claimNumber, [record, ...(demoReviews.get(claimNumber) ?? [])]);
        return record;
      },
    };
  }

  return {
    mode,
    async listClaims() {
      const claims = await api.fetchClaimSummaries();
      return claims.map((claim) => toClaimDetail({ claim }));
    },
    async getClaim(claimNumber: string) {
      const [claim, events, triage, documents, rag] = await Promise.all([
        api.fetchClaim(claimNumber),
        api.fetchClaimEvents(claimNumber),
        api.fetchClaimTriage(claimNumber),
        api.fetchDocumentWorkspace(claimNumber),
        api.askRagQuestion(claimNumber, "What should the adjuster verify?"),
      ]);
      return toClaimDetail({ claim, events, triage, documents, rag });
    },
    async getDocumentWorkspace(claimNumber: string) {
      const workspace = await api.fetchDocumentWorkspace(claimNumber);
      return toDocumentIntelligenceSnapshot(workspace);
    },
    async askRagQuestion(claimNumber: string, question: string) {
      const answer = await api.askRagQuestion(claimNumber, question);
      return toRagAnswer(answer);
    },
    async getGovernanceDashboard(filters: GovernanceFilters = {}) {
      const [claims, models, prompts, auditEvents] = await Promise.all([
        api.fetchClaimSummaries(),
        api.fetchModelVersions(),
        api.fetchPromptVersions(),
        api.fetchAuditEvents(filters),
      ]);
      return {
        modelVersions: models.map(toGovernanceModelVersion),
        promptVersions: prompts.map(toGovernancePromptVersion),
        auditEvents: auditEvents.map(toGovernanceAuditEvent),
        aiEvidence: claims.map((claim) => {
          const detail = toClaimDetail({ claim });
          return {
            claimNumber: detail.claimNumber,
            severity: detail.triage.severity,
            fraud: detail.triage.fraud,
            litigation: detail.triage.litigation,
            reasonCodes: detail.triage.reasonCodes,
            recommendedQueue: detail.triage.recommendedQueue,
            humanReviewRequired: detail.triage.humanReviewRequired,
            ragSourceCount: detail.rag.sources.length,
          };
        }),
      };
    },
    async listHumanReviews(claimNumber: string) {
      const reviews = await api.fetchHumanReviews(claimNumber);
      return reviews.map((review) => ({
        ...review,
        notes: review.notes ?? "",
      }));
    },
    async submitHumanReview(claimNumber: string, review: HumanReviewSubmission) {
      if (!reviewerAdjusterId) {
        throw new Error("VITE_REVIEWER_ADJUSTER_ID is required for live human review submission.");
      }
      const created = await api.createHumanReview(claimNumber, {
        reviewerAdjusterId,
        decision: review.action,
        overrideReason: review.action === "OVERRIDE_AI_RECOMMENDATION" ? review.reason : undefined,
        notes: review.reason,
      });
      return {
        ...created,
        notes: created.notes ?? "",
      };
    },
  };
}

export const claimRepository = createClaimRepository();

function demoGovernanceDashboard(filters: GovernanceFilters): GovernanceDashboard {
  const auditEvents = demoClaims.flatMap((claim) =>
    claim.audit.map((event, index) => ({
      id: `${claim.claimNumber}-${event.action}-${index}`,
      actorType: "SERVICE",
      actorId: event.actor,
      action: event.action,
      entityType: "CLAIMS",
      entityId: claim.claimNumber,
      correlationId: `demo-${claim.claimNumber}-${index + 1}`,
      status: "200",
      createdAt: event.timestamp,
    })),
  );
  const filteredAuditEvents = auditEvents.filter((event) => {
    const entityMatches = !filters.entityType || event.entityType === filters.entityType;
    const actorMatches = !filters.actorId || event.actorId.includes(filters.actorId);
    const actionMatches = !filters.action || event.action.includes(filters.action);
    const correlationMatches = !filters.correlationId || event.correlationId.includes(filters.correlationId);
    return entityMatches && actorMatches && actionMatches && correlationMatches;
  });
  return {
    modelVersions: [
      {
        id: "demo-model-rule-triage",
        name: "rule-based-triage",
        version: "1.0.0",
        type: "RULE_ENGINE",
        artifactUri: "registry://demo/rule-based-triage/1.0.0",
        metrics: { deterministic: true },
        active: true,
      },
      {
        id: "demo-model-rag",
        name: "deterministic-rag",
        version: "v1",
        type: "RAG",
        artifactUri: "registry://demo/deterministic-rag/v1",
        metrics: { sourceGrounded: true },
        active: true,
      },
    ],
    promptVersions: [
      {
        id: "demo-prompt-rag-answer",
        name: "rag-adjuster-answer",
        version: "v1",
        modelName: "deterministic-rag",
        templatePreview: "Answer adjuster questions only from retrieved claim evidence.",
        active: true,
      },
      {
        id: "demo-prompt-document-extraction",
        name: "document-extraction",
        version: "v1",
        modelName: "deterministic-document-intelligence",
        templatePreview: "Extract claim document fields and missing evidence.",
        active: true,
      },
    ],
    auditEvents: filteredAuditEvents,
    aiEvidence: demoClaims.map((claim) => ({
      claimNumber: claim.claimNumber,
      severity: claim.triage.severity,
      fraud: claim.triage.fraud,
      litigation: claim.triage.litigation,
      reasonCodes: claim.triage.reasonCodes,
      recommendedQueue: claim.triage.recommendedQueue,
      humanReviewRequired: claim.triage.humanReviewRequired,
      ragSourceCount: claim.rag.sources.length,
    })),
  };
}

function dataModeFromEnvironment(): DataMode {
  return import.meta.env.VITE_DATA_MODE === "live" ? "live" : "demo";
}

function reviewerAdjusterIdFromEnvironment() {
  return import.meta.env.VITE_REVIEWER_ADJUSTER_ID;
}
