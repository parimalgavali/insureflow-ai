import { demoClaims } from "../demoData";
import type { ClaimDetail, DataMode } from "../types";
import { createClaimApi, type ClaimApi } from "./claimApi";
import { toClaimDetail } from "./claimMapper";

export interface ClaimRepository {
  readonly mode: DataMode;
  listClaims(): Promise<ClaimDetail[]>;
  getClaim(claimNumber: string): Promise<ClaimDetail | null>;
}

interface ClaimRepositoryOptions {
  mode?: DataMode;
  api?: ClaimApi;
}

export function createClaimRepository(options: ClaimRepositoryOptions = {}): ClaimRepository {
  const mode = options.mode ?? dataModeFromEnvironment();
  const api = options.api ?? createClaimApi();

  if (mode === "demo") {
    return {
      mode,
      async listClaims() {
        return demoClaims;
      },
      async getClaim(claimNumber: string) {
        return demoClaims.find((claim) => claim.claimNumber === claimNumber) ?? null;
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
  };
}

export const claimRepository = createClaimRepository();

function dataModeFromEnvironment(): DataMode {
  return import.meta.env.VITE_DATA_MODE === "live" ? "live" : "demo";
}
