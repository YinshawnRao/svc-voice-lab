// Logic-only validation; this does not claim browser or human audio QA.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const body = fs.readFileSync(process.argv[2], 'utf8');
const code = body.match(/<script>([\s\S]*?)<\/script>/)[1];
const ids = [...body.matchAll(/data-track="([^"]+)"/g)].map(x => x[1]);
const buttons = ids.map(id => ({dataset:{track:id},classList:{toggle(){}},addEventListener(){}}));
const elements = {now:{textContent:''},error:{textContent:''},restart:{addEventListener(){}}};
const player = {currentTime:0,duration:200,pause(){},play(){return Promise.resolve()},
  load(){this.currentTime=0;this.duration=this.src.includes('参考')?15:200;this.onloadedmetadata()},addEventListener(){}};
elements.player = player;
const context = {document:{getElementById:id=>elements[id],querySelectorAll:()=>buttons}};
vm.createContext(context);vm.runInContext(code,context);
const choose = (id, restart=false) => vm.runInContext(`choose(${JSON.stringify(id)},${restart})`,context);
const mixes=ids.filter(x=>x.endsWith('-mix')),dry=ids.find(x=>x.endsWith('-dry')),ref=ids.find(x=>x.endsWith('-reference'));
assert(mixes.length>=2 && dry && ref);
choose(mixes[0]);assert.equal(player.currentTime,0);player.currentTime=11.2;
for(const id of mixes){choose(id);assert.equal(player.currentTime,11.2)}
choose(ref);assert.equal(player.currentTime,0);player.currentTime=5;
choose(dry);assert.equal(player.currentTime,11.2);
choose('original');assert.equal(player.currentTime,11.2);
choose(dry,true);assert.equal(player.currentTime,0);
console.log(JSON.stringify({status:'PASSED',method:'Node mock DOM; no browser or human audition',
  mix_tracks:mixes.length,same_position_switching:true,reference_restore:true,restart:true}));
