"""Isolated fictional acceptance/adversarial tests; never imports Core or Bee."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
APP = ROOT / 'h5_sidecar.py'
FIXTURES = ROOT / 'fixtures'


class H5Tests(unittest.TestCase):
    def setUp(self):
        (ROOT/'test-runs').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'test-runs')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.run = self.home/'pair'
        self.a = self.home/'A.json'; self.b = self.home/'B.json'
        self.a.write_bytes((FIXTURES/'A.json').read_bytes())
        self.b.write_bytes((FIXTURES/'B.json').read_bytes())

    def cli(self, *args):
        return subprocess.run([sys.executable,'-X','utf8','-I','-B',str(APP),
                               '--json',*map(str,args)],cwd=ROOT,
                              capture_output=True,text=True,encoding='utf-8',timeout=15)

    def capture(self, mode='synthetic', scope='DEMO/H5/synthetic', fact_id=900000001):
        return self.cli('acquire','--a',self.a,'--b',self.b,'--run',self.run,
                        '--mode',mode,'--scope',scope,'--fact-id',fact_id)

    def pair(self):
        r=self.capture(); self.assertEqual(r.returncode,0,r.stderr)
        return json.loads(r.stdout)

    def ask(self,pin):
        return self.cli('ask','--run',self.run,'--pair-sha256',pin)

    def edit(self, path, **changes):
        obj=json.loads(path.read_bytes());obj.update(changes)
        path.write_text(json.dumps(obj),encoding='utf-8')

    def denied(self, code):
        r=self.capture();self.assertEqual(r.returncode,2)
        self.assertEqual(r.stderr.strip(),'STOP: '+code)
        self.assertEqual(r.stdout,'');self.assertFalse(self.run.exists())

    def test_valid_pair_changes_and_preserves_a(self):
        r=self.pair();before=(self.run/'000001.json').read_bytes()
        answer=self.ask(r['pair_sha256']);self.assertEqual(answer.returncode,0,answer.stderr)
        v=json.loads(answer.stdout)['view']
        self.assertTrue(v['meaningful_change']);self.assertEqual(v['changes'],['text','confirmation'])
        self.assertEqual(v['authority'],'NONE');self.assertEqual(v['actions_taken'],[])
        self.assertEqual(v['original']['text'],json.loads(self.a.read_bytes())['text'])
        self.assertEqual(v['latest']['confirmed'],False)
        self.assertEqual(before,(self.run/'000001.json').read_bytes())

    def test_no_change_ignores_acquisition_clock(self):
        a=json.loads(self.a.read_bytes());self.edit(self.b,text=a['text'],confirmed=True)
        r=self.pair();v=json.loads(self.ask(r['pair_sha256']).stdout)['view']
        self.assertFalse(v['meaningful_change']);self.assertIn('No meaningful',v['answer'])

    def test_missing_confirmation_is_unknown_not_false(self):
        b=json.loads(self.b.read_bytes());del b['confirmed'];self.b.write_text(json.dumps(b))
        r=self.pair();v=json.loads(self.ask(r['pair_sha256']).stdout)['view']
        self.assertNotIn('confirmed',v['latest']);self.assertIn('not provided',v['answer'])

    def test_read_determinism_and_preservation(self):
        r=self.pair();before={p.name:p.read_bytes() for p in self.run.iterdir()}
        x=self.ask(r['pair_sha256']);y=self.ask(r['pair_sha256'])
        self.assertEqual(x.returncode,0);self.assertEqual(y.returncode,0)
        self.assertEqual(json.loads(x.stdout)['view'],json.loads(y.stdout)['view'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.run.iterdir()})

    def test_fresh_acquisition_and_reader_processes(self):
        r=self.cli('demo');self.assertEqual(r.returncode,0,r.stderr);x=json.loads(r.stdout)
        self.assertNotEqual(x['wrapper_pid'],x['acquisition_pid'])
        self.assertNotEqual(x['acquisition_pid'],x['reader_pid'])
        self.assertNotEqual(x['wrapper_pid'],x['reader_pid'])
        self.assertTrue(x['acquisition_exited_before_reader']);self.assertTrue(x['reader_preserved_evidence'])
        self.assertTrue(x['view']['meaningful_change']);self.assertEqual(x['view']['mode'],'synthetic')

    def test_missing_a(self): self.a.unlink();self.denied('INPUT_UNAVAILABLE')
    def test_missing_b(self): self.b.unlink();self.denied('INPUT_UNAVAILABLE')
    def test_different_ids(self): self.edit(self.b,fact_id=900000002);self.denied('IDENTITY_MISMATCH')
    def test_scope_mismatch(self): self.edit(self.b,scope='DEMO/H5/other');self.denied('SCOPE_MISMATCH')
    def test_invalid_scope(self): self.edit(self.b,scope='CORE/private');self.denied('INVALID_SCOPE')
    def test_unsupported_record_type(self): self.edit(self.b,source_type='conversation');self.denied('UNSUPPORTED_RECORD_TYPE')
    def test_missing_provenance(self):
        b=json.loads(self.b.read_bytes());del b['provenance'];self.b.write_text(json.dumps(b));self.denied('CAPTURE_FIELDS')
    def test_unverifiable_verified_origin_rejected(self):
        self.edit(self.b,provenance={'method':'synthetic-fixture','collector':'fixture','origin_status':'VERIFIED'});self.denied('ORIGIN_NOT_SUPPORTED')
    def test_disallowed_credential_field(self): self.edit(self.b,api_key='FICTIONAL-NOT-A-CREDENTIAL');self.denied('CAPTURE_FIELDS')
    def test_unexpected_provenance_field(self):
        self.edit(self.b,provenance={'method':'synthetic-fixture','collector':'fixture','origin_status':'SYNTHETIC','token':'fictional'});self.denied('PROVENANCE_FIELDS')
    def test_oversized_input(self): self.b.write_bytes(b' '*16385);self.denied('INPUT_TOO_LARGE')
    def test_malformed_json(self): self.b.write_bytes(b'{');self.denied('INVALID_JSON')
    def test_duplicate_json_keys(self): self.b.write_bytes(b'{"mode":"synthetic","mode":"external"}');self.denied('DUPLICATE_JSON_KEY')
    def test_nan_rejected(self): self.b.write_bytes(b'{"confirmed":NaN}');self.denied('INVALID_JSON')
    def test_bool_fact_id_rejected(self): self.edit(self.b,fact_id=True);self.denied('INVALID_FACT_ID')
    def test_string_confirmation_rejected(self): self.edit(self.b,confirmed='false');self.denied('INVALID_CONFIRMATION')
    def test_terminal_control_rejected(self): self.edit(self.b,text='fictional\x1b[31m');self.denied('INVALID_TEXT')
    def test_reversed_stage(self): self.edit(self.b,stage='A');self.denied('STAGE_ORDER')
    def test_reversed_acquisition_clock(self): self.edit(self.b,acquired_at='2026-10-10T12:00:00Z');self.denied('ACQUISITION_ORDER')
    def test_reversed_source_clock(self): self.edit(self.b,source_timestamp='2026-10-10T11:00:00Z');self.denied('SOURCE_ORDER')
    def test_naive_clock_rejected(self): self.edit(self.b,acquired_at='2026-10-10T12:06:00');self.denied('INVALID_TIMESTAMP')
    def test_duplicate_observation_id(self): self.edit(self.b,observation_id='synthetic-A');self.denied('DUPLICATE_OBSERVATION')
    def test_source_unavailable(self): self.edit(self.b,availability='UNAVAILABLE');self.denied('SOURCE_UNAVAILABLE')
    def test_mode_mismatch(self): self.edit(self.b,mode='external');self.denied('MODE_MISMATCH')

    def test_external_interface_with_fictional_unverified_inputs(self):
        for p in (self.a,self.b):self.edit(p,mode='external',provenance={'method':'external-supplied','collector':'fictional-test-collector','origin_status':'CLAIMED_UNVERIFIED'})
        r=self.capture(mode='external');self.assertEqual(r.returncode,0,r.stderr)
        v=json.loads(self.ask(json.loads(r.stdout)['pair_sha256']).stdout)['view']
        self.assertEqual(v['origin_status'],'CLAIMED_UNVERIFIED')
        self.assertIn('not independently authenticated',' '.join(v['uncertainty']))
        self.assertNotIn('LIVE PASS',v['answer'])

    def test_preserved_historical_refusal_predicate_with_fictional_id(self):
        import importlib.util
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('h5_guard_test',APP)
        h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
        c=json.loads(self.a.read_bytes());c.update(mode='external',fact_id=43,
          provenance={'method':'external-supplied','collector':'fictional','origin_status':'CLAIMED_UNVERIFIED'})
        with patch.object(h,'HISTORICAL_REFUSAL_SHA',hashlib.sha256(b'43').hexdigest()):
            with self.assertRaisesRegex(h.Stop,'HISTORICAL_TARGET_FORBIDDEN'):
                h.validate_capture(h.canonical(c),mode='external',stage='A',fact_id=43,scope=c['scope'])

    def test_existing_store_never_overwritten(self):
        self.pair();before={p.name:p.read_bytes() for p in self.run.iterdir()}
        self.edit(self.b,text='Different fictional second submission')
        r=self.capture();self.assertEqual(r.returncode,2);self.assertIn('STORE_EXISTS',r.stderr)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.run.iterdir()})

    def test_tampered_evidence(self):
        r=self.pair();p=self.run/'000001.json';x=json.loads(p.read_bytes());x['capture']['text']='tampered';p.write_text(json.dumps(x))
        q=self.ask(r['pair_sha256']);self.assertEqual(q.returncode,2);self.assertIn('RECORD_HASH_MISMATCH',q.stderr)

    def test_missing_record(self):
        r=self.pair();(self.run/'000002.json').unlink();q=self.ask(r['pair_sha256']);self.assertEqual(q.returncode,2);self.assertIn('INCOMPLETE_PAIR',q.stderr)

    def test_unexpected_store_file(self):
        r=self.pair();(self.run/'extra.json').write_text('{}');q=self.ask(r['pair_sha256']);self.assertEqual(q.returncode,2);self.assertIn('INCOMPLETE_PAIR',q.stderr)

    def test_pair_anchor_tampering(self):
        r=self.pair();(self.run/'PAIR.json').write_text('{}');q=self.ask(r['pair_sha256']);self.assertEqual(q.returncode,2);self.assertIn('PAIR_HASH_MISMATCH',q.stderr)

    def test_interrupted_capture_fails_closed_and_preserves_a(self):
        r=subprocess.run([sys.executable,'-I','-B',str(ROOT/'fault_probe.py'),str(self.a),str(self.b),str(self.run)],cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode,74,r.stderr);a=(self.run/'000001.json').read_bytes()
        q=self.ask('0'*64);self.assertEqual(q.returncode,2);self.assertIn('INCOMPLETE_PAIR',q.stderr)
        self.assertEqual(a,(self.run/'000001.json').read_bytes());self.assertNotEqual(self.capture().returncode,0)

    def test_hardlinked_input_refused(self):
        os.link(self.a,self.home/'A-link.json');self.denied('UNSAFE_PATH')

    def test_outside_workspace_refused(self):
        r=self.cli('acquire','--a',self.a,'--b',self.b,'--run',ROOT.parent/'outside-h5','--mode','synthetic','--fact-id',900000001,'--scope','DEMO/H5/synthetic')
        self.assertEqual(r.returncode,2);self.assertIn('UNSAFE_PATH',r.stderr)

    def test_historical_mode_is_explicit_separate_handoff(self):
        r=self.cli('historical');self.assertEqual(r.returncode,0,r.stderr);x=json.loads(r.stdout)
        self.assertEqual(x['mode'],'historical-replay-handoff');self.assertFalse(x['executed'])
        self.assertIn('historical',x['message'].lower());self.assertIn('No live Bee',x['message'])

    def test_capability_guard_denies_network_and_private_file_access(self):
        r=subprocess.run([sys.executable,'-I','-B',str(ROOT/'capability_probe.py')],cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr);x=json.loads(r.stdout)
        self.assertTrue(x['network_denied']);self.assertTrue(x['external_file_denied'])


if __name__=='__main__':unittest.main(verbosity=2)
