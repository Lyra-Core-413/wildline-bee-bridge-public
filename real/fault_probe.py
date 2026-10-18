"""Verification-only process death after B persistence, before pair publication."""
import importlib.util
import os
from pathlib import Path
import sys

root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('h5',root/'h5_sidecar.py')
h5=importlib.util.module_from_spec(spec);spec.loader.exec_module(h5)
h5.acquire(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]),mode='synthetic',
           fact_id=900000001,scope='DEMO/H5/synthetic',
           fault=lambda phase: os._exit(74) if phase=='before_seal' else None)
