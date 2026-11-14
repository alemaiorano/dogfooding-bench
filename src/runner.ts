import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { OpenAI } from 'openai';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { 
  QuestionBankTest, 
  TestResult, 
  KpiSummary, 
  StratifiedSummary, 
  DogfoodingOutput,
  GroupMetric
} from './types';

const DEFAULT_MAX_LATENCY_MS = 15000;
const CATEGORY_MAX_LATENCY_MS: Record<string, number> = {
  action: 20000,
  content_generation: 25000,
  complex_constraints: 25000,
  out_of_domain: 20000,
  multilingual: 20000,
};

const MAX_RESPONSE_LENGTH = 3000;

export interface RunnerConfig {
  targetUrl?: string;
  apiKey?: string;
  provider?: 'openai' | 'gemini' | 'custom';
  model?: string;
  scenarioPath?: string;
}

export class BenchmarkRunner {
  private config: RunnerConfig;
  private results: TestResult[] = [];
  private startTime: number = 0;
  private openai?: OpenAI;
  private gemini?: GoogleGenerativeAI;
  private scenarioContext: string = '';

  constructor(config: RunnerConfig) {
    this.config = config;
    if (config.provider === 'openai') {
      this.openai = new OpenAI({ apiKey: config.apiKey });
    } else if (config.provider === 'gemini') {
      this.gemini = new GoogleGenerativeAI(config.apiKey || '');
    }

    // Load scenario context if provided
    const sPath = config.scenarioPath || path.join(__dirname, 'scenario-A.json');
    if (fs.existsSync(sPath)) {
      const scenarioData = JSON.parse(fs.readFileSync(sPath, 'utf-8'));
      this.scenarioContext = `
CONTEXT SCENARIO:
You are an AI assistant for the 'the platform' marketing tool.
Current World State / Mock Data:
${JSON.stringify(scenarioData, null, 2)}

INSTRUCTIONS:
1. Use the data above to answer user questions.
2. If the user asks about 'my simulations' or metrics, refer to the data in 'accountData'.
3. Be professional and concise.
`;
    }
  }

  async run(datasetPath: string, studies: string[] = ['core', 'v2'], tier: string = 'smoke'): Promise<DogfoodingOutput> {
    this.results = [];
    this.startTime = Date.now();
    const dataset = JSON.parse(fs.readFileSync(datasetPath, 'utf-8'));
    const questions = this.filterQuestions(dataset, studies, tier);

    console.log(`\n🚀 Starting Benchmark | Mode: ${this.config.provider || 'custom'} | Tests: ${questions.length}`);

    for (let i = 0; i < questions.length; i++) {
      const test = questions[i];
      await this.runTest(test, i + 1, questions.length);
    }

    const durationMs = Date.now() - this.startTime;
    const kpis = this.calculateKpis();
    const stratified = this.calculateStratifiedSummary();

    return this.generateStructuredOutput(kpis, stratified, durationMs, studies.join(','), tier);
  }

  private filterQuestions(dataset: any, studies: string[], tier: string): QuestionBankTest[] {
    let all: QuestionBankTest[] = dataset.questions || [];
    return all;
  }

