#!/usr/bin/env ts-node
import { BenchmarkRunner, RunnerConfig } from './runner';
import * as path from 'path';
import * as fs from 'fs';

async function main() {
  const args = process.argv.slice(2);
  
  const targetUrl = args.find(a => a.startsWith('--target='))?.split('=')[1];
  const apiKey = args.find(a => a.startsWith('--key='))?.split('=')[1] || process.env.API_KEY || process.env.OPENAI_API_KEY || process.env.GEMINI_API_KEY;
  const provider = (args.find(a => a.startsWith('--provider='))?.split('=')[1] || 'custom') as RunnerConfig['provider'];
  const model = args.find(a => a.startsWith('--model='))?.split('=')[1];
  const datasetPath = args.find(a => a.startsWith('--dataset='))?.split('=')[1] || path.join(__dirname, 'dataset.json');
  const tier = args.find(a => a.startsWith('--tier='))?.split('=')[1] || 'smoke';

  if (!fs.existsSync(datasetPath)) {
    console.error(`❌ Dataset not found at: ${datasetPath}`);
    process.exit(1);
  }

  if (!apiKey && provider !== 'custom') {
    console.error(`❌ API Key is required for provider: ${provider}. Use --key or export OPENAI_API_KEY/GEMINI_API_KEY`);
    process.exit(1);
  }

  const config: RunnerConfig = {
    targetUrl: targetUrl || (provider === 'custom' ? 'http://localhost:3001/api/v2/chat' : undefined),
    apiKey,
    provider,
    model
  };

  const runner = new BenchmarkRunner(config);
  
  try {
    const output = await runner.run(datasetPath, ['v2'], tier);
    
    console.log('\n' + '='.repeat(60));
    console.log('📊 BENCHMARK COMPLETE');
    console.log('='.repeat(60));
    console.log(`Total: ${output.kpiSummary.totalTests} | ✅ ${output.kpiSummary.passedTests} | ❌ ${output.kpiSummary.failedTests}`);
    console.log(`Success Rate: ${Math.round((output.kpiSummary.passedTests / output.kpiSummary.totalTests) * 100)}%`);
    console.log(`P95 Latency: ${output.kpiSummary.p95LatencyMs}ms`);
    console.log(`Recommendation: ${output.recommendation.toUpperCase()}`);
    console.log('='.repeat(60));

    const outputPath = path.join(process.cwd(), `bench-results-${Date.now()}.json`);
    fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
    console.log(`📄 Detailed results saved to: ${outputPath}`);

  } catch (error) {
    console.error('❌ Benchmark failed:', error);
    process.exit(1);
  }
}

main();
