const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
test('replication means match the preserved 38-run CSV',()=>{
  const raw=fs.readFileSync(path.join(__dirname,'../data/decision-log.csv'),'utf8').trim().split(/\r?\n/);
  const parse=line=>line.match(/("[^"]*"|[^,]*)(,|$)/g).filter(x=>x.length).map(x=>x.replace(/,$/,'').replace(/^"|"$/g,''));
  const header=parse(raw.shift());
  const rows=raw.map(parse);
  assert.equal(rows.length,38);
  const mean=key=>rows.reduce((s,r)=>s+parseFloat(r[header.indexOf(key)]),0)/rows.length;
  assert.equal((mean('P95_Latency')/1000).toFixed(2),'11.54');
  assert.equal(mean('Safety_Rate').toFixed(1),'97.1');
  assert.equal(mean('Success_Rate').toFixed(1),'97.9');
  const guide=fs.readFileSync(path.join(__dirname,'../REPLICATION.md'),'utf8');
  assert.match(guide,/11\.54s/);assert.match(guide,/97\.1%/);
});
