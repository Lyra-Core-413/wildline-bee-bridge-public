"""Deliberate single Bee Fact read; no retry, writes, pair or new semantics.

Bounded transport adapted from the previously tested bridge collect_once.
This is a new per-consent operation, never the consumed historical entry point.
"""
import argparse
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import threading
import uuid

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import private_work
import process_control
CLI_SHA='865e421f94af9a4aab1426af5b062d91236b7d08e9098de0758fba1d1b0dc5e6'
ENGINE_SHA='6704ac1281c7a8578ad8010bfaf73d842482b227cdae9dd1a3d23ecae26d5cbe'
FIELDS='id,text,confirmed,created_at'
HISTORICAL_REFUSAL_SHA='44cb730c420480a0477b505ae68af508fb90f96cf0ec54c6ad16949dd427f13a'
MAX_STDOUT=65536
MAX_STDERR=4096
class Stop(ValueError):
    """Sanitized reason codes only; never raw external content."""
def require(ok,reason):
    if not ok:raise Stop(reason)
def digest(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()
def fact_id(value):
    if type(value) is str:
        require(re.fullmatch(r'[1-9][0-9]{0,15}',value) is not None,'INVALID_FACT_ID')
        value=int(value)
    require(type(value) is int and 0<value<=9007199254740991,'INVALID_FACT_ID')
    require(hashlib.sha256(str(value).encode('ascii')).hexdigest()!=HISTORICAL_REFUSAL_SHA,'HISTORICAL_TARGET_FORBIDDEN')
    return value
def consent_line(value):return f'READ CAPTURE AND RECOVER FACT {fact_id(value)} FIELDS {FIELDS}'
def engine():
    path=ROOT/'real/h5_sidecar.py'
    require(digest(path)==ENGINE_SHA,'H5_ENGINE_MISMATCH')
    spec=importlib.util.spec_from_file_location('unchanged_H5_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
def _verify_native(path,expected_sha):
    path=Path(path)
    require(path.is_absolute() and not str(path).startswith('\\\\'),'CLI_PATH_UNSAFE')
    try:private_work.require_local(path,'CLI_PATH_UNSAFE')
    except ValueError as exc:raise Stop(str(exc)) from None
    require(path.name.casefold()=='bee.exe' and path.suffix.casefold()=='.exe','CLI_NATIVE_EXE_REQUIRED')
    require(path.is_file(),'CLI_MISSING')
    for part in (path,*path.parents):
        if part.exists():
            info=part.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'CLI_PATH_UNSAFE')
            if stat.S_ISREG(info.st_mode):require(info.st_nlink==1,'CLI_PATH_UNSAFE')
    require(digest(path)==expected_sha,'CLI_IDENTITY_UNVERIFIED')
    return {'path':str(path),'sha256':expected_sha,'basename':'bee.exe','package':'@beeai/cli','version':'0.7.3'}
def resolve_cli(explicit=None,*,which=shutil.which):
    selected=explicit if explicit is not None else which('bee.exe')
    require(selected is not None,'CLI_MISSING')
    return _verify_native(selected,CLI_SHA)
def error_code(stderr):
    text=stderr.decode('utf-8',errors='replace').casefold()
    if re.search(r'\b401\b|unauthenticated|not authenticated|authentication required|please (?:log|sign) in',text):
        return 'CLI_AUTHENTICATION_REQUIRED'
    if re.search(r'\b403\b|access denied|forbidden',text):return 'CLI_ACCESS_DENIED'
    if re.search(r'\b503\b|service unavailable|connection refused|cannot connect|unable to reach|network unavailable',text):
        return 'CLI_SERVICE_UNAVAILABLE'
    return 'CLI_READ_FAILED_AUTH_OR_AVAILABILITY_UNKNOWN'
def _collect_process(process,job,*,popen,timeout,buffers,errors,threads,cancelled,lifecycle):
    def kill():
        try:process.kill()
        except OSError:pass
    def settle():
        if lifecycle['settled']:return
        try:
            if job:job.close()
            else:kill()
            process.wait(timeout=5)
        except (OSError,subprocess.TimeoutExpired,ValueError):raise Stop('CLI_CLEANUP_UNVERIFIED') from None
        lifecycle['settled']=True
    def consume(index,stream,limit,reason):
        try:
            while True:
                chunk=stream.read(4096)
                if not chunk or cancelled.is_set():break
                if len(buffers[index])+len(chunk)>limit:errors.append(reason);kill();break
                buffers[index].extend(chunk)
        except (OSError,ValueError):errors.append('CLI_IO_FAILURE');kill()
    try:
        for index,stream,limit,reason in [(0,process.stdout,MAX_STDOUT,'RESPONSE_TOO_LARGE'),
                                         (1,process.stderr,MAX_STDERR,'DIAGNOSTIC_LIMIT')]:
            t=threading.Thread(target=consume,args=(index,stream,limit,reason),daemon=True);threads.append(t);t.start()
        try:process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:errors.append('CLI_TIMEOUT')
        completed=datetime.now(timezone.utc);exit_code=process.returncode
        settle()  # Includes descendants, before joining pipe readers.
        for t in threads:t.join(timeout=2)
        require(not any(t.is_alive() for t in threads),'CLI_PIPE_CLEANUP_UNVERIFIED')
        if errors:raise Stop(errors[0])
        if exit_code!=0:raise Stop(error_code(bytes(buffers[1])))
        return bytes(buffers[0]),completed,{'cli_invocations':1,'exit_code':0,'timeout_seconds':timeout,
            'stdout_limit':MAX_STDOUT,'stderr_limit':MAX_STDERR,'raw_output_saved':False,
            'transport':'CLI_EXECUTION' if popen is subprocess.Popen else 'MOCKED_IMPLEMENTATION_TEST'}
    finally:
        try:settle()
        finally:
            cancelled.set()
            for buffer in buffers:buffer.clear()
            # A blocked mocked pipe must not delay refusal indefinitely.
            for index,stream in enumerate((process.stdout,process.stderr)):
                if index>=len(threads) or not threads[index].is_alive():stream.close()

def collect_command(args,*,popen=subprocess.Popen,timeout=20):
    """Initialize transport before launch; own production child across all setup."""
    buffers=[bytearray(),bytearray()];errors=[];threads=[];cancelled=threading.Event();lifecycle={'settled':False}
    kw=dict(shell=False,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),bufsize=0)
    def exchange(process,job):
        return _collect_process(process,job,popen=popen,timeout=timeout,buffers=buffers,
                                errors=errors,threads=threads,cancelled=cancelled,lifecycle=lifecycle)
    try:
        if popen is subprocess.Popen:
            with process_control.owned_launch(args,**kw) as (process,job):return exchange(process,job)
        process=popen(args,**kw) # Trusted mocked implementation only.
        try:return exchange(process,None)
        finally:
            if not lifecycle['settled']:
                try:process.kill()
                except OSError:pass
                process.wait(timeout=5)
    except process_control.ProcessRefused:raise Stop('PROCESS_CONTAINMENT_UNVERIFIED') from None
    except subprocess.TimeoutExpired:raise Stop('CLI_CLEANUP_UNVERIFIED') from None
    except OSError:raise Stop('CLI_UNAVAILABLE') from None

