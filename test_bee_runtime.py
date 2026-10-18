"""Injected synthetic transport only. Never invokes installed Bee."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import io
import subprocess
import hashlib
import threading
import time
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parent
import sys
sys.path.insert(0,str(ROOT))
import private_work as pw
spec=importlib.util.spec_from_file_location('bee_runtime',ROOT/'bee_runtime.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='wildline-fictional-adapter-');self.addCleanup(self.temp.cleanup)
        self.calls=[]
    def test_authorized_single_observation_uses_native_validator(self):
        def transport(exe,fact_id):
            self.calls.append((exe,fact_id))
            return (json.dumps({'id':42,'text':'Synthetic adapter test only','confirmed':True,
                                'created_at':1791205499028,'token':'UNRELATED_SYNTHETIC_SENTINEL'}).encode(),
                    datetime(2026,10,10,tzinfo=timezone.utc),{'transport':'MOCKED_IMPLEMENTATION_TEST','cli_invocations':1})
        try:
            result=b.read_once(42,confirm=lambda prompt:'READ CAPTURE AND RECOVER FACT 42 FIELDS id,text,confirmed,created_at',
                              resolve=lambda:{'path':'mock.exe','sha256':'mocked identity'},
                              transport=transport,output_root=Path(self.temp.name)/'private')
        except b.Stop:result=None
        self.assertIsNotNone(result,'Authorized mocked single-observation path is not implemented')
        self.assertEqual(self.calls,[('mock.exe',42)])
        self.assertEqual(result['capture']['fact_id'],42)
        self.assertEqual(result['capture']['provenance']['origin_status'],'CLAIMED_UNVERIFIED')
        self.assertFalse(result['receipt']['pair_recovery_performed'])
        self.assertNotIn('token',result['capture'])
class FakeProcess:
    def __init__(self,out=b'{}',err=b'',code=0,timeout=False):
        self.stdout=io.BytesIO(out);self.stderr=io.BytesIO(err);self.returncode=code
        self.timeout=timeout;self.killed=False
    def wait(self,timeout=None):
        if self.timeout and not self.killed:raise subprocess.TimeoutExpired('synthetic',timeout)
        return self.returncode
    def kill(self):self.killed=True;self.returncode=-1

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='wildline-fictional-adapter-');self.addCleanup(self.temp.cleanup)
        self.home=pw.make_root(Path(self.temp.name)/'private');self.when=datetime(2026,10,10,tzinfo=timezone.utc)
    def mapped(self,**changes):
        data={'id':42,'text':'Synthetic adapter test only'};data.update(changes)
        return b.map_response(json.dumps(data).encode(),42,self.when)
    def fail(self,code,fn):
        with self.assertRaises(b.Stop) as caught:fn()
        self.assertEqual(str(caught.exception),code)
    def test_fixed_argv_shell_disabled_and_single_launch(self):
        process=FakeProcess();launcher=Mock(return_value=process)
        raw,when,receipt=b.collect('synthetic-bee.exe',42,popen=launcher)
        self.assertEqual(raw,b'{}');self.assertEqual(launcher.call_count,1)
        args,kw=launcher.call_args
        self.assertEqual(args[0],['synthetic-bee.exe','facts','get','42','--json'])
        self.assertIs(kw['shell'],False);self.assertEqual(kw['stdin'],subprocess.DEVNULL)
        self.assertEqual(receipt['transport'],'MOCKED_IMPLEMENTATION_TEST')
        self.assertFalse(receipt['raw_output_saved']);self.assertIsNotNone(when.tzinfo)
    def test_invalid_ids_never_launch(self):
        for value in (0,-1,True,42.0,'42 & whoami','042','４２','',9007199254740992):
            launch=Mock()
            with self.subTest(value=value):self.fail('INVALID_FACT_ID',lambda:b.collect('mock',value,popen=launch))
            launch.assert_not_called()
    def test_historical_policy_never_launches(self):
        launch=Mock()
        with patch.object(b,'HISTORICAL_REFUSAL_SHA',hashlib.sha256(b'43').hexdigest()):
            self.fail('HISTORICAL_TARGET_FORBIDDEN',lambda:b.collect('mock',43,popen=launch))
        launch.assert_not_called()
    def test_declined_consent_precedes_resolver_and_transport(self):
        resolve=Mock();transport=Mock()
        self.fail('CONSENT_REQUIRED',lambda:b.read_once(42,confirm=lambda _: 'NO',resolve=resolve,transport=transport,output_root=self.home))
        resolve.assert_not_called();transport.assert_not_called();self.assertEqual(list(self.home.iterdir()),[])
    def test_consent_binds_exact_id_and_fields(self):
        for answer in ('READ CAPTURE AND RECOVER FACT 43 FIELDS id,text,confirmed,created_at','READ CAPTURE AND RECOVER FACT 42 FIELDS id,text','yes'):
            self.fail('CONSENT_REQUIRED',lambda:b.read_once(42,confirm=lambda _:answer,resolve=Mock(),output_root=self.home))
    def test_reusable_operations_each_require_new_consent(self):
        prompts=[];calls=[]
        def consent(prompt):prompts.append(prompt);return b.consent_line(42)
        def transport(exe,value):calls.append(value);return b'{"id":42,"text":"Synthetic reusable test"}',self.when,{'transport':'MOCKED_IMPLEMENTATION_TEST'}
        results=[b.read_once(42,confirm=consent,resolve=lambda:{'path':'mock','sha256':'mock'},transport=transport,output_root=self.home) for _ in range(2)]
        self.assertEqual(len(prompts),2);self.assertEqual(calls,[42,42])
        self.assertNotEqual(results[0]['operation'],results[1]['operation'])
        self.assertNotEqual(results[0]['capture']['scope'],results[1]['capture']['scope'])
    def test_missing_confirmation_is_not_inferred(self):
        capture,_=self.mapped();self.assertNotIn('confirmed',capture)
    def test_confirmation_boolean_preserved(self):
        for value in (True,False):self.assertIs(self.mapped(confirmed=value)[0]['confirmed'],value)
    def test_invalid_confirmation_rejected(self):
        for value in (None,1,'true'):self.fail('INVALID_CONFIRMATION',lambda:self.mapped(confirmed=value))
    def test_optional_timestamp_absent(self):
        capture,status=self.mapped();self.assertNotIn('source_timestamp',capture);self.assertEqual(status['status'],'NOT_SUPPLIED')
    def test_optional_timestamp_milliseconds(self):
        capture,status=self.mapped(created_at=1791205499028)
        self.assertEqual(capture['source_timestamp'],'2026-10-05T13:04:59.028Z')
        self.assertEqual(status['status'],'VERIFIED');self.assertIn('creation',status['meaning'])
    def test_optional_unverified_timestamp_omitted(self):
        for value in (None,True,1791205499,'2026-10-05',0,9999999999999,1791205499028.0):
            capture,status=self.mapped(created_at=value)
            self.assertNotIn('source_timestamp',capture);self.assertEqual(status['status'],'SOURCE_TIMESTAMP_UNVERIFIED')
    def test_unrelated_fields_never_survive(self):
        capture,_=self.mapped(token='SYNTHETIC_UNRELATED_SENTINEL',account_id='SYNTHETIC_ACCOUNT',location={'private':'synthetic'})
        self.assertNotIn('SYNTHETIC_UNRELATED_SENTINEL',json.dumps(capture));self.assertNotIn('account_id',capture)
    def test_id_mismatch_rejected(self):self.fail('FACT_ID_MISMATCH',lambda:self.mapped(id=43))
    def test_wrong_id_type_rejected(self):self.fail('FACT_ID_MISMATCH',lambda:self.mapped(id='42'))
    def test_malformed_json_rejected(self):
        for raw in (b'{',b'\xff',b'{"id":42,"id":42}',b'{"id":42,"text":NaN}',b'['*1100):
            self.fail('INVALID_JSON',lambda:b.map_response(raw,42,self.when))
    def test_wrong_response_structure_rejected(self):self.fail('INVALID_JSON_STRUCTURE',lambda:b.map_response(b'[]',42,self.when))
    def test_missing_text_rejected(self):self.fail('INVALID_FACT_TEXT',lambda:b.map_response(b'{"id":42}',42,self.when))
    def test_control_or_empty_text_rejected_by_unchanged_H5(self):
        for text in ('','  ','Synthetic\ncontrol','x'*4097):self.fail('H5_CAPTURE_REJECTED',lambda:self.mapped(text=text))
    def test_selected_sensitive_text_refused_before_save(self):
        self.fail('SELECTED_TEXT_REQUIRES_PRIVACY_REVIEW',lambda:self.mapped(text='Synthetic password=fictional-value'))
    def test_naive_acquisition_time_rejected(self):self.fail('INVALID_ACQUISITION_TIME',lambda:b.map_response(b'{"id":42,"text":"Synthetic"}',42,datetime(2026,10,10)))
    def test_timeout_kills_mock_and_does_not_retry(self):
        process=FakeProcess(timeout=True);launch=Mock(return_value=process)
        self.fail('CLI_TIMEOUT',lambda:b.collect('mock',42,popen=launch,timeout=.01))
        self.assertTrue(process.killed);self.assertEqual(launch.call_count,1)
    def test_blocked_reader_cleanup_does_not_wait_on_buffered_close(self):
        release=threading.Event();entered=threading.Event()
        class BlockedPipe:
            def read(self,size):entered.set();release.wait(12);return b''
            def close(self):release.wait(12)
        process=FakeProcess();process.stdout=BlockedPipe()
        def collect_result():
            try:b.collect('mock',42,popen=Mock(return_value=process))
            except b.Stop as error:result.append(str(error))
        result=[];runner=threading.Thread(target=collect_result,daemon=True);runner.start()
        try:
            self.assertTrue(entered.wait(1));runner.join(3)
            self.assertFalse(runner.is_alive(),'Cleanup exceeded bound while closing a reader-owned pipe')
            self.assertEqual(result,['CLI_PIPE_CLEANUP_UNVERIFIED'])
        finally:release.set();runner.join(2)
    def test_oversized_stdout_refused(self):
        process=FakeProcess(out=b'x'*(b.MAX_STDOUT+1))
        self.fail('RESPONSE_TOO_LARGE',lambda:b.collect('mock',42,popen=Mock(return_value=process)))
        self.assertTrue(process.killed)
    def test_oversized_stderr_refused(self):
        process=FakeProcess(err=b'x'*(b.MAX_STDERR+1))
        self.fail('DIAGNOSTIC_LIMIT',lambda:b.collect('mock',42,popen=Mock(return_value=process)))
    def test_error_diagnostics_sanitized(self):
        for err,code in ((b'401 please log in','CLI_AUTHENTICATION_REQUIRED'),(b'403 forbidden','CLI_ACCESS_DENIED'),(b'503 service unavailable','CLI_SERVICE_UNAVAILABLE'),(b'SYNTHETIC_SECRET_DIAGNOSTIC','CLI_READ_FAILED_AUTH_OR_AVAILABILITY_UNKNOWN')):
            self.fail(code,lambda:b.collect('mock',42,popen=Mock(return_value=FakeProcess(err=err,code=1))))
    def test_missing_process_unavailable(self):self.fail('CLI_UNAVAILABLE',lambda:b.collect('mock',42,popen=Mock(side_effect=FileNotFoundError('synthetic sensitive diagnostic'))))
    def test_failure_receipt_contains_only_reason_not_raw(self):
        def transport(exe,value):raise b.Stop('CLI_AUTHENTICATION_REQUIRED')
        self.fail('CLI_AUTHENTICATION_REQUIRED',lambda:b.read_once(42,confirm=lambda _:b.consent_line(42),resolve=lambda:{'path':'mock','sha256':'mock'},transport=transport,output_root=self.home))
        files=list(self.home.rglob('*.json'));self.assertEqual(len(files),2)
        self.assertEqual({p.name for p in files},{'attempt.json','failure.json'})
        self.assertIn('no_retry',json.loads(next(p for p in files if p.name=='failure.json').read_bytes()))
    def test_missing_path_resolution_no_other_command(self):
        finder=Mock(return_value=None);self.fail('CLI_MISSING',lambda:b.resolve_cli(which=finder));finder.assert_called_once_with('bee.exe')
    def test_native_identity_checked_without_execution(self):
        path=self.home/'bee.exe';path.write_bytes(b'INERT SYNTHETIC NOT AN EXECUTABLE')
        pin=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(b._verify_native(path,pin)['sha256'],pin)
        self.fail('CLI_IDENTITY_UNVERIFIED',lambda:b._verify_native(path,'0'*64))
    def test_shim_relative_and_unc_paths_refused(self):
        self.fail('CLI_NATIVE_EXE_REQUIRED',lambda:b._verify_native(self.home/'bee.cmd','0'*64))
        for value in ('bee.exe',r'\\synthetic\share\bee.exe'):self.fail('CLI_PATH_UNSAFE',lambda:b._verify_native(value,'0'*64))
    def test_outside_output_refused_before_transport(self):
        transport=Mock()
        self.fail('PRIVATE_LOCATION_REQUIRED',lambda:b.read_once(42,confirm=lambda _:b.consent_line(42),resolve=lambda:{'path':'mock','sha256':'mock'},transport=transport,output_root=ROOT.parent/'outside'))
        transport.assert_not_called()
    def test_exclusive_output_never_overwrites(self):
        path=self.home/'once.json';b.save(path,{'synthetic':True},self.home)
        with self.assertRaises(FileExistsError):b.save(path,{'changed':True},self.home)
        self.assertEqual(json.loads(path.read_bytes()),{'synthetic':True})
    def test_single_capture_not_pair_store(self):
        transport=lambda *args:(b'{"id":42,"text":"Synthetic single"}',self.when,{'transport':'MOCKED_IMPLEMENTATION_TEST'})
        result=b.read_once(42,confirm=lambda _:b.consent_line(42),resolve=lambda:{'path':'mock','sha256':'mock'},transport=transport,output_root=self.home)
        folder=Path(result['operation']);self.assertEqual({p.name for p in folder.iterdir()},{'attempt.json','capture.json','receipt.json'})
        self.assertFalse(result['receipt']['changed_state_demonstrated']);self.assertEqual(result['receipt']['authority'],'NONE')
    def test_capture_only_entry_refuses_without_transport(self):
        stderr=io.StringIO()
        with patch.object(b,'collect') as transport,patch('sys.stderr',stderr):
            self.assertEqual(b.main(),2)
        transport.assert_not_called();self.assertIn('USE_SINGLE_BRIDGE_ENTRY_REQUIRED',stderr.getvalue())

if __name__=='__main__':unittest.main(verbosity=2)
