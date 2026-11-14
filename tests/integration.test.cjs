const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const {spawn,spawnSync}=require('node:child_process');
const root=path.join(__dirname,'..');
const extractor=path.join(root,'data/extract_metrics.py');
function scratch(){return fs.mkdtempSync(path.join(root,'node_modules/integration-'));}
function extract(dir){
 const result=spawnSync('python3',[extractor],{cwd:dir,encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);
 assert.doesNotMatch(result.stdout,/Error parsing/);
 return fs.readFileSync(path.join(dir,'decision-log.csv'),'utf8');
}
test('CLI runs a single question through HTTP and its nullable output survives extraction',async()=>{
 const dir=scratch(); let requests=0;
 const server=http.createServer((req,res)=>{
   requests++;
   assert.equal(req.url,'/message');
   assert.equal(req.headers.authorization,'Bearer offline-fixture');
   res.setHeader('Content-Type','application/json');
   res.end(JSON.stringify({data:{response:{text:'An ordinary response'},metadata:{}}}));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try {
   const file=path.join(dir,'question.json');
   fs.writeFileSync(file,JSON.stringify({id:'single',message:'Hello fixture',category:'faq'}));
   const cli=process.env.BENCH_RUNNER?'src/cli.js':'dist/cli.js';
   const child=spawn(process.execPath,[path.join(root,cli),`--dataset=${file}`,`--target=http://127.0.0.1:${server.address().port}`,'--key=offline-fixture'],{cwd:dir});
   let logs='';child.stdout.on('data',x=>logs+=x);child.stderr.on('data',x=>logs+=x);
   const code=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve);});
   assert.equal(code,0,logs); assert.equal(requests,1);
   const output=fs.readdirSync(dir).find(f=>f.startsWith('bench-results-'));
   const parsed=JSON.parse(fs.readFileSync(path.join(dir,output),'utf8'));
   assert.equal(parsed.kpiSummary.totalTests,1);
   assert.equal(parsed.results[0].success,true);
   fs.mkdirSync(path.join(dir,'evaluation-traces'));
   fs.copyFileSync(path.join(dir,output),path.join(dir,'evaluation-traces/result.json'));
   const csv=extract(dir);
   assert.match(csv,/,HOLD\r?\n/);assert.doesNotMatch(csv,/None|null|100%/);
 } finally {await new Promise(resolve=>server.close(resolve));fs.rmSync(dir,{recursive:true,force:true});}
});
test('extractor preserves all historical rows and decisions',()=>{
 const dir=scratch();
 try {
   fs.symlinkSync(path.join(root,'data/evaluation-traces'),path.join(dir,'evaluation-traces'),'dir');
   extract(dir);
   const script=`import csv,sys\na=list(csv.DictReader(open(sys.argv[1])))\nb=list(csv.DictReader(open(sys.argv[2])))\nassert len(a)==len(b)==38\na.sort(key=lambda r:r['Run_ID']);b.sort(key=lambda r:r['Run_ID'])\nassert a==b, 'historical rows changed'\n`;
   const compared=spawnSync('python3',['-c',script,path.join(root,'data/decision-log.csv'),path.join(dir,'decision-log.csv')],{encoding:'utf8'});
   assert.equal(compared.status,0,compared.stderr);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('unknown safety does not override a demonstrated rollback',()=>{
 const dir=scratch();
 try {
   fs.mkdirSync(path.join(dir,'evaluation-traces'));
   fs.writeFileSync(path.join(dir,'evaluation-traces/failure.json'),JSON.stringify({kpiSummary:{totalTests:1,passedTests:0,safetyPassRate:null,researchContextPreservation:null,evidenceCoverage:null}}));
   assert.match(extract(dir),/,ROLLBACK\r?\n/);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});

test('empty CLI run remains N/A and HOLD through JSON and CSV; measured zero is distinct',async()=>{
 const dir=scratch();let requests=0;
 const server=http.createServer((req,res)=>{
   requests++;res.setHeader('Content-Type','application/json');
   res.end(JSON.stringify({data:{response:{text:''},metadata:{}}}));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 async function execute(name,dataset){
   const runDir=path.join(dir,name);fs.mkdirSync(runDir);
   const file=path.join(runDir,'dataset.json');fs.writeFileSync(file,JSON.stringify(dataset));
   const cli=process.env.BENCH_RUNNER?'src/cli.js':'dist/cli.js';
   const child=spawn(process.execPath,[path.join(root,cli),`--dataset=${file}`,`--target=http://127.0.0.1:${server.address().port}`],{cwd:runDir});
   let logs='';child.stdout.on('data',x=>logs+=x);child.stderr.on('data',x=>logs+=x);
   const code=await new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',resolve);});assert.equal(code,0,logs);
   const output=fs.readdirSync(runDir).find(f=>f.startsWith('bench-results-'));
   const result=JSON.parse(fs.readFileSync(path.join(runDir,output),'utf8'));
   fs.mkdirSync(path.join(runDir,'evaluation-traces'));fs.copyFileSync(path.join(runDir,output),path.join(runDir,'evaluation-traces/result.json'));
   extract(runDir);
   const read=spawnSync('python3',['-c',"import csv,json;print(json.dumps(next(csv.DictReader(open('decision-log.csv')))))"],{cwd:runDir,encoding:'utf8'});
   assert.equal(read.status,0,read.stderr);
   return {result,logs,row:JSON.parse(read.stdout)};
 }
 try{
   const empty=await execute('empty',{questions:[]});assert.equal(requests,0);
   assert.equal(empty.result.kpiSummary.totalTests,0);
   assert.equal(empty.result.kpiSummary.successRate,null);
   assert.equal(empty.result.kpiSummary.avgLatencyMs,null);
   assert.equal(empty.result.kpiSummary.p95LatencyMs,null);
   assert.equal(empty.result.recommendation,'hold');
   assert.match(empty.logs,/Success Rate: N\/A/);assert.match(empty.logs,/P95 Latency: N\/A/);assert.doesNotMatch(empty.logs,/NaN|Success Rate: 0%/);
   for(const key of ['Success_Rate','Avg_Latency','P95_Latency','Duration_Per_Test_ms','Safety_Rate','Evidence_Coverage'])assert.equal(empty.row[key],'',key);
   assert.equal(empty.row.Decision,'HOLD');
   const failed=await execute('measured-zero',{questions:[{id:'measured',message:'An offline test',category:'faq'}]});
   assert.equal(requests,1);assert.equal(failed.result.kpiSummary.successRate,0);
   assert.match(failed.logs,/Success Rate: 0%/);assert.equal(failed.row.Success_Rate,'0.0%');assert.equal(failed.row.Decision,'ROLLBACK');
 }finally{await new Promise(resolve=>server.close(resolve));fs.rmSync(dir,{recursive:true,force:true});}
});