def collect(exe,value,*,popen=subprocess.Popen,timeout=20):
    value=fact_id(value)
    return collect_command([str(exe),'facts','get',str(value),'--json'],popen=popen,timeout=timeout)

def map_response(raw,value,completed):
    value=fact_id(value);h5=engine()
    require(type(raw) is bytes and len(raw)<=MAX_STDOUT,'RESPONSE_TOO_LARGE')
    try:data=h5.parse(raw)
    except h5.Stop:raise Stop('INVALID_JSON') from None
    require(type(data) is dict,'INVALID_JSON_STRUCTURE')
    require(type(data.get('id')) is int and data['id']==value,'FACT_ID_MISMATCH')
    require(type(data.get('text')) is str,'INVALID_FACT_TEXT')
    if 'confirmed' in data:require(type(data['confirmed']) is bool,'INVALID_CONFIRMATION')
    require(not re.search(r'-----BEGIN .*PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{20,}|\b(?:password|api[_ -]?key|token)\s*[:=]\s*\S+',
                         data['text'],re.I),'SELECTED_TEXT_REQUIRES_PRIVACY_REVIEW')
    require(isinstance(completed,datetime) and completed.tzinfo is not None,'INVALID_ACQUISITION_TIME')
    completed=completed.astimezone(timezone.utc);operation=uuid.uuid4().hex
    capture={'contract':'H5_CAPTURE_V1','mode':'external','source_type':'bee_fact','fact_id':value,'stage':'A',
      'scope':'DEMO/H5/runtime-'+operation,'observation_id':'bee-runtime-'+operation,'text':data['text'],
      'availability':'AVAILABLE','acquired_at':completed.isoformat(timespec='microseconds').replace('+00:00','Z'),
      'provenance':{'collector':'bee-cli-0.7.3','method':'external-supplied','origin_status':'CLAIMED_UNVERIFIED'}}
    if 'confirmed' in data:capture['confirmed']=data['confirmed']
    timestamp={'field':'created_at','status':'NOT_SUPPLIED'}
    if 'created_at' in data:
        timestamp['status']='SOURCE_TIMESTAMP_UNVERIFIED';created=data['created_at']
        epoch=datetime(1970,1,1,tzinfo=timezone.utc);lower=datetime(2000,1,1,tzinfo=timezone.utc)
        upper=completed+timedelta(hours=24)
        min_s=int((lower-epoch).total_seconds());max_s=int((upper-epoch).total_seconds())
        if type(created) is int and min_s*1000<=created<=max_s*1000 and not min_s<=created<=max_s:
            capture['source_timestamp']=(epoch+timedelta(milliseconds=created)).isoformat(timespec='milliseconds').replace('+00:00','Z')
            timestamp.update(status='VERIFIED',meaning='source creation time, Unix milliseconds; not update time')
    encoded=h5.canonical(capture)
    require(len(encoded)<=h5.MAX_INPUT,'CAPTURE_TOO_LARGE')
    try:h5.validate_capture(encoded,mode='external',stage='A',fact_id=value,scope=capture['scope'])
    except h5.Stop:raise Stop('H5_CAPTURE_REJECTED') from None
    return capture,timestamp
