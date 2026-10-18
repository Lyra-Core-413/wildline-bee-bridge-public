"""Test disposable clean copies. All acquisition transport is fictional."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from package_integrity import verify

def main():
    verify()
    tests=['test_process_control.py','test_bridge.py','test_bee_runtime.py','real/test_h5.py']
    for name in tests:
        with tempfile.TemporaryDirectory(prefix='wildline-clean-tests-') as temp:
            clone=Path(temp)/'package';shutil.copytree(ROOT,clone)
            p=subprocess.run([sys.executable,'-X','utf8','-I','-B',str(clone/name)],cwd=clone,timeout=90)
            if p.returncode:return p.returncode
    verify()
    print('PASS: fictional adapter/bridge, Windows isolation and unchanged H5 pair tests. No Bee calls.')
    return 0
if __name__=='__main__':raise SystemExit(main())
