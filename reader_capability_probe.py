"""Fictional capability-denial test; creates no socket and reads no external file."""
from pathlib import Path
import socket
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import single_reader as r
r.install_guard(Path(sys.argv[1]))
denied=[]
for action in (lambda:socket.socket(),lambda:open(Path(sys.argv[1]).parent/'fictional-denied.txt','rb')):
    try:action()
    except PermissionError:denied.append(True)
    else:denied.append(False)
print(r.b.engine().canonical({'network_denied':denied[0],'outside_file_denied':denied[1]}).decode())
