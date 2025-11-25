"""Verify that the system is properly set up."""

import sys

print("=" * 60)
print("Agentic RAG System - Setup Verification")
print("=" * 60)
print()

# Check Python version
print(f"Python version: {sys.version}")
print()

# Check imports
print("Checking package imports...")
checks = []

try:
    import langchain
    checks.append(("langchain", True, langchain.__version__))
except ImportError as e:
    checks.append(("langchain", False, str(e)))

try:
    import langgraph
    version = getattr(langgraph, '__version__', 'OK')
    checks.append(("langgraph", True, version))
except ImportError as e:
    checks.append(("langgraph", False, str(e)))

try:
    import langchain_openai
    checks.append(("langchain-openai", True, "OK"))
except ImportError as e:
    checks.append(("langchain-openai", False, str(e)))

try:
    import sentence_transformers
    checks.append(("sentence-transformers", True, sentence_transformers.__version__))
except ImportError as e:
    checks.append(("sentence-transformers", False, str(e)))

try:
    import faiss
    checks.append(("faiss-cpu", True, "OK"))
except ImportError as e:
    checks.append(("faiss-cpu", False, str(e)))

try:
    import spacy
    checks.append(("spacy", True, spacy.__version__))
except ImportError as e:
    checks.append(("spacy", False, str(e)))

try:
    import networkx
    checks.append(("networkx", True, networkx.__version__))
except ImportError as e:
    checks.append(("networkx", False, str(e)))

try:
    from dotenv import load_dotenv
    checks.append(("python-dotenv", True, "OK"))
except ImportError as e:
    checks.append(("python-dotenv", False, str(e)))

# Print results
all_passed = True
for name, success, version in checks:
    status = "[OK]  " if success else "[FAIL]"
    print(f"  {status} {name:25s} {version if success else 'NOT INSTALLED'}")
    if not success:
        all_passed = False

print()

# Check .env file
print("Checking configuration...")
import os
from pathlib import Path

env_file = Path(".env")
if env_file.exists():
    print("  [OK]   .env file exists")

    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your_openai_api_key_here":
        print("  [OK]   OPENAI_API_KEY is set")
    else:
        print("  [WARN] OPENAI_API_KEY not configured (edit .env file)")
        all_passed = False
else:
    print("  [FAIL] .env file not found (copy from .env.example)")
    all_passed = False

print()

# Check data directory
data_dir = Path("data")
if data_dir.exists():
    doc_count = len(list(data_dir.glob("*.md")))
    print(f"  [OK]   Data directory exists with {doc_count} markdown files")
else:
    print("  [FAIL] Data directory not found")
    all_passed = False

print()
print("=" * 60)

if all_passed:
    print("SUCCESS: System is ready to use!")
    print()
    print("Next steps:")
    print("  1. Edit .env and add your OPENAI_API_KEY")
    print("  2. Run: python -m src.cli")
    print("  3. Or test with: python test_challenge_questions.py")
else:
    print("ISSUES FOUND: Please fix the above issues before running.")
    print()
    print("Common fixes:")
    print("  - Install missing packages: pip install -r requirements.txt")
    print("  - Create .env file: copy .env.example .env")
    print("  - Add your OpenAI API key to .env")

print("=" * 60)

sys.exit(0 if all_passed else 1)
