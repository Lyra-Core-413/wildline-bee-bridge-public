"""Isolated selected-field handoff; no collector, Core, database or Bee client.

Hashes prove local consistency, not external authenticity. Trusted local callers;
path checks/audit hooks are not a hostile-code or concurrent-filesystem sandbox.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parent
MAX_INPUT = 16384
MODES = ('synthetic', 'external')
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
SCOPE = re.compile(r'DEMO/H5/[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
HEX = re.compile(r'[0-9a-f]{64}\Z')
_guard_installed = False
# Preserved refusal-policy fingerprint; not a read target or anonymized evidence.
HISTORICAL_REFUSAL_SHA='44cb730c420480a0477b505ae68af508fb90f96cf0ec54c6ad16949dd427f13a'


class Stop(ValueError):
    """Only bounded reason codes reach stderr; never echo rejected content."""


def require(condition, code):
    if not condition:
        raise Stop(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def parse(raw):
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(Stop('INVALID_JSON')))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise Stop('INVALID_JSON') from None


def safe_path(value):
    path = Path(value).absolute()
    require(path.resolve().is_relative_to(ROOT) and path.resolve() != ROOT, 'UNSAFE_PATH')
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            require(not stat.S_ISLNK(info.st_mode)
                    and not getattr(info, 'st_file_attributes', 0) & 0x400, 'UNSAFE_PATH')
            if stat.S_ISREG(info.st_mode):
                require(info.st_nlink == 1, 'UNSAFE_PATH')
    return path


def read_bytes(path, limit=MAX_INPUT):
    path = safe_path(path)
    try:
        with path.open('rb') as stream:
            raw = stream.read(limit + 1)
    except OSError:
        raise Stop('INPUT_UNAVAILABLE') from None
    require(len(raw) <= limit, 'INPUT_TOO_LARGE')
    return raw


def timestamp(value):
    require(type(value) is str and len(value) <= 40
            and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value),
            'INVALID_TIMESTAMP')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None, 'INVALID_TIMESTAMP')
        return result
    except ValueError:
        raise Stop('INVALID_TIMESTAMP') from None


def validate_capture(raw, *, mode, stage, fact_id, scope):
    require(mode in MODES, 'MODE_MISMATCH')
    obj = parse(raw)
    require(type(obj) is dict, 'CAPTURE_FIELDS')
    required = {'contract','mode','stage','observation_id','source_type','fact_id',
                'scope','text','acquired_at','availability','provenance'}
    require(required <= set(obj) <= required | {'confirmed','source_timestamp'}, 'CAPTURE_FIELDS')
    require(obj['contract'] == 'H5_CAPTURE_V1', 'CAPTURE_CONTRACT')
    require(obj['source_type'] == 'bee_fact', 'UNSUPPORTED_RECORD_TYPE')
    require(type(obj['fact_id']) is int and 0 < obj['fact_id'] <= 9007199254740991, 'INVALID_FACT_ID')
    require(type(fact_id) is int and obj['fact_id'] == fact_id, 'IDENTITY_MISMATCH')
    require(type(obj['scope']) is str and SCOPE.fullmatch(obj['scope']), 'INVALID_SCOPE')
    require(obj['scope'] == scope, 'SCOPE_MISMATCH')
    require(obj['mode'] == mode, 'MODE_MISMATCH')
    require(obj['stage'] == stage, 'STAGE_ORDER')
    require(obj['availability'] == 'AVAILABLE', 'SOURCE_UNAVAILABLE')
    require(type(obj['observation_id']) is str and TOKEN.fullmatch(obj['observation_id']), 'INVALID_OBSERVATION_ID')
    text = obj['text']
    require(type(text) is str and 0 < len(text) <= 4096 and bool(text.strip())
            and all(unicodedata.category(c) not in ('Cc','Cf','Cs') for c in text), 'INVALID_TEXT')
    if 'confirmed' in obj:
        require(type(obj['confirmed']) is bool, 'INVALID_CONFIRMATION')
    timestamp(obj['acquired_at'])
    if 'source_timestamp' in obj:
        timestamp(obj['source_timestamp'])
    provenance = obj['provenance']
    require(type(provenance) is dict and set(provenance) == {'method','collector','origin_status'}, 'PROVENANCE_FIELDS')
    require(type(provenance['collector']) is str and TOKEN.fullmatch(provenance['collector']), 'INVALID_COLLECTOR')
    expected = ('synthetic-fixture','SYNTHETIC') if mode == 'synthetic' else ('external-supplied','CLAIMED_UNVERIFIED')
    require(provenance['method'] == expected[0] and provenance['origin_status'] == expected[1], 'ORIGIN_NOT_SUPPORTED')
    require(not (mode == 'external' and sha(str(fact_id).encode('ascii')) == HISTORICAL_REFUSAL_SHA), 'HISTORICAL_TARGET_FORBIDDEN')
    return obj


def validate_order(a, b):
    require(a['observation_id'] != b['observation_id'], 'DUPLICATE_OBSERVATION')
    require(timestamp(b['acquired_at']) > timestamp(a['acquired_at']), 'ACQUISITION_ORDER')
    if 'source_timestamp' in a and 'source_timestamp' in b:
        require(timestamp(b['source_timestamp']) >= timestamp(a['source_timestamp']), 'SOURCE_ORDER')


def exclusive_write(path, raw):
    path = safe_path(path)
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _receipt(capture, sequence, previous):
    body = {'contract':'H5_EVIDENCE_V1','sequence':sequence,'previous_sha256':previous,
            'capture':capture,'capture_sha256':sha(canonical(capture))}
    return body | {'receipt_sha256':sha(canonical(body))}


def acquire(a_path, b_path, run, *, mode, fact_id, scope, fault=None):
    """Validate both before publication; interrupted writes remain fail-closed."""
    run = safe_path(run)
    require(not run.exists(), 'STORE_EXISTS')
    a = validate_capture(read_bytes(a_path), mode=mode, stage='A', fact_id=fact_id, scope=scope)
    b = validate_capture(read_bytes(b_path), mode=mode, stage='B', fact_id=fact_id, scope=scope)
    validate_order(a, b)
    run.mkdir(parents=True, exist_ok=False)
    hashes = {}
    previous = None
    for seq, capture in enumerate((a,b), 1):
        raw = canonical(_receipt(capture, seq, previous))
        name = f'{seq:06d}.json'
        exclusive_write(run/name, raw)
        previous = sha(raw)
        hashes[name] = previous
        if fault:
            fault('after_'+capture['stage'])
    if fault:
        fault('before_seal')
    seal = canonical({'contract':'H5_PAIR_V1','mode':mode,'fact_id':fact_id,
                      'scope':scope,'records':hashes})
    exclusive_write(run/'PAIR.json', seal)
    return {'mode':mode,'pair_sha256':sha(seal),'acquisition_pid':os.getpid(),
            'run':str(run),'captures':2,'authority':'NONE'}


def load_pair(run, pair_sha256):
    run = safe_path(run)
    require(type(pair_sha256) is str and HEX.fullmatch(pair_sha256), 'INVALID_PAIR_ANCHOR')
    require(run.is_dir() and {p.name for p in run.iterdir()} == {'000001.json','000002.json','PAIR.json'}, 'INCOMPLETE_PAIR')
    seal_raw = read_bytes(run/'PAIR.json')
    require(sha(seal_raw) == pair_sha256, 'PAIR_HASH_MISMATCH')
    seal = parse(seal_raw)
    require(type(seal) is dict and set(seal) == {'contract','mode','fact_id','scope','records'}
            and seal['contract'] == 'H5_PAIR_V1', 'PAIR_CONTRACT')
    require(type(seal['records']) is dict and set(seal['records']) == {'000001.json','000002.json'}, 'PAIR_CONTRACT')
    captures = []
    previous = None
    for seq, stage in enumerate(('A','B'),1):
        name = f'{seq:06d}.json'
        raw = read_bytes(run/name, 32768)
        require(sha(raw) == seal['records'][name], 'RECORD_HASH_MISMATCH')
        receipt = parse(raw)
        require(type(receipt) is dict and set(receipt) == {'contract','sequence','previous_sha256','capture','capture_sha256','receipt_sha256'}, 'RECORD_CONTRACT')
        body = {k:v for k,v in receipt.items() if k != 'receipt_sha256'}
        require(receipt['contract'] == 'H5_EVIDENCE_V1' and type(receipt['sequence']) is int
                and receipt['sequence'] == seq and receipt['previous_sha256'] == previous
                and receipt['receipt_sha256'] == sha(canonical(body)), 'RECORD_CHAIN_MISMATCH')
        capture = validate_capture(canonical(receipt['capture']),mode=seal['mode'],stage=stage,
                                   fact_id=seal['fact_id'],scope=seal['scope'])
        require(receipt['capture_sha256'] == sha(canonical(capture)), 'CAPTURE_HASH_MISMATCH')
        require(raw == canonical(receipt), 'NONCANONICAL_EVIDENCE')
        captures.append(capture)
        previous = sha(raw)
    validate_order(*captures)
    require(seal_raw == canonical(seal), 'NONCANONICAL_EVIDENCE')
    return captures


def observed_answer(capture, prefix='The latest observed text is: '):
    confirmation = ('confirmed by the supplied source (not established truth)' if capture.get('confirmed') is True
                    else 'unconfirmed in the supplied source' if capture.get('confirmed') is False
                    else 'confirmation was not provided')
    return prefix+capture['text']+' It is '+confirmation+'.'


def project_single(capture):
    """One validated observation. Never duplicate it into the pair contract."""
    c = validate_capture(canonical(capture), mode=capture['mode'], stage='A',
                         fact_id=capture['fact_id'], scope=capture['scope'])
    return {'question':'What matters now?',
            'answer':observed_answer(c, 'One supplied observation reports: '),
            'observation':c, 'observation_count':1,
            'change_status':'NOT_ASSESSED_SINGLE_OBSERVATION',
            'mode':c['mode'], 'origin_status':c['provenance']['origin_status'],
            'authority':'NONE', 'actions_taken':[],
            'classification':'H5_SINGLE_SELECTED_OBSERVATION_NOT_NATIVE_REFLECTION_OR_BETWEEN',
            'uncertainty':['Only one observation is retained; change, no-change, correction and withdrawal are not assessed.',
                           'Confirmation is source-reported, not established truth.',
                           'Source creation time is not an update time; absent or ambiguous source clocks remain unknown.',
                           'Bee/device origin is not independently authenticated by this reader.',
                           'No live synchronization or autonomous action is performed.'],
            'challenge':'Inspect the one retained observation and its provenance; this interpretation is challengeable.'}


def project(a, b):
    """Bounded source-reported comparison, never native Reflection or Between."""
    changes = []
    if a['text'] != b['text']:
        changes.append('text')
    if ('confirmed' in a, a.get('confirmed')) != ('confirmed' in b, b.get('confirmed')):
        changes.append('confirmation')
    answer = observed_answer(b)
    if not changes:
        answer = 'No meaningful text or confirmation change was observed. '+answer
    return {'question':'What matters now?','answer':answer,'changes':changes,
            'meaningful_change':bool(changes),'original':a,'latest':b,'mode':b['mode'],
            'origin_status':b['provenance']['origin_status'],'authority':'NONE','actions_taken':[],
            'classification':'H5_SELECTED_FIELD_RULE_BASED_COMPARISON_NOT_NATIVE_REFLECTION_OR_BETWEEN',
            'uncertainty':['Fictional fixtures; no genuine Bee origin.' if b['mode']=='synthetic'
                           else 'External-file Bee origin and human edit authorization are not independently authenticated.',
                           'Confirmation is source-reported, not automatic truth.',
                           'Acquisition order is supplied, not proof of causation; absent source clocks remain unknown.',
                           'No live Bee retrieval or synchronization is performed by this sidecar.'],
            'challenge':'Compare both retained observations and their provenance; this interpretation is challengeable.'}


def store_hashes(run):
    return {p.name:sha(read_bytes(p,32768)) for p in sorted(run.iterdir())}


def human(view):
    a,b=view['original'],view['latest']
    label = 'SYNTHETIC DEMONSTRATION — fictional Bee-style observations; no live Bee calls.' if view['mode']=='synthetic' else 'EXTERNAL CAPTURE — supplied files; Bee origin and edit authorization unverified.'
    status = lambda c: 'confirmed' if c.get('confirmed') is True else 'unconfirmed' if c.get('confirmed') is False else 'confirmation not provided'
    return '\n'.join([label,'','ORIGINAL EVIDENCE',a['text']+' ['+status(a)+']',
                      'CHANGE',('Changed: '+', '.join(view['changes'])+'. Earlier evidence preserved.') if view['changes'] else 'No meaningful text or confirmation change observed.',
                      '','What matters now?',view['answer'],'','WHY / HISTORY',
                      'Before: '+a['text'],'After: '+b['text'],
                      f"Source: selected Bee-style Fact {b['fact_id']}; scope {b['scope']}.",
                      f"Supplied acquisition times: {a['acquired_at']} → {b['acquired_at']}.",
                      'Origin: '+view['origin_status']+'.',
                      'Uncertainty: '+' '.join(view['uncertainty']),view['challenge'],
                      'Authority: NONE. No actions taken.'])


def demo():
    run = ROOT/'runs'/('synthetic-'+uuid.uuid4().hex)
    prefix = [sys.executable,'-X','utf8','-I','-B',str(ROOT/'h5_sidecar.py'),'--json']
    result = subprocess.run([*prefix,'acquire','--a',str(ROOT/'fixtures/A.json'),
                            '--b',str(ROOT/'fixtures/B.json'),'--run',str(run),
                            '--mode','synthetic','--fact-id','900000001','--scope','DEMO/H5/synthetic'],
                            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=15)
    require(result.returncode == 0, 'ACQUISITION_CHILD_FAILED')
    acquisition = parse(result.stdout.encode())
    before = store_hashes(run)
    # subprocess.run has waited for acquisition exit before the new reader starts.
    reader = subprocess.run([*prefix,'ask','--run',str(run),'--pair-sha256',acquisition['pair_sha256']],
                            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=15)
    require(reader.returncode == 0, 'READER_CHILD_FAILED')
    recovered = parse(reader.stdout.encode())
    require(before == store_hashes(run), 'READER_MUTATED_EVIDENCE')
    require(len({os.getpid(),acquisition['acquisition_pid'],recovered['reader_pid']}) == 3, 'FRESH_PROCESS_NOT_PROVEN')
    record = {'format':'H5_FRESH_PROCESS_V1','wrapper_pid':os.getpid(),
              'acquisition_pid':acquisition['acquisition_pid'],'reader_pid':recovered['reader_pid'],
              'acquisition_exited_before_reader':True,'reader_preserved_evidence':True,
              'child_exit_codes':[result.returncode,reader.returncode],
              'pair_sha256':acquisition['pair_sha256'],'run':str(run),
              'before_reader':before,'after_reader':store_hashes(run),'view':recovered['view']}
    path = ROOT/'evidence'/('fresh-process-'+uuid.uuid4().hex+'.json')
    path.parent.mkdir(exist_ok=True)
    exclusive_write(path,canonical(record))
    return record


def install_guard():
    """CLI capability guard, not protection from hostile in-process Python."""
    global _guard_installed
    if _guard_installed:
        return
    runtime = Path(sys.base_prefix).resolve()
    def guard(event, args):
        if event.startswith(('socket.','winreg.')) or event in ('os.system','os.startfile','sqlite3.connect'):
            raise PermissionError('H5 capability denied')
        if event == 'open' and not isinstance(args[0],int):
            path = Path(args[0]).resolve()
            mode,flags = args[1],args[2]
            write = (isinstance(mode,str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
            if not path.is_relative_to(ROOT) and (write or not path.is_relative_to(runtime)):
                raise PermissionError('H5 file capability denied')
        if event in ('os.mkdir','os.remove','os.rmdir') and not Path(args[0]).resolve().is_relative_to(ROOT):
            raise PermissionError('H5 write capability denied')
        if event in ('os.rename','os.replace') and not all(Path(p).resolve().is_relative_to(ROOT) for p in args[:2]):
            raise PermissionError('H5 write capability denied')
    sys.addaudithook(guard)
    _guard_installed = True


def main():
    parser = argparse.ArgumentParser(description='H5 isolated two-observation sidecar; no Bee calls')
    parser.add_argument('--json',action='store_true')
    commands = parser.add_subparsers(dest='command')
    commands.add_parser('demo')
    commands.add_parser('historical')
    acquire_parser = commands.add_parser('acquire')
    for name in ('a','b','run','scope'):
        acquire_parser.add_argument('--'+name,required=True)
    acquire_parser.add_argument('--mode',choices=MODES,required=True)
    acquire_parser.add_argument('--fact-id',type=int,required=True)
    ask = commands.add_parser('ask')
    ask.add_argument('--run',required=True);ask.add_argument('--pair-sha256',required=True)
    args = parser.parse_args()
    install_guard()
    try:
        if args.command == 'acquire':
            value = acquire(args.a,args.b,args.run,mode=args.mode,fact_id=args.fact_id,scope=args.scope)
        elif args.command == 'ask':
            a,b = load_pair(args.run,args.pair_sha256)
            value = {'reader_pid':os.getpid(),'view':project(a,b)}
        elif args.command == 'historical':
            value = {'mode':'historical-replay-handoff','executed':False,'authority':'NONE',
                     'message':'Historical deterministic replay remains the separate preserved H4/H3 fallback. No live Bee calls. H5 does not execute or write to H4.',
                     'launcher':'Historical replay is excluded; see README.md'}
        else:
            value = demo()
        if args.json or args.command == 'acquire':
            print(canonical(value).decode())
        elif args.command == 'historical':
            print(value['message']+'\nSeparate fallback: '+value['launcher'])
        else:
            if args.command != 'ask':
                print('Acquisition process exited. Starting condition recovered by a fresh process.\n')
            print(human(value['view']))
        return 0
    except Stop as exc:
        print('STOP: '+str(exc),file=sys.stderr)
    except (OSError,ValueError,TypeError,KeyError,RecursionError,subprocess.SubprocessError):
        print('STOP: LOCAL_IO_OR_FORMAT_FAILURE',file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
