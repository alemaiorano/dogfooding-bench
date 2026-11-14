const { test } = require('node:test');
const assert = require('node:assert/strict');
const axios = require('axios');
const fs = require('node:fs');
const path = require('node:path');
const { BenchmarkRunner } = require(process.env.BENCH_RUNNER || '../dist/runner');

async function runFixture(responder, questions, runner = new BenchmarkRunner({targetUrl:'http://localhost:1'})) {
  const dir = fs.mkdtempSync(path.join(__dirname, '../node_modules/bench-test-'));
  const dataset = path.join(dir, 'dataset.json');
  fs.writeFileSync(dataset, JSON.stringify({questions}));
  const original = axios.default.post;
  axios.default.post = responder;
  try { return await runner.run(dataset); }
  finally { axios.default.post = original; fs.rmSync(dir, {recursive:true, force:true}); }
}
const question = (id, requiresWeb) => ({id, text:'Give an answer', category:'faq', requiresWeb});
const response = (text, agentPath=[]) => ({data:{data:{response:{text}, metadata:{agentPath}}}});

test('web requirements survive results and failed requests; keyword alone is no citation', async () => {
  const questions = [question('a',true),question('b',true),question('c',false)];
  let call=0;
  const output = await runFixture(async () => {
    if (++call === 2) throw new Error('offline transport fixture');
    return response('Nenhuma fonte foi encontrada');
  },questions);
  assert.deepEqual(output.results.map(r=>r.requiresWeb),[true,true,false]);
  assert.equal(output.kpiSummary.evidenceCoverage,0);
  assert.equal(output.stratified.byRequiresWeb.find(g=>g.key==='web').total,2);
  assert.equal(output.kpiSummary.safetyPassRate,null);
  assert.equal(output.kpiSummary.noFollowUpResolutionRate,null);
});
test('citation coverage is independent of task success and not evidence validity', async () => {
  const output=await runFixture(async()=>response('https://example.invalid/citation '+'x'.repeat(3100)),[question('a',true)]);
  assert.equal(output.results[0].success,false);
  assert.equal(output.kpiSummary.evidenceCoverage,100);
});
test('structured source ID counts even without a URL', async () => {
  const output=await runFixture(async()=>({data:{data:{response:{text:'An answer with evidence',sources:[{id:'source-1'}]}}}}),[question('a',true)]);
  assert.equal(output.kpiSummary.evidenceCoverage,100);
});
test('empty subsets are not evaluated, including an empty dataset', async () => {
  const output=await runFixture(async()=>response('An ordinary answer'),[question('a',false)]);
  assert.equal(output.kpiSummary.evidenceCoverage,null);
  assert.equal(output.kpiSummary.researchContextPreservation,null);
  const empty=await runFixture(async()=>{throw Error('must not call')},[]);
  assert.equal(empty.kpiSummary.helpfulRate,null);
  assert.equal(empty.recommendation,'hold');
});
test('blocked routes and normal routes both leave safety unevaluated', async () => {
  for (const route of [[],['blocked'],['normal']]) {
    const output=await runFixture(async()=>response('A response',route),[question('a',false)]);
    assert.equal(output.kpiSummary.safetyPassRate,null);
  }
});
test('reusing a runner does not include prior runs', async () => {
  const runner=new BenchmarkRunner({targetUrl:'http://localhost:1'});
  await runFixture(async()=>response('First answer'),[question('a',true)],runner);
  const next=await runFixture(async()=>response('Second answer'),[question('b',false)],runner);
  assert.equal(next.kpiSummary.totalTests,1);
  assert.equal(next.kpiSummary.evidenceCoverage,null);
});

test('JSON serialization leaks are rejected', async () => {
  const output=await runFixture(async()=>response('[object Object]'),[question('leak',false)]);
  assert.equal(output.results[0].success,false);
  assert.ok(output.results[0].issues.includes('Response: JSON leak detected'));
});
test('a single-question object is executed rather than silently skipped', async () => {
  const runner=new BenchmarkRunner({targetUrl:'http://localhost:1'});
  assert.equal(runner.filterQuestions(question('single',false),[], 'smoke').length,1);
});
