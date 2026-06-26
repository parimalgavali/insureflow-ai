export type RiskLabel = "LOW" | "MEDIUM" | "HIGH";

export interface QueueFilters {
  search: string;
  risk: "ALL" | RiskLabel;
  status: "ALL" | string;
}

export interface CustomerSnapshot {
  name: string;
  customerNumber: string;
  email: string;
  location: string;
}

export interface PolicySnapshot {
  policyNumber: string;
  type: string;
  status: string;
  coverageStatus: string;
  deductible: string;
  limit: string;
  activeOnLossDate: boolean;
}

export interface TriageSnapshot {
  severity: RiskLabel;
  fraud: RiskLabel;
  litigation: RiskLabel;
  recommendedQueue: string;
  humanReviewRequired: boolean;
  reasonCodes: string[];
}

export interface DocumentIntelligenceSnapshot {
  receivedDocuments: string[];
  missingDocuments: string[];
  extractionHighlights: string[];
  summarySections: {
    title: string;
    body: string;
  }[];
}

export interface RagSource {
  documentId: string;
  chunkId: string;
  sectionTitle: string;
}

export interface RagAnswer {
  question: string;
  answer: string;
  confidence: RiskLabel;
  sources: RagSource[];
}

export interface TimelineEvent {
  timestamp: string;
  type: string;
  description: string;
  source: string;
}

export interface AuditEvent {
  timestamp: string;
  actor: string;
  action: string;
  detail: string;
}

export interface ClaimDetail {
  claimNumber: string;
  status: string;
  priority: RiskLabel;
  customer: CustomerSnapshot;
  policy: PolicySnapshot;
  claimType: string;
  lossDate: string;
  reportedDate: string;
  estimatedLoss: string;
  description: string;
  triage: TriageSnapshot;
  documents: DocumentIntelligenceSnapshot;
  rag: RagAnswer;
  timeline: TimelineEvent[];
  audit: AuditEvent[];
}

export interface HumanReviewSubmission {
  action: string;
  reason: string;
}