  private async runTest(test: QuestionBankTest, index: number, total: number) {
    const questionText = test.text || test.message || '';
    console.log(`[${index}/${total}] ${test.id}: ${questionText.substring(0, 60)}...`);

    const start = Date.now();
    let success = false;
    let issues: string[] = [];
    let responseText = '';
    let agentPath: string[] = [];
    let intent = '';
    let faqHandled = false;
    let sourceIds: string[] = [];
    let traceEvents: any[] = [];

    try {
      if (this.config.provider === 'openai') {
        const completion = await this.openai!.chat.completions.create({
          messages: [
            { role: 'system', content: this.scenarioContext },
            { role: 'user', content: questionText }
          ],
          model: this.config.model || 'gpt-4o',
        });
        responseText = completion.choices[0].message.content || '';
        agentPath = ['openai-direct'];
      } else if (this.config.provider === 'gemini') {
        // Updated model naming convention for Gemini
        let modelName = this.config.model || 'gemini-2.5-flash';
        if (!modelName.startsWith('models/')) modelName = `models/${modelName}`;

        const model = this.gemini!.getGenerativeModel({ 
          model: modelName,
          systemInstruction: this.scenarioContext
        });
        const result = await model.generateContent(questionText);
        responseText = result.response.text();
        agentPath = ['gemini-direct'];
      } else {
        // Custom HTTP Endpoint (e.g. the platform API)
        const response = await axios.post(this.config.targetUrl!.replace(/\/$/, '') + '/message', {
          message: questionText,
          conversationId: `bench-${test.id}-${Date.now()}`,
        }, {
          headers: {
            'Authorization': `Bearer ${this.config.apiKey}`,
            'Content-Type': 'application/json'
          },
          timeout: 45000
        });
        const data = response.data.data;
        responseText = data.response?.text || '';
        agentPath = data.metadata?.agentPath || [];
        intent = data.metadata?.intent || '';
        faqHandled = data.metadata?.faqHandled || false;
        sourceIds = data.response?.sources?.map((s: any) => s.id) || [];
        traceEvents = data.metadata?.trace?.events || [];
      }

      const latencyMs = Date.now() - start;
      const validation = this.validate(test, responseText, agentPath, intent, faqHandled, latencyMs, sourceIds);
      issues = validation.issues;
      success = issues.length === 0;

      this.results.push({
        testId: test.id,
        questionSet: test.questionSet || 'default',
        message: questionText,
        persona: test.persona,
        category: test.category || 'unknown',
        rawCategory: test.rawCategory || 'unknown',
        requiresWeb: !!test.requiresWeb,
        success,
        latencyMs,
        agentPath,
        responseText,
        sourceIds,
        intent,
        faqHandled,
        issues,
        researchContextPreserved: validation.researchContextPreserved,
        evidenceCitationPresent: validation.evidenceCitationPresent,
        traceEvents
      });

      console.log(`  ${success ? '✅' : '❌'} ${latencyMs}ms | ${agentPath.join(' -> ')}`);
      if (issues.length) console.log(`     Issues: ${issues.join(', ')}`);

    } catch (error: any) {
      const latencyMs = Date.now() - start;
      const errorMsg = error.response?.data?.error?.message || error.message;
      issues.push(`Error: ${errorMsg}`);

      this.results.push({
        testId: test.id,
        questionSet: test.questionSet || 'default',
        message: questionText,
        category: test.category || 'unknown',
        rawCategory: test.rawCategory || 'unknown',
        requiresWeb: !!test.requiresWeb,
        success: false,
        latencyMs,
        agentPath: [],
        responseText: '',
        issues
      });

      console.log(`  ❌ Error: ${errorMsg}`);
    }
  }

  private validate(test: QuestionBankTest, responseText: string, agentPath: string[], intent: string, faqHandled: boolean, latencyMs: number, sourceIds: string[]) {
    const issues: string[] = [];

    if (test.expectedPath && test.expectedPath.length > 0 && !agentPath.includes('openai-direct') && !agentPath.includes('gemini-direct')) {
      const expectedLast = test.expectedPath[test.expectedPath.length - 1];
      const actualLast = agentPath[agentPath.length - 1];
      if (actualLast !== expectedLast) {
        issues.push(`Path: Expected ${expectedLast}, got ${actualLast}`);
      }
    }

    if (!responseText || responseText.length < 5) {
      issues.push('Response: Too short or empty');
    }
    if (responseText.length > MAX_RESPONSE_LENGTH) {
      issues.push('Response: Too long (verbosity)');
    }

    const maxLatency = test.maxLatencyMs || CATEGORY_MAX_LATENCY_MS[test.category] || DEFAULT_MAX_LATENCY_MS;
    if (latencyMs > maxLatency) {
      issues.push(`Latency: ${latencyMs}ms exceeds ${maxLatency}ms`);
    }

    const evidenceCitationPresent = sourceIds.some(id => typeof id === 'string' && id.trim().length > 0)
      || /https?:\/\/[^\s<>]+/i.test(responseText);
    if (test.requiresWeb && !evidenceCitationPresent) {
      issues.push('Evidence: Missing citations for web-required question');
    }

    const researchContextPreserved = test.category === 'research' && agentPath.includes('research') && !faqHandled;

    return { issues, researchContextPreserved, evidenceCitationPresent };
  }

