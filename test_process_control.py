"""Inert Python processes only; never launches Bee."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import process_control as pc
import private_work as pw
spec=importlib.util.spec_from_file_location('test_adapter_cleanup',ROOT/'bee_runtime.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class ProcessTests(unittest.TestCase):
    def test_windows_job_kills_inert_child_and_grandchild(self):
        with tempfile.TemporaryDirectory(prefix='wildline-process-test-') as temp:
            marker=Path(temp)/'pids.json'
            code=('import subprocess,sys,os,json,time; '
                  'p=subprocess.Popen([sys.executable,"-I","-B","-c","import time;time.sleep(30)"]); '
                  'open(sys.argv[1],"w").write(json.dumps([os.getpid(),p.pid]));time.sleep(30)')
            child,job=pc.launch([sys.executable,'-I','-B','-c',code,str(marker)],
                shell=False,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                until=time.monotonic()+5
                while not marker.exists() and time.monotonic()<until:time.sleep(.01)
                self.assertTrue(marker.exists(),'Contained inert process did not run')
                pids=json.loads(marker.read_text());self.assertEqual(pids[0],child.pid)
                self.assertNotEqual(pids[0],pids[1])
            finally:job.close();child.wait(timeout=5)
            self.assertIsNotNone(child.returncode)
            # OpenProcess(SYNCHRONIZE) may still find an exited process object; test its wait state.
            import ctypes
            k=ctypes.WinDLL('kernel32',use_last_error=True)
            k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
            k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];k.WaitForSingleObject.restype=ctypes.c_ulong
            k.CloseHandle.argtypes=[ctypes.c_void_p]
            for pid in pids:
                handle=k.OpenProcess(0x100000,False,pid)
                if handle:
                    try:self.assertEqual(k.WaitForSingleObject(handle,0),0)
                    finally:k.CloseHandle(handle)
    def test_adapter_interrupt_kills_and_reaps_mock_child(self):
        import io
        process=Mock(stdout=io.BytesIO(b'{}'),stderr=io.BytesIO(b''),returncode=0)
        process.wait.side_effect=[KeyboardInterrupt,0]
        with self.assertRaises(KeyboardInterrupt):b.collect('mock.exe',42,popen=Mock(return_value=process))
        process.kill.assert_called();self.assertGreaterEqual(process.wait.call_count,2)
    def test_new_root_and_operation_have_restricted_acl(self):
        with tempfile.TemporaryDirectory(prefix='wildline-acl-test-') as temp:
            root=pw.make_root(Path(temp)/'private');pw.check_acl(root)
            op=pw.make_dir(pw.operation(root,'a'*32));pw.check_acl(op)
            self.assertEqual(op,root/('a'*32))
    def test_unc_rejected(self):
        with self.assertRaises(ValueError):pw.check_root(r'\\fictional\share\private')
    def test_interrupt_during_transport_setup_kills_and_reaps(self):
        import io
        from unittest.mock import patch
        process=Mock(stdout=io.BytesIO(b'{}'),stderr=io.BytesIO(b''),returncode=0)
        launcher=Mock(return_value=process)
        with patch.object(b.threading,'Event',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):b.collect('mock.exe',42,popen=launcher)
        # Event setup must precede launch, so no resource exists at this point.
        launcher.assert_not_called();self.assertEqual(process.wait.call_count,0)
    def test_native_launch_owned_before_return_to_collector(self):
        import io
        self.assertTrue(callable(getattr(pc,'owned_launch',None)),'Native launch needs caller-owned context')
        process=Mock(stdout=io.BytesIO(b''),stderr=io.BytesIO(b''),returncode=0)
        job=Mock()
        from unittest.mock import patch
        with patch.object(pc,'Job',return_value=job),patch.object(pc.subprocess,'Popen',return_value=process):
            with self.assertRaises(KeyboardInterrupt):
                with pc.owned_launch(['fictional-python']):raise KeyboardInterrupt
        job.close.assert_called();process.wait.assert_called()

if __name__=='__main__':unittest.main(verbosity=2)
