import type {
  AuditEvent,
  ClaimDetail,
  DocumentIntelligenceSnapshot,
  GovernanceAuditEvent,
  GovernanceModelVersion,
  GovernancePromptVersion,
  RagAnswer,
  RiskLabel,
  TimelineEvent,
  TriageSnapshot,
} from "../types";
import type { BackendClaimEventResponse, BackendClaimResponse, BackendClaimTriageResponse } from "./claimApi";
import type {
  BackendDocumentWorkspaceResponse,
  BackendGovernanceAuditEventResponse,
  BackendModelVersionResponse,
  BackendPromptVersionResponse,
  BackendRagQuestionResponse,
} from "./claimApi";

interface ClaimMappingInput {
  claim: BackendClaimResponse;
  events?: BackendClaimEventResponse[];
  triage?: BackendClaimTriageResponse | null;
  documents?: BackendDocumentWorkspaceResponse | null;
  rag?: BackendRagQuestionResponse | null;
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
    documents: input.documents ? toDocumentIntelligenceSnapshot(input.documents) : emptyDocuments,
    rag: input.rag ? toRagAnswer(input.rag) : emptyRag,
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

export function toDocumentIntelligenceSnapshot(
  workspace: BackendDocumentWorkspaceResponse,
): DocumentIntelligenceSnapshot {
  return {
    receivedDocuments: workspace.receivedDocuments,
    missingDocuments: workspace.missingDocuments,
    extractionHighlights: workspace.extractionHighlights,
    summarySections: workspace.summarySections,
  };
}

export function toRagAnswer(answer: BackendRagQuestionResponse): RagAnswer {
  return {
    question: answer.question,
    answer: answer.answer,
    confidence: answer.confidence,
    sources: answer.sources.map((source) => ({
      documentId: source.documentId,
      chunkId: source.chunkId,
      sectionTitle: source.sectionTitle,
    })),
  };
}

export function toGovernanceModelVersion(model: BackendModelVersionResponse): GovernanceModelVersion {
  return {
    id: model.id,
    name: model.modelName,
    version: model.version,
    type: model.modelType,
    artifactUri: model.artifactUri,
    metrics: model.metrics,
    active: model.active,
  };
}

export function toGovernancePromptVersion(prompt: BackendPromptVersionResponse): GovernancePromptVersion {
  return {
    id: prompt.id,
    name: prompt.promptName,
    version: prompt.version,
    modelName: prompt.modelName,
    templatePreview: prompt.template.length > 140 ? `${prompt.template.slice(0, 137)}...` : prompt.template,
    active: prompt.active,
  };
}

export function toGovernanceAuditEvent(event: BackendGovernanceAuditEventResponse): GovernanceAuditEvent {
  const status = event.afterState?.status;
  return {
    id: event.id,
    actorType: event.actorType,
    actorId: event.actorId ?? "anonymous",
    action: event.action,
    entityType: event.entityType,
    entityId: event.entityId,
    correlationId: event.correlationId,
    status: typeof status === "number" || typeof status === "string" ? String(status) : "unknown",
    createdAt: formatDateTime(event.createdAt),
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
