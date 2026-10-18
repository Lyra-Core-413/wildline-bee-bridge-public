"""Verification-only denied operations; no connection or private read occurs."""
import importlib.util
from pathlib import Path
import socket

root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('h5',root/'h5_sidecar.py')
h5=importlib.util.module_from_spec(spec);spec.loader.exec_module(h5)
h5.install_guard()
network_denied=external_file_denied=False
try:socket.socket()
except PermissionError:network_denied=True
try:open(root.parent/'h5-outside-denial-control.txt','rb')
except PermissionError:external_file_denied=True
print(h5.canonical({'network_denied':network_denied,'external_file_denied':external_file_denied}).decode())
