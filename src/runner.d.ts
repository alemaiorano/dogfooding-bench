import { DogfoodingOutput } from './types';
export interface RunnerConfig {
    targetUrl?: string;
    apiKey?: string;
    provider?: 'openai' | 'gemini' | 'custom';
    model?: string;
    scenarioPath?: string;
}
export declare class BenchmarkRunner {
    private config;
    private results;
    private startTime;
    private openai?;
    private gemini?;
    private scenarioContext;
    constructor(config: RunnerConfig);
    run(datasetPath: string, studies?: string[], tier?: string): Promise<DogfoodingOutput>;
    private filterQuestions;
    private runTest;
    private validate;
    private calculateKpis;
    private calcRate;
    private calculateStratifiedSummary;
    private generateStructuredOutput;
}
//# sourceMappingURL=runner.d.ts.map