import os

def ensure_workspace(workspace):
    os.makedirs(workspace, exist_ok=True) 