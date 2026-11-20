import sys
from pathlib import Path

# make `import schemas`, `import validate_questions` work from the tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
