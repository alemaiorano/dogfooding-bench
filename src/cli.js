#!/usr/bin/env ts-node
"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const runner_1 = require("./runner");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
async function main() {
    const args = process.argv.slice(2);
    const targetUrl = args.find(a => a.startsWith('--target='))?.split('=')[1];
    const apiKey = args.find(a => a.startsWith('--key='))?.split('=')[1] || process.env.API_KEY || process.env.OPENAI_API_KEY || process.env.GEMINI_API_KEY;
    const provider = (args.find(a => a.startsWith('--provider='))?.split('=')[1] || 'custom');
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
    const config = {
        targetUrl: targetUrl || (provider === 'custom' ? 'http://localhost:3001/api/v2/chat' : undefined),
        apiKey,
        provider,
        model
    };
    const runner = new runner_1.BenchmarkRunner(config);
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
    }
    catch (error) {
        console.error('❌ Benchmark failed:', error);
        process.exit(1);
    }
}
main();
//# sourceMappingURL=cli.js.map