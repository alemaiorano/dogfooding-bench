import { DogfoodingOutput } from './types';
export declare class BenchmarkRunner {
    private targetUrl;
    private apiKey;
    private results;
    private startTime;
    constructor(targetUrl: string, apiKey: string);
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