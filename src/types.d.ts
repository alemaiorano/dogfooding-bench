/**
 * Dogfooding Benchmark Types
 */
export interface QuestionBankTest {
    id: string;
    questionSet: string;
    message?: string;
    text?: string;
    category: string;
    rawCategory: string;
    rawIntent?: string;
    intent?: string;
    persona?: string;
    requiresWeb?: boolean;
    notes?: string;
    history?: Array<{
        role: string;
        content: string;
    }>;
    expectedPath?: string[];
    expectedIntent?: string;
    expectedFaqHandled?: boolean;
    expectedMetric?: string;
    expectedMetricTolerance?: number;
    strictPathCheck?: boolean;
    maxLatencyMs?: number;
    threadKey?: string;
}
export interface TestResult {
    testId: string;
    questionSet: string;
    message: string;
    persona?: string;
    category: string;
    rawCategory: string;
    rawIntent?: string;
    requiresWeb?: boolean;
    evidenceCitationPresent?: boolean;
    success: boolean;
    latencyMs: number;
    agentPath: string[];
    responseText: string;
    sourceIds?: string[];
    intent?: string;
    faqHandled?: boolean;
    issues: string[];
    notes?: string;
    researchContextPreserved?: boolean;
    traceEvents?: any[];
    traceSpans?: any[];
}
export interface KpiSummary {
    successRate: number | null;
    totalTests: number;
    passedTests: number;
    failedTests: number;
    avgLatencyMs: number | null;
    p95LatencyMs: number | null;
    researchContextPreservation: number | null;
    faqAccuracy: number | null;
    dataQueryAccuracy: number | null;
    helpfulRate: number | null;
    noFollowUpResolutionRate: number | null;
    safetyPassRate: number | null;
    evidenceCoverage: number | null;
}
export interface GroupMetric {
    key: string;
    total: number;
    passed: number;
    failed: number;
    successRate: number;
    avgLatencyMs: number;
    p95LatencyMs: number;
}
export interface StratifiedSummary {
    byQuestionSet: GroupMetric[];
    byPersona: GroupMetric[];
    byRawCategory: GroupMetric[];
    byMappedCategory: GroupMetric[];
    byIntent: GroupMetric[];
    byRequiresWeb: GroupMetric[];
}
export interface DogfoodingOutput {
    metadata: {
        runId: string;
        timestamp: string;
        environment: string;
        user: string;
        questionSet: string;
        durationMs: number;
        tier: string;
    };
    scope: any;
    kpiSummary: KpiSummary;
    stratified: StratifiedSummary;
    qualityGates: any[];
    triage: any;
    results: TestResult[];
    recommendation: "promote" | "hold" | "rollback";
    topIssues: string[];
    insights: string[];
}
//# sourceMappingURL=types.d.ts.map