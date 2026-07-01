import { demoClaims } from "../demoData";
import type { ClaimDetail, DataMode, HumanReviewRecord, HumanReviewSubmission } from "../types";
import { createClaimApi, type ClaimApi } from "./claimApi";
import { toClaimDetail } from "./claimMapper";

export interface ClaimRepository {
  readonly mode: DataMode;
  listClaims(): Promise<ClaimDetail[]>;
  getClaim(claimNumber: string): Promise<ClaimDetail | null>;
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
      const [claim, events, triage] = await Promise.all([
        api.fetchClaim(claimNumber),
        api.fetchClaimEvents(claimNumber),
        api.fetchClaimTriage(claimNumber),
      ]);
      return toClaimDetail({ claim, events, triage });
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

function dataModeFromEnvironment(): DataMode {
  return import.meta.env.VITE_DATA_MODE === "live" ? "live" : "demo";
}

function reviewerAdjusterIdFromEnvironment() {
  return import.meta.env.VITE_REVIEWER_ADJUSTER_ID;
}
