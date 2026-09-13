import sys
from pathlib import Path

# Add src and root to sys.path so tests can import modules from src/ and ml/
root_path = str(Path(__file__).resolve().parent.parent)
src_path = str(Path(__file__).resolve().parent.parent / "src")
if root_path not in sys.path:
    sys.path.insert(0, root_path)
if src_path not in sys.path:
    sys.path.insert(0, src_path)
