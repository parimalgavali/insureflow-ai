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

export interface BackendHumanReviewResponse {
  id: string;
  claimNumber: string;
  reviewerAdjusterId: string;
  decision: string;
  overrideReason: string | null;
  notes: string | null;
  reviewedAt: string;
}

export interface BackendDocumentWorkspaceResponse {
  claimNumber: string;
  receivedDocuments: string[];
  missingDocuments: string[];
  extractionHighlights: string[];
  summarySections: {
    title: string;
    body: string;
  }[];
}

export interface BackendRagSourceResponse {
  documentId: string;
  chunkId: string;
  documentType: string;
  sectionTitle: string;
  pageNumber: number;
  score: number;
}

export interface BackendRagQuestionResponse {
  claimNumber: string;
  question: string;
  answer: string;
  confidence: RiskLabel;
  requiresHumanReview: boolean;
  sources: BackendRagSourceResponse[];
}

export interface CreateHumanReviewPayload {
  reviewerAdjusterId: string;
  decision: string;
  overrideReason?: string;
  notes?: string;
}

export interface ClaimApi {
  fetchClaimSummaries(): Promise<BackendClaimResponse[]>;
  fetchClaim(claimNumber: string): Promise<BackendClaimResponse>;
  fetchClaimEvents(claimNumber: string): Promise<BackendClaimEventResponse[]>;
  fetchClaimTriage(claimNumber: string): Promise<BackendClaimTriageResponse | null>;
  fetchHumanReviews(claimNumber: string): Promise<BackendHumanReviewResponse[]>;
  fetchDocumentWorkspace(claimNumber: string): Promise<BackendDocumentWorkspaceResponse>;
  askRagQuestion(claimNumber: string, question: string): Promise<BackendRagQuestionResponse>;
  createHumanReview(
    claimNumber: string,
    payload: CreateHumanReviewPayload,
  ): Promise<BackendHumanReviewResponse>;
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

  async function postJson<T>(path: string, body: unknown): Promise<T> {
    const token = await authToken();
    const response = await fetchImpl(`${baseUrl}${path}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

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
    async fetchHumanReviews(claimNumber: string) {
      return (
        (await getJson<BackendHumanReviewResponse[]>(
          `/claims/${encodeURIComponent(claimNumber)}/human-reviews`,
        )) ?? []
      );
    },
    async fetchDocumentWorkspace(claimNumber: string) {
      const workspace = await getJson<BackendDocumentWorkspaceResponse>(
        `/claims/${encodeURIComponent(claimNumber)}/document-workspace`,
      );
      if (!workspace) {
        throw new Error(`Document workspace for ${claimNumber} was not found`);
      }
      return workspace;
    },
    async askRagQuestion(claimNumber: string, question: string) {
      return await postJson<BackendRagQuestionResponse>(
        `/claims/${encodeURIComponent(claimNumber)}/rag-query`,
        { question },
      );
    },
    async createHumanReview(claimNumber: string, payload: CreateHumanReviewPayload) {
      return await postJson<BackendHumanReviewResponse>(
        `/claims/${encodeURIComponent(claimNumber)}/human-reviews`,
        payload,
      );
    },
  };
}
