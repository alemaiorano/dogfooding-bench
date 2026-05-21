/**
 * Dogfooding Benchmark Types
 */
export interface QuestionBankTest {
    id: string;
    questionSet: string;
    message: string;
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
    totalTests: number;
    passedTests: number;
    failedTests: number;
    avgLatencyMs: number;
    p95LatencyMs: number;
    researchContextPreservation: number;
    faqAccuracy: number;
    dataQueryAccuracy: number;
    helpfulRate: number;
    noFollowUpResolutionRate: number;
    safetyPassRate: number;
    evidenceCoverage: number;
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