"""Windows owner/SYSTEM-only operation folders outside package and Git roots."""
import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path
import re
import stat

PACKAGE=Path(__file__).resolve().parent
def require(ok,code):
    if not ok:raise ValueError(code)
def _api():
    require(os.name=='nt','WINDOWS_REQUIRED')
    k=c.WinDLL('kernel32',use_last_error=True);a=c.WinDLL('advapi32',use_last_error=True)
    def bind(d,name,args,result):
        f=getattr(d,name);f.argtypes=args;f.restype=result;return f
    bind(k,'GetCurrentProcess',[],w.HANDLE);bind(k,'CloseHandle',[w.HANDLE],w.BOOL)
    bind(k,'LocalFree',[c.c_void_p],c.c_void_p)
    bind(a,'OpenProcessToken',[w.HANDLE,w.DWORD,c.POINTER(w.HANDLE)],w.BOOL)
    bind(a,'GetTokenInformation',[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.POINTER(w.DWORD)],w.BOOL)
    bind(a,'ConvertSidToStringSidW',[c.c_void_p,c.POINTER(w.LPWSTR)],w.BOOL)
    bind(a,'ConvertStringSecurityDescriptorToSecurityDescriptorW',[w.LPCWSTR,w.DWORD,c.POINTER(c.c_void_p),c.POINTER(w.DWORD)],w.BOOL)
    bind(a,'ConvertSecurityDescriptorToStringSecurityDescriptorW',[c.c_void_p,w.DWORD,w.DWORD,c.POINTER(w.LPWSTR),c.POINTER(w.DWORD)],w.BOOL)
    bind(a,'GetNamedSecurityInfoW',[w.LPCWSTR,c.c_int,w.DWORD,c.POINTER(c.c_void_p),c.POINTER(c.c_void_p),c.POINTER(c.c_void_p),c.POINTER(c.c_void_p),c.POINTER(c.c_void_p)],w.DWORD)
    return k,a
def _descriptor():
    k,a=_api();token=w.HANDLE()
    require(a.OpenProcessToken(k.GetCurrentProcess(),8,c.byref(token)),'PRIVATE_ACL_UNVERIFIED')
    try:
        size=w.DWORD();a.GetTokenInformation(token,1,None,0,c.byref(size))
        require(0<size.value<65536,'PRIVATE_ACL_UNVERIFIED')
        buf=c.create_string_buffer(size.value)
        require(a.GetTokenInformation(token,1,buf,size,c.byref(size)),'PRIVATE_ACL_UNVERIFIED')
        sid=c.cast(buf,c.POINTER(c.c_void_p))[0];text=w.LPWSTR()
        require(a.ConvertSidToStringSidW(sid,c.byref(text)),'PRIVATE_ACL_UNVERIFIED')
        try:owner=text.value
        finally:k.LocalFree(c.cast(text,c.c_void_p))
    finally:k.CloseHandle(token)
    sd=c.c_void_p();sddl='O:'+owner+'D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;'+owner+')'
    require(a.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,1,c.byref(sd),None),'PRIVATE_ACL_UNVERIFIED')
    return k,a,sd
def _string(a,k,sd):
    text=w.LPWSTR()
    require(a.ConvertSecurityDescriptorToStringSecurityDescriptorW(sd,1,5,c.byref(text),None),'PRIVATE_ACL_UNVERIFIED')
    try:return text.value
    finally:k.LocalFree(c.cast(text,c.c_void_p))
def check_acl(path):
    k,a,expected=_descriptor();actual=c.c_void_p()
    try:
        code=a.GetNamedSecurityInfoW(str(path),1,5,None,None,None,None,c.byref(actual))
        require(code==0,'PRIVATE_ACL_UNVERIFIED')
        require(_string(a,k,actual)==_string(a,k,expected),'PRIVATE_ACL_UNVERIFIED')
    finally:
        if actual:k.LocalFree(actual)
        k.LocalFree(expected)
def _no_links(path):
    for part in (path,*path.parents):
        if part.exists() or part.is_symlink():
            info=part.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'PRIVATE_PATH_UNSAFE')
            if stat.S_ISREG(info.st_mode):require(info.st_nlink==1,'PRIVATE_PATH_UNSAFE')
def drive_type(anchor):
    require(os.name=='nt','WINDOWS_REQUIRED')
    k=c.WinDLL('kernel32',use_last_error=True)
    k.GetDriveTypeW.argtypes=[w.LPCWSTR];k.GetDriveTypeW.restype=w.UINT
    return k.GetDriveTypeW(str(anchor))
def require_local(path,code='PRIVATE_PATH_UNSAFE'):
    path=Path(path)
    require(path.is_absolute() and len(path.drive)==2 and not str(path).startswith('\\\\'),code)
    require(drive_type(path.anchor)==3,code) # DRIVE_FIXED; reject mapped/remote/unknown drives before I/O.
    return path
def check_root(value):
    path=require_local(value)
    _no_links(path);path=require_local(path.resolve())
    # Also exclude the package's sibling private verification/assembly tree.
    forbidden=PACKAGE.parent.resolve()
    require(not path.is_relative_to(forbidden) and not forbidden.is_relative_to(path),'PRIVATE_LOCATION_REQUIRED')
    require(all(not (p/'.git').exists() for p in (path,*path.parents)),'PRIVATE_LOCATION_REQUIRED')
    require(path.parent.is_dir(),'PRIVATE_PARENT_MISSING')
    if path.exists():require(path.is_dir(),'PRIVATE_PATH_UNSAFE')
    return path
def make_dir(path):
    k,a,sd=_descriptor()
    class SA(c.Structure):_fields_=[('nLength',w.DWORD),('lpSecurityDescriptor',c.c_void_p),('bInheritHandle',w.BOOL)]
    attributes=SA(c.sizeof(SA),sd,False)
    k.CreateDirectoryW.argtypes=[w.LPCWSTR,c.POINTER(SA)];k.CreateDirectoryW.restype=w.BOOL
    try:require(k.CreateDirectoryW(str(path),c.byref(attributes)),'PRIVATE_DIRECTORY_CREATE_FAILED')
    finally:k.LocalFree(sd)
    check_acl(path);return path
def make_root(value):
    path=check_root(value)
    if path.exists():check_acl(path)
    else:make_dir(path)
    return path
def operation(root,identifier):
    root=check_root(root);check_acl(root)
    require(type(identifier) is str and re.fullmatch(r'[a-f0-9]{32}',identifier),'PRIVATE_OPERATION_UNSAFE')
    folder=root/identifier;_no_links(folder)
    if folder.exists():require(folder.is_dir(),'PRIVATE_OPERATION_UNSAFE');check_acl(folder)
    return folder
def safe(path,root):
    root=check_root(root);check_acl(root)
    path=Path(path).absolute();_no_links(path)
    require(path.resolve().is_relative_to(root) and path.resolve()!=root,'OUTPUT_PATH_UNSAFE')
    return path
def default_root():
    base=os.environ.get('LOCALAPPDATA');require(bool(base),'PRIVATE_ROOT_REQUIRED')
    return check_root(Path(base)/'WildlineBeeContinuity')
