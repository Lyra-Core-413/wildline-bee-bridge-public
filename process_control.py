"""Bounded Windows child containment. Children run only after job assignment."""
import ctypes as c
from contextlib import contextmanager
from ctypes import wintypes as w
import os
import subprocess
import time

class ProcessRefused(ValueError):pass
def require(ok):
    if not ok:raise ProcessRefused('PROCESS_CONTAINMENT_UNVERIFIED')
class Basic(c.Structure):
    _fields_=[('user',c.c_longlong),('job_user',c.c_longlong),('flags',w.DWORD),
      ('min',c.c_size_t),('max',c.c_size_t),('active',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class Extended(c.Structure):
    _fields_=[('basic',Basic),('io',c.c_ulonglong*6),('process_memory',c.c_size_t),
      ('job_memory',c.c_size_t),('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
class Accounting(c.Structure):
    _fields_=[('times',c.c_longlong*4),('faults',w.DWORD),('total',w.DWORD),('active',w.DWORD),('terminated',w.DWORD)]
class Thread(c.Structure):
    _fields_=[('size',w.DWORD),('usage',w.DWORD),('tid',w.DWORD),('pid',w.DWORD),('base',w.LONG),('delta',w.LONG),('flags',w.DWORD)]
class Job:
    def __init__(self):
        require(os.name=='nt');self.k=c.WinDLL('kernel32',use_last_error=True);self.handle=None
        signatures={
          'CreateJobObjectW':([c.c_void_p,w.LPCWSTR],w.HANDLE),
          'SetInformationJobObject':([w.HANDLE,c.c_int,c.c_void_p,w.DWORD],w.BOOL),
          'QueryInformationJobObject':([w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.POINTER(w.DWORD)],w.BOOL),
          'AssignProcessToJobObject':([w.HANDLE,w.HANDLE],w.BOOL),
          'TerminateJobObject':([w.HANDLE,w.UINT],w.BOOL),'CloseHandle':([w.HANDLE],w.BOOL),
          'CreateToolhelp32Snapshot':([w.DWORD,w.DWORD],w.HANDLE),
          'Thread32First':([w.HANDLE,c.POINTER(Thread)],w.BOOL),'Thread32Next':([w.HANDLE,c.POINTER(Thread)],w.BOOL),
          'OpenThread':([w.DWORD,w.BOOL,w.DWORD],w.HANDLE),'ResumeThread':([w.HANDLE],w.DWORD)}
        for name,(args,result) in signatures.items():
            f=getattr(self.k,name);f.argtypes=args;f.restype=result
        self.handle=self.k.CreateJobObjectW(None,None);require(self.handle)
        info=Extended();info.basic.flags=0x2000 # KILL_ON_JOB_CLOSE, no breakaway permission.
        if not self.k.SetInformationJobObject(self.handle,9,c.byref(info),c.sizeof(info)):
            self.k.CloseHandle(self.handle);self.handle=None;require(False)
    def attach_resume(self,process):
        require(self.k.AssignProcessToJobObject(self.handle,w.HANDLE(int(process._handle))))
        snapshot=self.k.CreateToolhelp32Snapshot(4,0)
        require(snapshot and snapshot!=w.HANDLE(-1).value)
        try:
            item=Thread();item.size=c.sizeof(item);ok=self.k.Thread32First(snapshot,c.byref(item));ids=[]
            while ok:
                if item.pid==process.pid:ids.append(item.tid)
                item.size=c.sizeof(item);ok=self.k.Thread32Next(snapshot,c.byref(item))
            require(len(ids)==1) # The process has not executed its initial suspended thread.
            thread=self.k.OpenThread(2,False,ids[0]);require(thread)
            try:require(self.k.ResumeThread(thread)==1)
            finally:self.k.CloseHandle(thread)
        finally:self.k.CloseHandle(snapshot)
    def close(self):
        if self.handle:
            try:
                require(self.k.TerminateJobObject(self.handle,74))
                deadline=time.monotonic()+5
                while True:
                    info=Accounting();require(self.k.QueryInformationJobObject(self.handle,1,c.byref(info),c.sizeof(info),None))
                    if info.active==0:break
                    require(time.monotonic()<deadline);time.sleep(.01)
            finally:
                self.k.CloseHandle(self.handle);self.handle=None
def launch(argv,**kwargs):
    job=Job();process=None
    try:
        kwargs['creationflags']=kwargs.get('creationflags',0)|4 # CREATE_SUSPENDED
        process=subprocess.Popen(argv,**kwargs);job.attach_resume(process)
        return process,job
    except BaseException:
        if process is not None:
            try:process.kill();process.wait(timeout=5)
            except (OSError,subprocess.TimeoutExpired):pass
        job.close();raise

@contextmanager
def owned_launch(argv,**kwargs):
    """Own native child lifetime before yielding it to transport setup."""
    job=Job();process=None
    try:
        kwargs['creationflags']=kwargs.get('creationflags',0)|4
        process=subprocess.Popen(argv,**kwargs);job.attach_resume(process)
        yield process,job
    finally:
        try:job.close()
        finally:
            if process is not None:
                try:process.kill();process.wait(timeout=5)
                except OSError:process.wait(timeout=5)
