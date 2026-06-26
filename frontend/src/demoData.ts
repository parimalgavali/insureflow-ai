import type { ClaimDetail } from "./types";

export const demoClaims: ClaimDetail[] = [
  {
    claimNumber: "CLM-20260626-000418",
    status: "Needs Review",
    priority: "HIGH",
    customer: {
      name: "Marta Keller",
      customerNumber: "CUST-10042",
      email: "marta.keller@example.test",
      location: "Bielefeld, DE",
    },
    policy: {
      policyNumber: "POL-MOTOR-77881",
      type: "Personal Motor",
      status: "ACTIVE",
      coverageStatus: "Collision covered",
      deductible: "500 EUR",
      limit: "25,000 EUR",
      activeOnLossDate: true,
    },
    claimType: "Motor collision",
    lossDate: "2026-06-20",
    reportedDate: "2026-06-26",
    estimatedLoss: "8,400 EUR",
    description:
      "Rear bumper collision near Bielefeld. The other driver left the scene. Photos and repair invoice are present, but police report is missing.",
    triage: {
      severity: "HIGH",
      fraud: "MEDIUM",
      litigation: "LOW",
      recommendedQueue: "Senior motor adjuster",
      humanReviewRequired: true,
      reasonCodes: ["HIGH_DAMAGE_AMOUNT", "POLICE_REPORT_MISSING", "THIRD_PARTY_INVOLVED"],
    },
    documents: {
      receivedDocuments: ["DAMAGE_PHOTOS", "REPAIR_INVOICE"],
      missingDocuments: ["POLICE_REPORT"],
      extractionHighlights: [
        "Possible hit-and-run detected from loss description.",
        "Repair invoice total is 8,400 EUR.",
        "Initial estimate and invoice amount differ materially.",
      ],
      summarySections: [
        {
          title: "Claim overview",
          body: "High-priority motor collision reported six days after loss.",
        },
        {
          title: "Recommended next action",
          body: "Request police report and keep claim in senior motor queue.",
        },
      ],
    },
    rag: {
      question: "Is this collision loss covered?",
      answer:
        "Based on the retrieved policy coverage section, collision damage appears potentially covered when the policy was active on the loss date. Human review is required before any claim decision.",
      confidence: "MEDIUM",
      sources: [
        {
          documentId: "DOC-POLICY-001",
          chunkId: "DOC-POLICY-001-CHUNK-0001",
          sectionTitle: "Collision Coverage",
        },
      ],
    },
    timeline: [
      {
        timestamp: "2026-06-26 08:24",
        type: "FNOL_SUBMITTED",
        description: "Claim submitted through FNOL intake.",
        source: "Backend",
      },
      {
        timestamp: "2026-06-26 08:26",
        type: "TRIAGE_COMPLETED",
        description: "AI triage recommended senior motor adjuster review.",
        source: "AI Triage",
      },
      {
        timestamp: "2026-06-26 08:31",
        type: "DOCUMENT_SUMMARY",
        description: "Document intelligence detected missing police report.",
        source: "Document AI",
      },
    ],
    audit: [
      {
        timestamp: "2026-06-26 08:26",
        actor: "triage-service",
        action: "AI_SCORE_CREATED",
        detail: "Severity HIGH, fraud MEDIUM, litigation LOW.",
      },
      {
        timestamp: "2026-06-26 08:33",
        actor: "rag-service",
        action: "RAG_QUERY_ANSWERED",
        detail: "Answer returned with one policy source.",
      },
    ],
  },
  {
    claimNumber: "CLM-20260626-000219",
    status: "Open",
    priority: "MEDIUM",
    customer: {
      name: "Jonas Weber",
      customerNumber: "CUST-10418",
      email: "jonas.weber@example.test",
      location: "Hamburg, DE",
    },
    policy: {
      policyNumber: "POL-HOME-44190",
      type: "Homeowners",
      status: "ACTIVE",
      coverageStatus: "Water damage review",
      deductible: "750 EUR",
      limit: "80,000 EUR",
      activeOnLossDate: true,
    },
    claimType: "Property water damage",
    lossDate: "2026-06-23",
    reportedDate: "2026-06-25",
    estimatedLoss: "4,900 EUR",
    description: "Kitchen water damage after pipe leak. Photos received, repair estimate pending.",
    triage: {
      severity: "MEDIUM",
      fraud: "LOW",
      litigation: "LOW",
      recommendedQueue: "Property adjuster",
      humanReviewRequired: false,
      reasonCodes: ["REPAIR_ESTIMATE_MISSING"],
    },
    documents: {
      receivedDocuments: ["DAMAGE_PHOTOS"],
      missingDocuments: ["REPAIR_ESTIMATE"],
      extractionHighlights: ["Water damage appears localized to kitchen.", "No injury or third party reported."],
      summarySections: [
        {
          title: "Claim overview",
          body: "Medium-priority property claim with active policy and missing repair estimate.",
        },
        {
          title: "Recommended next action",
          body: "Request repair estimate and continue standard property review.",
        },
      ],
    },
    rag: {
      question: "What documents are missing?",
      answer:
        "The retrieved claim guideline indicates a repair estimate should be requested before amount validation.",
      confidence: "MEDIUM",
      sources: [
        {
          documentId: "DOC-GUIDE-002",
          chunkId: "DOC-GUIDE-002-CHUNK-0003",
          sectionTitle: "Property Damage Documents",
        },
      ],
    },
    timeline: [
      {
        timestamp: "2026-06-25 10:12",
        type: "FNOL_SUBMITTED",
        description: "Water damage claim submitted.",
        source: "Backend",
      },
      {
        timestamp: "2026-06-25 10:15",
        type: "COVERAGE_VALIDATED",
        description: "Policy was active on loss date.",
        source: "Backend",
      },
    ],
    audit: [
      {
        timestamp: "2026-06-25 10:16",
        actor: "triage-service",
        action: "AI_SCORE_CREATED",
        detail: "Severity MEDIUM, fraud LOW, litigation LOW.",
      },
    ],
  },
  {
    claimNumber: "CLM-20260626-000117",
    status: "Ready for Review",
    priority: "LOW",
    customer: {
      name: "Lea Fischer",
      customerNumber: "CUST-10277",
      email: "lea.fischer@example.test",
      location: "Munich, DE",
    },
    policy: {
      policyNumber: "POL-MOTOR-55124",
      type: "Personal Motor",
      status: "ACTIVE",
      coverageStatus: "Glass covered",
      deductible: "150 EUR",
      limit: "5,000 EUR",
      activeOnLossDate: true,
    },
    claimType: "Glass damage",
    lossDate: "2026-06-24",
    reportedDate: "2026-06-24",
    estimatedLoss: "620 EUR",
    description: "Windshield crack reported same day. Repair estimate and photos received.",
    triage: {
      severity: "LOW",
      fraud: "LOW",
      litigation: "LOW",
      recommendedQueue: "Fast track",
      humanReviewRequired: false,
      reasonCodes: ["LOW_DAMAGE_AMOUNT", "DOCUMENTS_COMPLETE"],
    },
    documents: {
      receivedDocuments: ["DAMAGE_PHOTOS", "REPAIR_ESTIMATE"],
      missingDocuments: [],
      extractionHighlights: ["Glass damage only.", "Documents complete for fast-track review."],
      summarySections: [
        {
          title: "Claim overview",
          body: "Low-risk windshield claim reported on loss date.",
        },
        {
          title: "Recommended next action",
          body: "Proceed with fast-track adjuster review.",
        },
      ],
    },
    rag: {
      question: "What should the adjuster check before approval?",
      answer:
        "The retrieved guideline says the adjuster should confirm active glass coverage and verify the repair estimate before approval.",
      confidence: "MEDIUM",
      sources: [
        {
          documentId: "DOC-GUIDE-003",
          chunkId: "DOC-GUIDE-003-CHUNK-0002",
          sectionTitle: "Glass Claims",
        },
      ],
    },
    timeline: [
      {
        timestamp: "2026-06-24 13:00",
        type: "FNOL_SUBMITTED",
        description: "Glass claim submitted with complete documents.",
        source: "Backend",
      },
    ],
    audit: [
      {
        timestamp: "2026-06-24 13:02",
        actor: "triage-service",
        action: "AI_SCORE_CREATED",
        detail: "Fast-track recommendation created.",
      },
    ],
  },
];