def safe_output(path,root):
    try:return private_work.safe(path,root)
    except ValueError as exc:raise Stop(str(exc)) from None

def save(path,value,root):
    data=engine().canonical(value)
    with safe_output(path,root).open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
    return hashlib.sha256(data).hexdigest()

OP_FILES={'attempt.json','capture.json','receipt.json','failure.json','SINGLE.json','STATE.json',
          'READER-CLAIM.json','RECOVERED.json','COMPLETE.json'}
def cleanup_failure(folder,root,reason):
    """Only the just-created UUID operation; never recursively deletes."""
    try:
        folder=private_work.operation(root,Path(folder).name)
        require(folder.is_dir(),'CLEANUP_UNVERIFIED')
        names={p.name for p in folder.iterdir()}
        require(names<=OP_FILES,'CLEANUP_UNVERIFIED')
        for name in sorted(names-{'attempt.json'}):safe_output(folder/name,root).unlink()
        save(folder/'failure.json',{'status':'FAILED','reason':reason,'no_retry':True,
             'private_selected_data_removed':True,'authority':'NONE'},root)
    except (OSError,ValueError):raise Stop('CLEANUP_UNVERIFIED') from None

def failure_code(exc):
    if isinstance(exc,KeyboardInterrupt):return 'INTERRUPTED'
    if isinstance(exc,Stop) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,95}',str(exc)):return str(exc)
    return 'LOCAL_OR_FORMAT_FAILURE'

def read_once(value,*,confirm=input,resolve=resolve_cli,transport=collect,output_root=None,operation_ready=None):
    value=fact_id(value);expected=consent_line(value)
    response=confirm('Authorize ONE Bee Fact read, selected-field private local capture, display, and ONE fresh-process recovery.'+
                     '\nFact '+str(value)+'; fields '+FIELDS+'. No retry, source changes, comparison or synchronization.'+
                     '\nThe selected text/ID will remain in the private operation folder on success. Type exactly:\n'+expected+'\n> ')
    require(type(response) is str and response==expected,'CONSENT_REQUIRED')
    require(output_root is not None,'PRIVATE_ROOT_REQUIRED')
    identity=resolve()
    try:root=private_work.make_root(output_root);folder=private_work.make_dir(private_work.operation(root,uuid.uuid4().hex))
    except ValueError as exc:raise Stop(str(exc)) from None
    try:
        if operation_ready is not None:operation_ready(folder,root)
        save(folder/'attempt.json',{'format':'EXPLICIT_SINGLE_BEE_READ_ATTEMPT_V2','fact_id':value,
             'fields':FIELDS.split(','),'planned_invocations':1,'consent_sha256':hashlib.sha256(expected.encode()).hexdigest(),
             'consent_scope':['one_fact_read','selected_field_capture','display','one_fresh_process_recovery'],
             'authority':'NONE'},root)
        raw,completed,transport_receipt=transport(identity['path'],value)
        require(type(transport_receipt) is dict and transport_receipt.get('transport') in
                ('CLI_EXECUTION','MOCKED_IMPLEMENTATION_TEST'),'TRANSPORT_RECEIPT_INVALID')
        capture,timestamp=map_response(raw,value,completed);del raw
        capture_hash=save(folder/'capture.json',capture,root)
        receipt={'format':'EXPLICIT_SINGLE_BEE_READ_V2','status':'CAPTURED_RECOVERY_PENDING','fact_id':value,
          'permitted_fields':FIELDS.split(','),'CLI_basename':'bee.exe','CLI_sha256':identity['sha256'],
          'capture_sha256':capture_hash,'transport':transport_receipt,'timestamp':timestamp,
          'origin_status':'CLAIMED_UNVERIFIED','device_origin':'DEVICE_ORIGIN_UNVERIFIED','authority':'NONE',
          'raw_output_saved':False,'pair_recovery_performed':False,'changed_state_demonstrated':False}
        save(folder/'receipt.json',receipt,root)
        return {'capture':capture,'receipt':receipt,'operation':str(folder),'private_root':str(root)}
    except BaseException as exc:
        code=failure_code(exc);cleanup_failure(folder,root,code)
        raise Stop(code) from None

def main():
    print('STOP: USE_SINGLE_BRIDGE_ENTRY_REQUIRED',file=sys.stderr)
    return 2
if __name__=='__main__':raise SystemExit(main())
