import sys
from pathlib import Path

# Add parent directory to path so tests can import app module
sys.path.insert(0, str(Path(__file__).parent.parent))

