# Installation Guide

## Step-by-Step Installation

### 1. Upgrade pip (Important!)

First, upgrade pip to the latest version to avoid dependency resolution issues:

```bash
python -m pip install --upgrade pip
```

### 2. Install Dependencies

Try installing with the updated pip:

```bash
pip install -r requirements.txt
```

### Alternative Installation (If Above Fails)

If you encounter dependency conflicts, try installing in stages:

#### Option A: Install Core Packages First

```bash
# Install core LangChain packages
pip install langchain-core>=0.3.0
pip install langsmith>=0.1.0
pip install orjson>=3.9.14

# Install LangChain ecosystem
pip install langchain>=0.3.0
pip install langchain-openai>=0.2.0
pip install langchain-community>=0.3.0
pip install langgraph>=0.2.0

# Install embeddings and vector store
pip install sentence-transformers>=2.2.0
pip install faiss-cpu>=1.7.4

# Install NLP
pip install spacy>=3.7.0
pip install networkx>=3.2

# Install utilities
pip install python-dotenv>=1.0.0
pip install pydantic>=2.0.0
pip install numpy>=1.24.0
pip install tiktoken>=0.5.0
```

#### Option B: Use Conda (Recommended for Windows)

If you have Anaconda or Miniconda:

```bash
# Create conda environment
conda create -n agentic-rag python=3.10
conda activate agentic-rag

# Install packages
pip install -r requirements.txt
```

#### Option C: Minimal Installation (Core Functionality Only)

If you just want to get started quickly, install only the essential packages:

```bash
pip install langchain langchain-openai langgraph
pip install sentence-transformers faiss-cpu
pip install networkx python-dotenv pydantic numpy
```

Note: spaCy is optional - the system will fall back to pattern-based entity extraction.

### 3. Download spaCy Model (Optional but Recommended)

For better entity extraction:

```bash
python -m spacy download en_core_web_sm
```

If this fails, the system will still work using pattern-based extraction.

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your OpenAI API key
# Windows: notepad .env
# Unix/Mac: nano .env
```

Add this line to .env:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 5. Verify Installation

Test that everything is working:

```bash
python -c "import langchain, langgraph, sentence_transformers; print('✅ All core packages installed!')"
```

### 6. Run the System

```bash
python -m src.cli --query "Hello, can you help me?"
```

## Troubleshooting

### Issue: "Cannot install langchain because of conflicting dependencies"

**Solution 1**: Upgrade pip first
```bash
python -m pip install --upgrade pip
```

**Solution 2**: Use a fresh virtual environment
```bash
# Remove old venv
rm -rf venv  # Unix
rmdir /s venv  # Windows

# Create new venv
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix

# Upgrade pip immediately
python -m pip install --upgrade pip

# Install packages
pip install -r requirements.txt
```

**Solution 3**: Install packages one by one (see Option A above)

### Issue: "ImportError: cannot import name 'BaseModel' from 'pydantic'"

**Solution**: Ensure pydantic v2 is installed
```bash
pip install --upgrade pydantic>=2.0.0
```

### Issue: "No module named 'faiss'"

**Solution**: Install faiss-cpu (not faiss-gpu)
```bash
pip install faiss-cpu
```

### Issue: "spaCy model not found"

This is just a warning. The system will work with pattern-based extraction. To fix:
```bash
python -m spacy download en_core_web_sm
```

### Issue: "OpenAI API key not found"

**Solution**: Make sure you created .env file with your API key
```bash
# Check if .env exists
ls .env  # Unix
dir .env  # Windows

# If not, create it
cp .env.example .env

# Add your key
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### Issue: Python version incompatibility

**Solution**: Use Python 3.9, 3.10, or 3.11
```bash
python --version  # Should show 3.9.x, 3.10.x, or 3.11.x
```

If you have an older version, install Python 3.10 from python.org

## Platform-Specific Notes

### Windows

- Use `venv\Scripts\activate` to activate virtual environment
- Use `notepad .env` to edit files
- If you see SSL errors, install certificates: `pip install --upgrade certifi`

### macOS

- Use `source venv/bin/activate`
- May need to install Xcode Command Line Tools: `xcode-select --install`
- Use `nano .env` or `vim .env` to edit files

### Linux

- Use `source venv/bin/activate`
- May need to install python3-venv: `sudo apt-get install python3-venv`
- May need build tools: `sudo apt-get install build-essential`

## Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment activated
- [ ] pip upgraded to latest version
- [ ] All packages installed without errors
- [ ] .env file created with OpenAI API key
- [ ] Test import successful
- [ ] Can run CLI with test query

## Getting Help

If you're still having issues:

1. Check Python version: `python --version`
2. Check pip version: `pip --version`
3. List installed packages: `pip list`
4. Check for conflicting packages: `pip check`
5. Review error messages carefully

Common fixes:
- Start with a fresh virtual environment
- Upgrade pip before installing anything
- Install packages in the order shown in Option A
- Use Python 3.10 (most compatible)

## Quick Start After Installation

Once everything is installed:

```bash
# Activate environment (if not already active)
venv\Scripts\activate  # Windows

# Run the system
python -m src.cli

# Or test with a single query
python -m src.cli --query "What is AuthService?"

# Run the test suite
python test_challenge_questions.py
```

---

**Need more help?** Check the README.md for full documentation or QUICKSTART.md for a simplified guide.
