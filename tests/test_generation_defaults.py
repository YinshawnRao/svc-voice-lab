"""User-facing single output defaults and explicit historical comparison compatibility."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import listening_page
import run_stage2_poc


class GenerationContract(unittest.TestCase):
    def invoke_prepared(self, extra):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();clips=root/'work/clips';clips.mkdir(parents=True)
            for name in ['source_vocals.wav','source_accompaniment.wav','target_reference_1.wav']:
                (clips/name).touch()
            argv=['run_stage2_poc','--run-id','example','--clips',str(clips),'--evidence-dir',str(root/'reports/evidence/test'),*extra]
            with patch.object(run_stage2_poc,'ROOT',root),patch.object(sys,'argv',argv),patch.object(run_stage2_poc.subprocess,'run') as run,patch('builtins.print'):
                run_stage2_poc.main()
            commands=[c.args[0] for c in run.call_args_list]
            convert=next(c for c in commands if 'scripts/seed_vc_local.py' in c)
            return convert[convert.index('--steps')+1:convert.index('--device')]

    def test_default_invocation_requests_only_30_steps(self):
        self.assertEqual(self.invoke_prepared([]),['30'])

    def test_explicit_comparison_remains_available(self):
        self.assertEqual(self.invoke_prepared(['--steps','30','50']),['30','50'])

    def page(self, labels):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();inputs=root/'inputs';inputs.mkdir();dest=root/'output';dest.mkdir()
            for name in ['source.wav','target.wav','original.wav']:(inputs/name).touch()
            manifest={'display_title':'音色 · A/B 对比','original_mix_path':str(inputs/'original.wav'),
                      'reference_note':'本轮两版都使用同一参考。','target_artist':'测试歌手','target_song':'测试歌曲'}
            (inputs/'manifest.json').write_text(json.dumps(manifest))
            rows=[]
            for label,steps in labels:
                dry=dest/(label+'-dry.wav');mix=dest/(label+'-mix.wav');dry.touch();mix.touch()
                rows.append({'label':label,'steps':steps,'dry_path':str(dry),'mix_path':str(mix)})
            run={'source':str(inputs/'source.wav'),'target':str(inputs/'target.wav')}
            with patch.object(listening_page,'ROOT',root):listening_page.write_page(dest,run,{'variants':rows})
            html=(dest/'listen.html').read_text()
            tracks=json.loads(re.search(r'const tracks=(\[.*?\]);',html).group(1))
            for track in tracks:self.assertTrue((dest/track['url']).is_file())
            return html,tracks

    def test_single_page_has_one_mix_and_one_dry_without_ab_copy(self):
        html,tracks=self.page([('single',30)])
        self.assertEqual([t['label'] for t in tracks],['AI 混音','原唱 · 同一片段','源人声 · 无伴奏','AI 纯人声'])
        for old in ['A/B','两版','两组','50 步']:self.assertNotIn(old,html)
        self.assertIn('测试歌手《测试歌曲》',html)

    def test_explicit_comparison_page_keeps_both_outputs(self):
        html,tracks=self.page([('A',30),('B',50)])
        self.assertEqual([t['id'] for t in tracks],['A','B','original','source','A-dry','B-dry'])
        self.assertIn('A：30 步 / B：50 步',html)


if __name__=='__main__':unittest.main()
