"""Static package consistency; hashes are not publisher authentication."""
import hashlib
import json
from pathlib import Path
import stat

ROOT=Path(__file__).resolve().parent
def verify():
    def require(ok):
        if not ok:raise ValueError('PACKAGE_INTEGRITY_FAILED')
    try:
        for p in (ROOT,*ROOT.parents):
            s=p.lstat();require(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400)
        manifest=ROOT/'PACKAGE-MANIFEST.json';raw=manifest.read_bytes()
        require(len(raw)<131072)
        anchor=(ROOT/'PACKAGE-ANCHOR.sha256').read_text(encoding='ascii').strip()
        require(hashlib.sha256(raw).hexdigest()==anchor)
        data=json.loads(raw);files=data['files']
        require(data['format']=='WILDLINE_PRIVATE_SINGLE_BRIDGE_V1' and type(files) is dict)
        require(set(files)=={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}
                -{'PACKAGE-MANIFEST.json','PACKAGE-ANCHOR.sha256'})
        for name,pin in files.items():
            p=ROOT/name
            require(p.resolve().is_relative_to(ROOT) and not p.is_symlink())
            for part in (p,*p.parents):
                s=part.lstat();require(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400)
                if part==ROOT:break
            require(p.stat().st_nlink==1)
            raw=p.read_bytes();require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'])
        return anchor
    except (OSError,ValueError,KeyError,TypeError):raise ValueError('PACKAGE_INTEGRITY_FAILED') from None
