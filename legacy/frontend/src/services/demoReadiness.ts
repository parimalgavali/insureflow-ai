export interface DemoReadinessCheck {
  label: string;
  detail: string;
}

export const demoReadinessChecks: DemoReadinessCheck[] = [
  {
    label: "Frontend smoke",
    detail: "Queue, claim detail, review, documents, governance, integrations, and settings routes are covered by Vitest.",
  },
  {
    label: "Docker app profile",
    detail: "Run docker compose --profile app up --build and scripts/smoke-test-containers.sh for container demo validation.",
  },
  {
    label: "Live backend mode",
    detail: "Set VITE_DATA_MODE=live to call the Spring Boot API through the Vite or nginx /api proxy.",
  },
];
