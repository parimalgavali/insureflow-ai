import type { RiskLabel } from "../types";

export interface BackendCoverageValidation {
  covered: boolean;
  policyStatus: string | null;
  coverageType: string | null;
  limitAmount: number | string | null;
  deductibleAmount: number | string | null;
  exclusions: string | null;
  reasons: string[];
  warnings: string[];
}

export interface BackendClaimResponse {
  claimNumber: string;
  policyNumber: string;
  customerNumber: string;
  claimType: string;
  status: string;
  lossDate: string;
  reportedAt: string;
  lossLocation: string | null;
  description: string;
  estimatedLossAmount: number | string | null;
  coverageValidation: BackendCoverageValidation | null;
}

export interface BackendClaimEventResponse {
  eventType: string;
  eventSource: string;
  description: string;
  payload: Record<string, unknown>;
  createdAt: string;
}

export interface BackendClaimTriageResponse {
  claimNumber: string;
  modelName: string;
  modelVersion: string;
  severityScore: number | string;
  severityLabel: RiskLabel;
  fraudRiskScore: number | string;
  fraudRiskLabel: RiskLabel;
  litigationRiskScore: number | string;
  litigationRiskLabel: RiskLabel;
  recommendedQueue: string;
  reasonCodes: string[];
  humanReviewRequired: boolean;
  explanation: string;
  createdAt: string;
}

export interface ClaimApi {
  fetchClaimSummaries(): Promise<BackendClaimResponse[]>;
  fetchClaim(claimNumber: string): Promise<BackendClaimResponse>;
  fetchClaimEvents(claimNumber: string): Promise<BackendClaimEventResponse[]>;
  fetchClaimTriage(claimNumber: string): Promise<BackendClaimTriageResponse | null>;
}

export interface ClaimApiOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
}

interface DevTokenResponse {
  token: string;
}

export function createClaimApi(options: ClaimApiOptions = {}): ClaimApi {
  const baseUrl = options.baseUrl ?? "/api/v1";
  const fetchImpl = options.fetchImpl ?? fetch;
  let tokenPromise: Promise<string> | null = null;

  async function requestDevToken() {
    const response = await fetchImpl(`${baseUrl}/auth/dev-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        subject: "frontend-adjuster",
        roles: ["ADJUSTER"],
      }),
    });
    if (!response.ok) {
      throw new Error(`Unable to create development token (${response.status})`);
    }
    const body = (await response.json()) as DevTokenResponse;
    return body.token;
  }

  async function authToken() {
    tokenPromise ??= requestDevToken();
    return tokenPromise;
  }

  async function getJson<T>(path: string, allowMissing = false): Promise<T | null> {
    const token = await authToken();
    const response = await fetchImpl(`${baseUrl}${path}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (allowMissing && response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error(`Request failed for ${path} (${response.status})`);
    }
    return (await response.json()) as T;
  }

  return {
    async fetchClaimSummaries() {
      return (await getJson<BackendClaimResponse[]>("/claims")) ?? [];
    },
    async fetchClaim(claimNumber: string) {
      const claim = await getJson<BackendClaimResponse>(`/claims/${encodeURIComponent(claimNumber)}`);
      if (!claim) {
        throw new Error(`Claim ${claimNumber} was not found`);
      }
      return claim;
    },
    async fetchClaimEvents(claimNumber: string) {
      return (await getJson<BackendClaimEventResponse[]>(`/claims/${encodeURIComponent(claimNumber)}/events`)) ?? [];
    },
    async fetchClaimTriage(claimNumber: string) {
      return await getJson<BackendClaimTriageResponse>(`/claims/${encodeURIComponent(claimNumber)}/triage`, true);
    },
  };
}
