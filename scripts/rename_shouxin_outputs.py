#!/usr/bin/env python3
"""Apply the user-requested directory name after generation and validation finish."""
import datetime as dt
import json
from common import ROOT
from download import hash_file
from run_seven_experiment import dump, page
from extend_shouxin_experiment import EVIDENCE, load, save, validate


def main():
    c = load('shouxin')
    before = json.loads((EVIDENCE/'final-validation.json').read_text())
    assert c['status']=='POC_PASSED' and before['status']=='PASSED'
    old = 'outputs/stage14-shouxin'
    new = 'outputs/stage14-seven-shouxindetaiyang'
    assert c['output_directory']==old and not (ROOT/new).exists()
    files = [{'relative_path':str(p.relative_to(ROOT/old)), 'size_bytes':p.stat().st_size,
              'sha256':hash_file(p)} for p in sorted((ROOT/old).rglob('*')) if p.is_file()]
    dump(EVIDENCE/'output-tree-before-relocation.json',files)
    dump(EVIDENCE/'manifest-before-relocation.json',c)
    (ROOT/old).rename(ROOT/new)
    for row in files:
        p = ROOT/new/row['relative_path']
        assert p.stat().st_size==row['size_bytes'] and hash_file(p)==row['sha256']
    relocation = {'from':old, 'to':new, 'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'authorization':'用户要求目录名带seven且歌名拼音完整；全部生成完成后统一迁移。',
        'actual_converted_singers':6, 'original_artist_excluded':'张韶涵',
        'files_moved_without_content_change':len(files),
        'historical_run_metadata':'run/evaluation/mix receipts and stage14 config retain paths at generation; replace the from prefix with the to prefix to locate current output files.',
        'inventory':'reports/evidence/stage15/output-tree-before-relocation.json',
        'pre_move_manifest':'reports/evidence/stage15/manifest-before-relocation.json'}
    dump(EVIDENCE/'output-relocation.json',relocation)
    c['output_directory']=new
    c['output_relocation']={'from':old,'to':new,'evidence':'reports/evidence/stage15/output-relocation.json'}
    for a in c['artists']:
        for row in a['deliverables'].values():
            assert row['path'].startswith(old+'/')
            row['path']=new+row['path'][len(old):]
    save('shouxin',c)
    page(c)
    # Keep historical evidence immutable; refresh only current navigation and this extension's report.
    for name in ('README.md','config/status.json','reports/06_summary.md',
                 'reports/22_preparation.md','reports/22_shouxin.md'):
        p=ROOT/name
        p.write_text(p.read_text().replace(old+'/',new+'/'))
    for row in files:
        if row['relative_path'] in ('manifest.json','listen.html'):continue
        p=ROOT/new/row['relative_path']
        assert p.stat().st_size==row['size_bytes'] and hash_file(p)==row['sha256']
    assert not (ROOT/old).exists()
    validate('post-relocation-validation.json')
    print('Renamed and revalidated:',ROOT/new)


if __name__=='__main__':
    main()
