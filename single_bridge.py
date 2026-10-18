"""One consent, one selected Fact acquisition, one offline fresh reader."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import bee_runtime as b
import private_work as pw
from package_integrity import verify

def hashes(folder):
    return {name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
            for name in ('attempt.json','capture.json','receipt.json','SINGLE.json')}

def recover(folder,root,anchor):
    argv=[sys.executable,'-X','utf8','-I','-B',str(ROOT/'single_reader.py'),
          '--private-root',str(root),'--operation',folder.name,'--seal-sha256',anchor]
    try:raw,_,_=b.collect_command(argv,timeout=15)
    except b.Stop as exc:
        if str(exc) in ('CLI_TIMEOUT','CLI_CLEANUP_UNVERIFIED','CLI_PIPE_CLEANUP_UNVERIFIED','PROCESS_CONTAINMENT_UNVERIFIED'):
            raise b.Stop('READER_'+str(exc)) from None
        raise b.Stop('READER_FAILED') from None
    b.require(raw==b'','READER_UNEXPECTED_STDOUT')
    with b.safe_output(folder/'RECOVERED.json',root).open('rb') as f:data=f.read(32769)
    b.require(len(data)<=32768,'RECOVERED_TOO_LARGE')
    result=b.engine().parse(data)
    b.require(data==b.engine().canonical(result),'RECOVERED_FORMAT_INVALID')
    return result

def display(result):
    view=result['view'];c=view['observation']
    label=('MOCKED OFFLINE DEMONSTRATION — fictional CLI response; no genuine Bee data.'
           if result['acquisition_kind']=='MOCKED_IMPLEMENTATION_TEST' else
           'ONE AUTHORIZED BEE CLI READ — selected fields; source/device origin not independently authenticated.')
    return '\n'.join([label,'','What matters now?',view['answer'],'',
        'Source: Bee-style Fact '+str(c['fact_id'])+'; collector '+c['provenance']['collector']+'.',
        'Provenance: '+c['provenance']['origin_status']+'; scope '+c['scope']+'.',
        'Acquired: '+c['acquired_at']+'. Source creation: '+c.get('source_timestamp','UNKNOWN')+'.',
        'Recovered by a separate process from one retained selected-field capture.',
        'Change status: '+view['change_status']+'.',
        'Uncertainty: '+' '.join(view['uncertainty']),view['challenge'],
        'Authority: NONE. No actions taken.'])

def execute(value,private_root,*,confirm=input,resolve=b.resolve_cli,transport=b.collect,emit=None):
    verify()
    owned={}
    def operation_ready(folder,root):owned.update(folder=folder,root=root)
    try:
        capture=b.read_once(value,confirm=confirm,resolve=resolve,transport=transport,
                            output_root=private_root,operation_ready=operation_ready)
        folder=Path(capture['operation']);root=Path(capture['private_root'])
        h=b.engine();files={}
        for name in ('attempt.json','capture.json','receipt.json'):
            raw=b.safe_output(folder/name,root).read_bytes();files[name]={'bytes':len(raw),'sha256':h.sha(raw)}
        kind=capture['receipt']['transport']['transport']
        seal={'contract':'H5_SINGLE_OBSERVATION_V1','observation_count':1,'fact_id':capture['capture']['fact_id'],
              'scope':capture['capture']['scope'],'operation':folder.name,'acquisition_pid':os.getpid(),
              'acquisition_kind':kind,'files':files,
              'consent_sha256':hashlib.sha256(b.consent_line(value).encode()).hexdigest(),'authority':'NONE'}
        anchor=b.save(folder/'SINGLE.json',seal,root)
        b.save(folder/'STATE.json',{'status':'RECOVERY_PENDING','seal_sha256':anchor,'authority':'NONE'},root)
        before=hashes(folder);result=recover(folder,root,anchor);after=hashes(folder)
        expected={'format':'H5_SINGLE_RECOVERED_V1','acquisition_pid':os.getpid(),'observation_count':1,
                  'acquisition_kind':kind,'seal_sha256':anchor,'view':h.project_single(capture['capture'])}
        b.require(type(result) is dict and set(result)==set(expected)|{'reader_pid'}
                  and {k:v for k,v in result.items() if k!='reader_pid'}==expected,'RECOVERED_RESULT_MISMATCH')
        b.require(type(result['reader_pid']) is int and result['reader_pid']>0
                  and result['reader_pid']!=os.getpid(),'FRESH_PROCESS_NOT_PROVEN')
        b.require(before==after,'READER_MUTATED_EVIDENCE')
        if emit is not None:emit(display(result))
        receipt=result|{'status':'COMPLETE','before_reader':before,'after_reader':after,
                       'reader_preserved_evidence':True,'reader_exit_code':0,'operation':str(folder),
                       'authority':'NONE','no_retry':True}
        b.save(folder/'COMPLETE.json',receipt,root)
        return receipt
    except BaseException as exc:
        code=b.failure_code(exc)
        if owned:b.cleanup_failure(owned['folder'],owned['root'],code)
        raise b.Stop(code) from None

def offline_demo(private_root,emit=None):
    data=(ROOT/'fixtures/fictional-cli-response.json').read_bytes()
    # Exercise the exact adapter collect/map path with an in-memory fake executable.
    import io
    class FictionalProcess:
        def __init__(self):self.stdout=io.BytesIO(data);self.stderr=io.BytesIO();self.returncode=0
        def wait(self,timeout=None):return self.returncode
        def kill(self):pass
    def mocked(argv,**kwargs):
        b.require(argv==['fictional-bee.exe','facts','get','42','--json'] and kwargs['shell'] is False,'MOCK_ARGV_MISMATCH')
        return FictionalProcess()
    return execute(42,private_root,confirm=lambda _:b.consent_line(42),
                   resolve=lambda:{'path':'fictional-bee.exe','sha256':'MOCKED_NO_EXECUTABLE'},
                   transport=lambda exe,value:b.collect(exe,value,popen=mocked),emit=emit)

def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    group=p.add_mutually_exclusive_group();group.add_argument('--offline-demo',action='store_true')
    group.add_argument('--live-read',action='store_true')
    p.add_argument('--fact-id');p.add_argument('--bee-exe');p.add_argument('--private-root')
    a=p.parse_args()
    try:
        if a.live_read:
            b.require(a.fact_id is not None,'FACT_ID_REQUIRED')
            b.require(sys.stdin.isatty() and sys.stdout.isatty(),'INTERACTIVE_CONSENT_REQUIRED')
            root=Path(a.private_root) if a.private_root else pw.default_root()
            execute(b.fact_id(a.fact_id),root,resolve=lambda:b.resolve_cli(a.bee_exe),emit=lambda x:print(x,flush=True))
        else:
            b.require(a.fact_id is None and a.bee_exe is None,'OFFLINE_OPTIONS_INVALID')
            root=Path(a.private_root) if a.private_root else pw.default_root()
            offline_demo(root,emit=lambda x:print(x,flush=True))
        print('\nVerified completion saved in the private operation folder. No source changes or synchronization.',flush=True)
        return 0
    except BaseException as exc:
        print('STOP: '+b.failure_code(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
