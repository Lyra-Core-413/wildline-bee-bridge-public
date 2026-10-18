"""Fictional single-observation integration tests; never contact Bee."""
import importlib.util
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('h5_test',ROOT/'real/h5_sidecar.py')
class SingleContractTests(unittest.TestCase):
    def capture(self):return json.loads((ROOT/'real/fixtures/A.json').read_bytes())
    def single(self,c):
        self.assertTrue(callable(getattr(h,'project_single',None)),'Missing single-observation projection')
        return h.project_single(c)
    def test_single_projection_exists_without_duplication(self):
        self.assertTrue(callable(getattr(h,'project_single',None)),
            'H5 needs a separate single-observation projection; pair contracts must stay intact')
    def test_one_record_no_comparison_or_no_change_claim(self):
        c=self.capture();v=self.single(c)
        self.assertEqual(v['observation'],c);self.assertEqual(v['observation_count'],1)
        self.assertEqual(v['change_status'],'NOT_ASSESSED_SINGLE_OBSERVATION')
        self.assertNotIn('original',v);self.assertNotIn('latest',v);self.assertNotIn('changes',v)
        self.assertNotIn('No meaningful',v['answer']);self.assertEqual(v['authority'],'NONE')
    def test_unknown_confirmation_not_inferred(self):
        c=self.capture();del c['confirmed'];v=self.single(c)
        self.assertIn('not provided',v['answer']);self.assertIn('one observation',' '.join(v['uncertainty']).lower())
    def test_single_does_not_accept_stage_b(self):
        c=self.capture();c['stage']='B'
        self.assertTrue(callable(getattr(h,'project_single',None)))
        with self.assertRaises(h.Stop):h.project_single(c)

