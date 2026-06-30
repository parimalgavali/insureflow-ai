import type {
  AuditEvent,
  ClaimDetail,
  DocumentIntelligenceSnapshot,
  RagAnswer,
  RiskLabel,
  TimelineEvent,
  TriageSnapshot,
} from "../types";
import type { BackendClaimEventResponse, BackendClaimResponse, BackendClaimTriageResponse } from "./claimApi";

interface ClaimMappingInput {
  claim: BackendClaimResponse;
  events?: BackendClaimEventResponse[];
  triage?: BackendClaimTriageResponse | null;
}

const emptyDocuments: DocumentIntelligenceSnapshot = {
  receivedDocuments: [],
  missingDocuments: ["DOCUMENT_REVIEW_PENDING"],
  extractionHighlights: ["Live document intelligence will be connected in Phase 18."],
  summarySections: [
    {
      title: "Document status",
      body: "Backend claim metadata is live. Document intelligence output is pending a later phase.",
    },
  ],
};

const emptyRag: RagAnswer = {
  question: "What should the adjuster verify?",
  answer: "Live RAG answers will be connected in Phase 18. Use the policy and coverage context shown here.",
  confidence: "LOW",
  sources: [],
};

export function toClaimDetail(input: ClaimMappingInput): ClaimDetail {
  const triage = input.triage ? toTriageSnapshot(input.triage) : fallbackTriage(input.claim);
  return {
    claimNumber: input.claim.claimNumber,
    status: humanize(input.claim.status),
    priority: triage.severity,
    customer: {
      name: input.claim.customerNumber,
      customerNumber: input.claim.customerNumber,
      email: `${input.claim.customerNumber.toLowerCase()}@example.test`,
      location: input.claim.lossLocation ?? "Location unavailable",
    },
    policy: {
      policyNumber: input.claim.policyNumber,
      type: humanize(input.claim.claimType),
      status: input.claim.coverageValidation?.policyStatus ?? "UNKNOWN",
      coverageStatus: coverageStatus(input.claim),
      deductible: money(input.claim.coverageValidation?.deductibleAmount),
      limit: money(input.claim.coverageValidation?.limitAmount),
      activeOnLossDate: input.claim.coverageValidation?.policyStatus === "ACTIVE",
    },
    claimType: humanize(input.claim.claimType),
    lossDate: input.claim.lossDate,
    reportedDate: formatDate(input.claim.reportedAt),
    estimatedLoss: money(input.claim.estimatedLossAmount),
    description: input.claim.description,
    triage,
    documents: emptyDocuments,
    rag: emptyRag,
    timeline: toTimelineEvents(input.events ?? []),
    audit: toAuditEvents(input.triage),
  };
}

export function toTimelineEvents(events: BackendClaimEventResponse[]): TimelineEvent[] {
  return events.map((event) => ({
    timestamp: formatDateTime(event.createdAt),
    type: event.eventType,
    description: event.description,
    source: event.eventSource,
  }));
}

export function toTriageSnapshot(triage: BackendClaimTriageResponse): TriageSnapshot {
  return {
    severity: triage.severityLabel,
    fraud: triage.fraudRiskLabel,
    litigation: triage.litigationRiskLabel,
    recommendedQueue: triage.recommendedQueue,
    humanReviewRequired: triage.humanReviewRequired,
    reasonCodes: triage.reasonCodes,
  };
}

function fallbackTriage(claim: BackendClaimResponse): TriageSnapshot {
  const amount = numeric(claim.estimatedLossAmount);
  const severity: RiskLabel = amount >= 7500 ? "HIGH" : amount >= 2500 ? "MEDIUM" : "LOW";
  return {
    severity,
    fraud: "LOW",
    litigation: "LOW",
    recommendedQueue: severity === "HIGH" ? "Senior adjuster review" : "Standard adjuster review",
    humanReviewRequired: severity === "HIGH",
    reasonCodes: severity === "HIGH" ? ["HIGH_DAMAGE_AMOUNT"] : ["LIVE_BACKEND_CLAIM"],
  };
}

function toAuditEvents(triage?: BackendClaimTriageResponse | null): AuditEvent[] {
  if (!triage) {
    return [];
  }
  return [
    {
      timestamp: formatDateTime(triage.createdAt),
      actor: triage.modelName,
      action: "AI_SCORE_CREATED",
      detail: `${triage.modelVersion}: ${triage.explanation}`,
    },
  ];
}

function coverageStatus(claim: BackendClaimResponse) {
  const coverage = claim.coverageValidation;
  if (!coverage) {
    return "Coverage pending";
  }
  if (!coverage.covered) {
    return "Coverage review required";
  }
  return `${humanize(coverage.coverageType ?? "coverage")} covered`;
}

function money(value: number | string | null | undefined) {
  const amount = numeric(value);
  return `${amount.toLocaleString("en-US", { maximumFractionDigits: 0 })} EUR`;
}

function numeric(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return 0;
  }
  return Number(value);
}

function formatDate(value: string) {
  return value.slice(0, 10);
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toISOString().slice(0, 16).replace("T", " ");
}

function humanize(value: string) {
  return value
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
