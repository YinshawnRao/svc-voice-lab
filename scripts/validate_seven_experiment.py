#!/usr/bin/env python3
"""Validate the grouped audio, singer associations, shared playback and protected files."""
import json
import datetime as dt
from pathlib import Path
import re
import shutil
import subprocess
import numpy as np
import soundfile as sf
from common import ROOT, local_env
from download import hash_file, records, charged, reservations


def main():
    c=json.loads((ROOT/'config/experiments/seven-ruguoniyetingshuo.json').read_text())
    assert c['status']=='POC_PASSED' and len(c['artists'])==7
    dest=ROOT/c['output_directory'];ev=ROOT/'reports/evidence/stage9'
    assert json.loads((dest/'manifest.json').read_text())==c
    acquisitions=[c['source_acquisition_id']]+[a['acquisition_id'] for a in c['artists'] if 'acquisition_id' in a]
    for acquisition in acquisitions:
        receipt=json.loads((ROOT/'work/acquisition'/acquisition/'receipt.json').read_text())
        assert receipt['status']=='PASS'
        raw=ROOT/receipt['output']['data_path']
        assert raw.stat().st_size==receipt['output']['size_bytes'] and hash_file(raw)==receipt['output']['sha256']
    rows=[];source_hashes=set();ref_hashes=set();dry_hashes=set()
    for a in c['artists']:
        run=json.loads((dest/'runs'/a['key']/'run.json').read_text())
        evaluation=json.loads((dest/'runs'/a['key']/'evaluation.json').read_text())
        m=json.loads((ROOT/a['clips']/'manifest.json').read_text())
        assert (m['target_artist'],m['target_song'],m['source_song'])==(a['artist'],a['reference_song'],c['source_song'])
        assert run['requested_steps']==[30] and len(run['variants'])==1
        assert run['target_sha256']==a['reference_sha256']==hash_file(Path(run['target']))
        source_hashes.add(run['source_sha256']);ref_hashes.add(run['target_sha256'])
        assert json.loads((ev/f"{a['key']}-validation.json").read_text())['status']=='PASSED'
        for mode,row in a['deliverables'].items():
            path=ROOT/row['path'];assert hash_file(path)==row['sha256'] and path.stat().st_size==row['size_bytes']
            wave,sr=sf.read(path,always_2d=True);assert np.isfinite(wave).all() and np.max(np.abs(wave))>1e-5 and sr==44100
            if mode=='reference':
                assert len(wave)==15*sr and wave.shape[1]==1 and row['sha256']==run['target_sha256']
                continue
            assert path.parent==dest and path.name.endswith('_AI.wav')
            assert wave.shape[1]==(2 if mode=='mix' else 1)
            if mode=='mix':
                assert len(wave)==round(c['duration_seconds']*sr) and np.max(np.abs(wave))<=.981
                assert row['sha256']==evaluation['variants'][0]['mix_sha256']
            else:
                assert abs(len(wave)-round(c['duration_seconds']*sr))<=512
                assert row['sha256']==run['variants'][0]['sha256']!=run['source_sha256']
                dry_hashes.add(row['sha256'])
            rows.append({'artist':a['artist'],'mode':mode,**row,'duration_seconds':len(wave)/sr,'peak':float(np.max(np.abs(wave)))})
    assert len(source_hashes)==1 and len(ref_hashes)==7 and len(dry_hashes)==7
    assert len(list(dest.glob('*.wav')))==14
    document=(dest/'listen.html').read_text()
    tracks=json.loads(re.search(r'const tracks=(\[.*?\]);',document).group(1))
    assert len(tracks)==23 and len({t['url'] for t in tracks})==23
    assert 'A/B' not in document and 'https://' not in document and 'http://' not in document
    for t in tracks:
        assert (dest/t['url']).resolve().is_relative_to(dest) and (dest/t['url']).is_file()
    for href in re.findall(r'href="([^"]+)"',document):assert (dest/href).is_file()
    script=re.search(r'<script>(.*?)</script>',document,re.S).group(1)
    jsfile=ROOT/'work/stage9-player-check.js'
    jsfile.write_text('''const fs=require('fs'),vm=require('vm'),assert=require('assert');
const body=fs.readFileSync(process.argv[2],'utf8');const code=body.match(/<script>([\\s\\S]*?)<\\/script>/)[1];
const ids=[...body.matchAll(/data-track="([^"]+)"/g)].map(x=>x[1]);
const buttons=ids.map(id=>({dataset:{track:id},active:false,classList:{toggle(){}},addEventListener(){}}));
const elements={now:{textContent:''},error:{textContent:''},restart:{addEventListener(){}}};
const player={currentTime:0,duration:33.3,pause(){},play(){return Promise.resolve()},load(){this.currentTime=0;this.duration=this.src.includes('参考')?15:33.3;this.onloadedmetadata()},addEventListener(){}};
elements.player=player;const sandbox={document:{getElementById:id=>elements[id],querySelectorAll:()=>buttons}};vm.createContext(sandbox);vm.runInContext(code,sandbox);
vm.runInContext("choose('stefanie-mix')",sandbox);assert.equal(player.currentTime,0);player.currentTime=11.2;
for(const id of ids.filter(x=>x.endsWith('-mix'))){vm.runInContext('choose('+JSON.stringify(id)+')',sandbox);assert.equal(player.currentTime,11.2)}
vm.runInContext("choose('jolin-reference')",sandbox);assert.equal(player.currentTime,0);player.currentTime=5;
vm.runInContext("choose('rainie-dry')",sandbox);assert.equal(player.currentTime,11.2);
vm.runInContext("choose('rainie-dry',true)",sandbox);assert.equal(player.currentTime,0);
console.log(JSON.stringify({status:'PASSED',method:'Node mock DOM; no human/browser audition',track_buttons:ids.length,same_position_switching:true,reference_restore:true,restart:true}));
''')
    checked=subprocess.run(['node',str(jsfile),str(dest/'listen.html')],check=True,capture_output=True,text=True,env=local_env())
    player=json.loads(checked.stdout)
    before=json.loads((ev/'protected-before.json').read_text())
    for row in before:
        path=ROOT/row['path'];assert path.stat().st_size==row['size'] and hash_file(path)==row['sha256'],'Protected file changed'
    sizes={name:sum(p.stat().st_size for p in (ROOT/name).rglob('*') if p.is_file()) for name in ('work','outputs','data')}
    sizes['experiment']=sum(p.stat().st_size for p in dest.rglob('*') if p.is_file());sizes['disk_free']=shutil.disk_usage(ROOT).free
    result={'status':'PASSED','checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'audio':rows,'source_hashes':list(source_hashes),'unique_references':7,'unique_conversions':7,
        'protected_files_unchanged':len(before),'new_raw_inputs_verified':len(acquisitions),'player':player,'human_audition':False,'space_bytes':sizes,
        'download_budget':{'charged_bytes':charged(records()),'reserved_bytes':sum(reservations().values()),'limit_bytes':30000000000}}
    with (ev/'final-validation.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':'PASSED','final_audio_files':len(rows),'protected_files':len(before),'player':player,'space_bytes':sizes},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