  private calculateKpis(): KpiSummary {
    const latencies = this.results.map(r => r.latencyMs).sort((a, b) => a - b);
    const p95 = latencies[Math.floor(latencies.length * 0.95)] || 0;
    const passed = this.results.filter(r => r.success).length;

    return {
      totalTests: this.results.length,
      passedTests: passed,
      failedTests: this.results.length - passed,
      avgLatencyMs: Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) || 0,
      p95LatencyMs: p95,
      researchContextPreservation: this.calcRate(this.results.filter(r => r.category === 'research'), r => !!r.researchContextPreserved),
      faqAccuracy: this.calcRate(this.results.filter(r => r.category === 'faq'), r => r.success),
      dataQueryAccuracy: this.calcRate(this.results.filter(r => r.category === 'data_query'), r => r.success),
      helpfulRate: this.calcRate(this.results, r => r.success && r.issues.length === 0),
      // Neither safety nor follow-up resolution is evaluated by this runner.
      noFollowUpResolutionRate: null,
      safetyPassRate: null,
      evidenceCoverage: this.calcRate(this.results.filter(r => r.requiresWeb), r => r.evidenceCitationPresent === true)
    };
  }

  private calcRate(subset: TestResult[], predicate: (r: TestResult) => boolean): number | null {
    if (subset.length === 0) return null;
    return Math.round((subset.filter(predicate).length / subset.length) * 100);
  }

  private calculateStratifiedSummary(): StratifiedSummary {
    const group = (keyFn: (r: TestResult) => string) => {
      const groups = new Map<string, TestResult[]>();
      this.results.forEach(r => {
        const k = keyFn(r) || 'unknown';
        if (!groups.has(k)) groups.set(k, []);
        groups.get(k)!.push(r);
      });
      return Array.from(groups.entries()).map(([key, group]): GroupMetric => {
        const latencies = group.map(r => r.latencyMs).sort((a, b) => a - b);
        const p = group.filter(r => r.success).length;
        return {
          key,
          total: group.length,
          passed: p,
          failed: group.length - p,
          successRate: Math.round((p / group.length) * 100),
          avgLatencyMs: Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length),
          p95LatencyMs: latencies[Math.floor(latencies.length * 0.95)] || 0
        };
      });
    };

    return {
      byQuestionSet: group(r => r.questionSet),
      byPersona: group(r => r.persona || 'none'),
      byRawCategory: group(r => r.rawCategory),
      byMappedCategory: group(r => r.category),
      byIntent: group(r => r.intent || 'unknown'),
      byRequiresWeb: group(r => r.requiresWeb ? 'web' : 'local')
    };
  }

  private generateStructuredOutput(kpis: KpiSummary, stratified: StratifiedSummary, durationMs: number, questionSet: string, tier: string): DogfoodingOutput {
    const failedTests = this.results.filter(r => !r.success);
    return {
      metadata: {
        runId: `bench-${Date.now()}`,
        timestamp: new Date().toISOString(),
        environment: this.config.targetUrl || this.config.provider || 'direct',
        user: 'bench-user',
        questionSet,
        durationMs,
        tier
      },
      scope: {},
      kpiSummary: kpis,
      stratified,
      qualityGates: [],
      triage: {
        highSeverity: 0,
        mediumSeverity: 0,
        lowSeverity: 0,
        items: failedTests.map(t => ({
          testId: t.testId,
          issue: t.issues.join(', ')
        }))
      },
      results: this.results,
      recommendation: kpis.passedTests / kpis.totalTests >= 0.8 ? 'promote' : 'hold',
      topIssues: failedTests.slice(0, 3).map(t => `${t.testId}: ${t.issues[0]}`),
      insights: []
    };
  }
}
