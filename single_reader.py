"""Fresh-process, offline single-observation recovery. No Bee collector calls."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import bee_runtime as b
import private_work as pw
from package_integrity import verify

FILES={'attempt.json','capture.json','receipt.json','SINGLE.json','STATE.json'}
SEAL_KEYS={'contract','observation_count','fact_id','scope','operation','acquisition_pid',
           'acquisition_kind','files','consent_sha256','authority'}

def read(path,root,limit=32768):
    with pw.safe(path,root).open('rb') as f:raw=f.read(limit+1)
    b.require(len(raw)<=limit,'SINGLE_INPUT_TOO_LARGE')
    h=b.engine();value=h.parse(raw)
    b.require(raw==h.canonical(value),'NONCANONICAL_SINGLE_EVIDENCE')
    return raw,value

def install_guard(folder):
    """Reader capability bounds for trusted local code, not a hostile-code sandbox."""
    runtime=Path(sys.base_prefix).resolve()
    reads={folder/name for name in FILES|{'READER-CLAIM.json','RECOVERED.json'}}
    writes={folder/'READER-CLAIM.json',folder/'RECOVERED.json'}
    def guard(event,args):
        if event.startswith(('socket.','winreg.')) or event in ('subprocess.Popen','os.system','os.startfile','sqlite3.connect'):
            raise PermissionError('READER_CAPABILITY_DENIED')
        if event=='open' and not isinstance(args[0],int):
            p=Path(args[0]).resolve();mode,flags=args[1:3]
            write=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
            if write and p not in writes:raise PermissionError('READER_CAPABILITY_DENIED')
            if not write and p not in reads and not p.is_relative_to(ROOT) and not p.is_relative_to(runtime):
                raise PermissionError('READER_CAPABILITY_DENIED')
        if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.replace'):
            raise PermissionError('READER_CAPABILITY_DENIED')
    sys.addaudithook(guard)

def recover_one(root,identifier,seal_sha256):
    verify();root=pw.check_root(root);pw.check_acl(root);folder=pw.operation(root,identifier)
    pw.check_acl(folder);install_guard(folder)
    b.require(re.fullmatch(r'[0-9a-f]{64}',seal_sha256) is not None,'SINGLE_ANCHOR_INVALID')
    b.require({p.name for p in folder.iterdir()}==FILES,'SINGLE_STORE_NOT_PENDING')
    seal_raw,seal=read(folder/'SINGLE.json',root)
    b.require(hashlib.sha256(seal_raw).hexdigest()==seal_sha256,'SINGLE_ANCHOR_MISMATCH')
    b.require(type(seal) is dict and set(seal)==SEAL_KEYS,'SINGLE_CONTRACT')
    b.require(seal['contract']=='H5_SINGLE_OBSERVATION_V1' and type(seal['observation_count']) is int
              and seal['observation_count']==1 and seal['operation']==identifier and seal['authority']=='NONE','SINGLE_CONTRACT')
    value=b.fact_id(seal['fact_id'])
    b.require(type(seal['acquisition_pid']) is int and seal['acquisition_pid']>0
              and seal['acquisition_pid']!=os.getpid(),'FRESH_PROCESS_NOT_PROVEN')
    kind=seal['acquisition_kind'];b.require(kind in ('CLI_EXECUTION','MOCKED_IMPLEMENTATION_TEST'),'SINGLE_ORIGIN_INVALID')
    expected_consent=hashlib.sha256(b.consent_line(value).encode()).hexdigest()
    b.require(seal['consent_sha256']==expected_consent,'CONSENT_BINDING_MISMATCH')
    b.require(type(seal['files']) is dict and set(seal['files'])=={'attempt.json','capture.json','receipt.json'},'SINGLE_FILE_BINDING')
    records={}
    for name,pin in seal['files'].items():
        raw,obj=read(folder/name,root)
        b.require(type(pin) is dict and set(pin)=={'bytes','sha256'} and pin['bytes']==len(raw)
                  and pin['sha256']==hashlib.sha256(raw).hexdigest(),'SINGLE_FILE_HASH_MISMATCH')
        records[name]=obj
    attempt=records['attempt.json']
    b.require(attempt=={'format':'EXPLICIT_SINGLE_BEE_READ_ATTEMPT_V2','fact_id':value,
              'fields':b.FIELDS.split(','),'planned_invocations':1,'consent_sha256':expected_consent,
              'consent_scope':['one_fact_read','selected_field_capture','display','one_fresh_process_recovery'],
              'authority':'NONE'},'CONSENT_BINDING_MISMATCH')
    _,state=read(folder/'STATE.json',root)
    b.require(state=={'status':'RECOVERY_PENDING','seal_sha256':seal_sha256,'authority':'NONE'},'SINGLE_STORE_NOT_PENDING')
    h=b.engine();capture=h.validate_capture(h.canonical(records['capture.json']),mode='external',stage='A',
            fact_id=value,scope=seal['scope'])
    receipt=records['receipt.json']
    b.require(type(receipt) is dict and receipt.get('format')=='EXPLICIT_SINGLE_BEE_READ_V2'
              and receipt.get('status')=='CAPTURED_RECOVERY_PENDING' and receipt.get('fact_id')==value
              and receipt.get('capture_sha256')==seal['files']['capture.json']['sha256']
              and receipt.get('permitted_fields')==b.FIELDS.split(',') and receipt.get('authority')=='NONE'
              and receipt.get('raw_output_saved') is False and receipt.get('pair_recovery_performed') is False
              and receipt.get('changed_state_demonstrated') is False
              and receipt.get('transport',{}).get('transport')==kind,'SINGLE_RECEIPT_MISMATCH')
    b.require(receipt.get('CLI_basename')=='bee.exe' and
              (kind!='CLI_EXECUTION' or receipt.get('CLI_sha256')==b.CLI_SHA),'CLI_IDENTITY_UNVERIFIED')
    b.save(folder/'READER-CLAIM.json',{'reader_pid':os.getpid(),'seal_sha256':seal_sha256},root)
    view=h.project_single(capture)
    result={'format':'H5_SINGLE_RECOVERED_V1','reader_pid':os.getpid(),'acquisition_pid':seal['acquisition_pid'],
            'observation_count':1,'acquisition_kind':kind,'seal_sha256':seal_sha256,'view':view}
    b.save(folder/'RECOVERED.json',result,root)
    return result

def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--private-root',required=True);p.add_argument('--operation',required=True)
    p.add_argument('--seal-sha256',required=True);a=p.parse_args()
    try:recover_one(a.private_root,a.operation,a.seal_sha256);return 0
    except BaseException as exc:
        print('STOP: '+b.failure_code(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
