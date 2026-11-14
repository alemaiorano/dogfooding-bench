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