class BridgeTests(unittest.TestCase):
    def modules(self):
        for name in ('private_work','process_control','single_bridge','single_reader'):
            self.assertTrue((ROOT/(name+'.py')).is_file(),'Missing bounded component: '+name)
        import single_bridge as bridge
        return bridge
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='wildline-fictional-bridge-')
        self.addCleanup(self.temp.cleanup);self.out=Path(self.temp.name)/'private-work'
    def test_exact_consent_includes_capture_and_recovery(self):
        bridge=self.modules();b=bridge.b
        self.assertEqual(b.consent_line(42),'READ CAPTURE AND RECOVER FACT 42 FIELDS id,text,confirmed,created_at')
    def test_decline_creates_no_private_data_and_never_resolves_cli(self):
        bridge=self.modules();resolve=Mock();transport=Mock()
        with self.assertRaisesRegex(bridge.b.Stop,'CONSENT_REQUIRED'):
            bridge.execute(42,self.out,confirm=lambda _:'NO',resolve=resolve,transport=transport)
        resolve.assert_not_called();transport.assert_not_called();self.assertFalse(self.out.exists())
    def test_mock_cli_to_real_fresh_process_outside_package(self):
        bridge=self.modules();before={p:p.read_bytes() for p in ROOT.rglob('*') if p.is_file()}
        r=bridge.offline_demo(self.out)
        self.assertNotEqual(r['acquisition_pid'],r['reader_pid']);self.assertEqual(r['observation_count'],1)
        self.assertEqual(r['view']['change_status'],'NOT_ASSESSED_SINGLE_OBSERVATION')
        self.assertEqual(r['acquisition_kind'],'MOCKED_IMPLEMENTATION_TEST')
        self.assertEqual(r['before_reader'],r['after_reader']);self.assertEqual(r['view']['authority'],'NONE')
        self.assertTrue(Path(r['operation']).is_relative_to(self.out));self.assertFalse(Path(r['operation']).is_relative_to(ROOT))
        self.assertFalse((Path(r['operation'])/'PAIR.json').exists())
        self.assertEqual(before,{p:p.read_bytes() for p in ROOT.rglob('*') if p.is_file()})
    def test_reader_failure_removes_data_and_success_artifacts(self):
        bridge=self.modules()
        with patch.object(bridge,'recover',side_effect=bridge.b.Stop('READER_FAILED')):
            with self.assertRaisesRegex(bridge.b.Stop,'READER_FAILED'):bridge.offline_demo(self.out)
        folder=next(self.out.iterdir())
        self.assertEqual({p.name for p in folder.iterdir()},{'attempt.json','failure.json'})
        self.assertEqual(json.loads((folder/'failure.json').read_bytes())['status'],'FAILED')
    def test_interruption_after_capture_leaves_no_success(self):
        bridge=self.modules()
        with patch.object(bridge,'recover',side_effect=KeyboardInterrupt):
            with self.assertRaisesRegex(bridge.b.Stop,'INTERRUPTED'):bridge.offline_demo(self.out)
        folder=next(self.out.iterdir());self.assertEqual({p.name for p in folder.iterdir()},{'attempt.json','failure.json'})
    def test_private_root_inside_repository_or_package_refused(self):
        bridge=self.modules();import private_work as p
        with self.assertRaises(ValueError):p.check_root(ROOT/'data')
        repo=Path(self.temp.name)/'repo';repo.mkdir();(repo/'.git').mkdir()
        with self.assertRaises(ValueError):p.check_root(repo/'private')
    def test_existing_unprotected_root_refused_without_changing_acl(self):
        self.out.mkdir();bridge=self.modules();import private_work as p
        with self.assertRaises(ValueError):p.make_root(self.out)
    def test_noninteractive_live_refuses_before_cli_or_private_output(self):
        self.modules()
        p=subprocess.run([sys.executable,'-X','utf8','-I','-B',str(ROOT/'single_bridge.py'),
           '--live-read','--fact-id','42','--private-root',str(self.out)],cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,2);self.assertIn('INTERACTIVE_CONSENT_REQUIRED',p.stderr)
        self.assertFalse(self.out.exists());self.assertEqual(p.stdout,'')
    def test_actual_recovered_answer_is_displayed_with_qualification(self):
        bridge=self.modules();messages=[];r=bridge.offline_demo(self.out,emit=messages.append)
        self.assertEqual(messages,[bridge.display(r)])
        self.assertIn(r['view']['answer'],messages[0]);self.assertIn('MOCKED OFFLINE',messages[0])
        self.assertIn('CLAIMED_UNVERIFIED',messages[0]);self.assertIn('Uncertainty:',messages[0])
        self.assertIn('Authority: NONE',messages[0])
        self.assertNotIn('FICTIONAL_UNSELECTED_FIELD',messages[0])
    def test_unknown_confirmation_survives_fresh_process(self):
        bridge=self.modules()
        raw=b'{"id":42,"text":"Fictional unknown-confirmation observation"}'
        from datetime import datetime,timezone
        r=bridge.execute(42,self.out,confirm=lambda _:bridge.b.consent_line(42),
            resolve=lambda:{'path':'mock','sha256':'MOCKED'},
            transport=lambda *_:(raw,datetime.now(timezone.utc),{'transport':'MOCKED_IMPLEMENTATION_TEST','cli_invocations':1}))
        self.assertNotIn('confirmed',r['view']['observation']);self.assertIn('not provided',r['view']['answer'])
    def test_cli_failures_never_recover_or_persist_raw_content(self):
        bridge=self.modules();b=bridge.b
        class Fake:
            def __init__(self,out,err,code):self.stdout=io.BytesIO(out);self.stderr=io.BytesIO(err);self.returncode=code
            def wait(self,timeout=None):return self.returncode
            def kill(self):pass
        cases=[(b'',b'401 FICTIONAL_PRIVATE_DIAGNOSTIC',1,'CLI_AUTHENTICATION_REQUIRED'),
               (b'{',b'',0,'INVALID_JSON'),
               (b'{"id":43,"text":"FICTIONAL_PRIVATE_CONTENT"}',b'',0,'FACT_ID_MISMATCH'),
               (b'{"id":42,"text":"password=FICTIONAL_PRIVATE_CONTENT"}',b'',0,'SELECTED_TEXT_REQUIRES_PRIVACY_REVIEW')]
        for n,(out,err,status,reason) in enumerate(cases):
            root=Path(self.temp.name)/('private-'+str(n));launcher=Mock(return_value=Fake(out,err,status))
            with patch.object(bridge,'recover') as reader:
                with self.assertRaisesRegex(b.Stop,reason):
                    bridge.execute(42,root,confirm=lambda _:b.consent_line(42),resolve=lambda:{'path':'mock','sha256':'MOCKED'},
                        transport=lambda exe,value:b.collect(exe,value,popen=launcher))
                reader.assert_not_called();self.assertEqual(launcher.call_count,1)
            folder=next(root.iterdir());self.assertEqual({p.name for p in folder.iterdir()},{'attempt.json','failure.json'})
            self.assertNotIn(b'FICTIONAL_PRIVATE',b''.join(p.read_bytes() for p in folder.iterdir()))
    def test_tampered_capture_seal_or_receipt_fail_closed(self):
        bridge=self.modules();original=bridge.recover
        for name in ('capture.json','receipt.json','SINGLE.json','STATE.json'):
            root=Path(self.temp.name)/('private-'+name.split('.')[0])
            def tamper(folder,private_root,anchor):
                (folder/name).write_bytes(b'{}');return original(folder,private_root,anchor)
            with patch.object(bridge,'recover',side_effect=tamper):
                with self.assertRaisesRegex(bridge.b.Stop,'READER_FAILED'):bridge.offline_demo(root)
            folder=next(root.iterdir());self.assertEqual({p.name for p in folder.iterdir()},{'attempt.json','failure.json'})
    def test_second_reader_cannot_recover_consumed_operation(self):
        bridge=self.modules();r=bridge.offline_demo(self.out);folder=Path(r['operation'])
        before={p.name:p.read_bytes() for p in folder.iterdir()}
        with self.assertRaisesRegex(bridge.b.Stop,'READER_FAILED'):
            bridge.recover(folder,self.out,r['seal_sha256'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in folder.iterdir()})
    def test_reader_mutation_is_refused_and_cleanup_runs(self):
        bridge=self.modules();original=bridge.recover
        def mutate(folder,root,anchor):
            r=original(folder,root,anchor);(folder/'capture.json').write_bytes(b'{}');return r
        with patch.object(bridge,'recover',side_effect=mutate):
            with self.assertRaisesRegex(bridge.b.Stop,'READER_MUTATED_EVIDENCE'):bridge.offline_demo(self.out)
        self.assertEqual({p.name for p in next(self.out.iterdir()).iterdir()},{'attempt.json','failure.json'})
    def test_false_recovered_result_is_refused(self):
        bridge=self.modules();original=bridge.recover
        def fake(folder,root,anchor):
            r=original(folder,root,anchor);r['view']['authority']='WRITE';return r
        with patch.object(bridge,'recover',side_effect=fake):
            with self.assertRaisesRegex(bridge.b.Stop,'RECOVERED_RESULT_MISMATCH'):bridge.offline_demo(self.out)
        self.assertFalse(any(self.out.rglob('COMPLETE.json')))
    def test_display_interruption_leaves_no_success_or_selected_content(self):
        bridge=self.modules()
        with self.assertRaisesRegex(bridge.b.Stop,'INTERRUPTED'):
            bridge.offline_demo(self.out,emit=Mock(side_effect=KeyboardInterrupt))
        folder=next(self.out.iterdir());self.assertEqual({p.name for p in folder.iterdir()},{'attempt.json','failure.json'})
    def test_cleanup_failure_is_stop_never_success(self):
        bridge=self.modules()
        with (patch.object(bridge,'recover',side_effect=bridge.b.Stop('READER_FAILED')),
              patch.object(Path,'unlink',side_effect=PermissionError('fictional inaccessible artifact'))):
            with self.assertRaisesRegex(bridge.b.Stop,'CLEANUP_UNVERIFIED'):bridge.offline_demo(self.out)
        self.assertFalse(any(self.out.rglob('COMPLETE.json')))
    def test_reader_network_and_outside_file_capabilities_denied(self):
        self.modules()
        p=subprocess.run([sys.executable,'-I','-B',str(ROOT/'reader_capability_probe.py'),str(self.out)],
             cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout),{'network_denied':True,'outside_file_denied':True})
    def test_interrupt_on_capture_return_still_cleans_selected_data(self):
        bridge=self.modules();original=bridge.b.read_once
        def interrupted(*args,**kwargs):original(*args,**kwargs);raise KeyboardInterrupt
        with patch.object(bridge.b,'read_once',side_effect=interrupted):
            with self.assertRaisesRegex(bridge.b.Stop,'INTERRUPTED'):bridge.offline_demo(self.out)
        self.assertEqual({p.name for p in next(self.out.iterdir()).iterdir()},{'attempt.json','failure.json'})
    def test_mapped_or_nonfixed_drive_refused_before_filesystem_read(self):
        self.modules();import private_work as p
        self.assertTrue(callable(getattr(p,'drive_type',None)),'Missing fixed-local-drive guard')
        with patch.object(p,'drive_type',return_value=4),patch.object(p,'_no_links') as links:
            with self.assertRaisesRegex(ValueError,'PRIVATE_PATH_UNSAFE'):p.check_root(self.out)
            links.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
