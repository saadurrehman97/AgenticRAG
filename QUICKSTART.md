# Quick Start Guide

Get up and running with the Mini Agentic RAG System in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- OpenAI API key

## Installation Steps

### 1. Clone and Navigate

```bash
cd "Agentic RAG"
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Unix/MacOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Optional: Install spaCy Model

For better entity extraction (recommended):

```bash
python -m spacy download en_core_web_sm
```

If this fails, the system will fall back to pattern-based extraction.

### 5. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your OpenAI API key
# On Windows: notepad .env
# On Unix/MacOS: nano .env
```

Add your API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

## Running the System

### Interactive Mode (Chat Interface)

```bash
python -m src.cli
```

You'll see:
```
🤖 Mini Agentic RAG System with LangGraph
═══════════════════════════════════════

Commands:
  /help    - Show help message
  /history - Show conversation history
  /exit    - Exit the system

Type your question and press Enter.
═══════════════════════════════════════

💬 You:
```

### Example Queries

Try these queries:

```
What is AuthService?

Which projects depend on AuthService?

Summarize the authentication subsystem

How many services are in the knowledge graph?

What services does PaymentRouter depend on?

Which project uses PaymentRouter and what authentication does it use?
```

### Single Query Mode

```bash
python -m src.cli --query "What is AuthService?"
```

### Run Tests

```bash
python test_challenge_questions.py
```

## Understanding the Output

When you ask a question, you'll see:

```
💬 You: What is AuthService?
🤔 Processing...

───────────────────────────────────────
📝 ANSWER:
───────────────────────────────────────
[AI-generated answer with citations]

🔍 EXECUTION DETAILS:
───────────────────────────────────────

• Router Decision: retrieve
• Retrieved Chunks: 5
• Tools Used: None

• Steps Executed:
  1. Router decided: retrieve
  2. Retrieved 5 relevant chunks using graph-aware retrieval
  3. Generated final answer using LLM reasoning
───────────────────────────────────────
```

## Troubleshooting

### "OpenAI API key not found"

Make sure you:
1. Created the `.env` file
2. Added your API key: `OPENAI_API_KEY=sk-...`
3. Key starts with `sk-`

### "Data directory not found"

The `data/` directory should contain sample documents. Make sure you're in the correct directory:
```bash
ls data/  # Should show .md files
```

### "spaCy model not found"

This is a warning, not an error. The system will work with pattern-based entity extraction. To fix:
```bash
python -m spacy download en_core_web_sm
```

### Knowledge Graph Not Building

If you see entity extraction errors:
```bash
# Rebuild the graph
python -m src.cli --rebuild-graph
```

### ImportError or ModuleNotFoundError

Make sure you:
1. Activated the virtual environment
2. Installed all requirements: `pip install -r requirements.txt`

## Next Steps

1. **Explore the README.md** for detailed architecture and design decisions
2. **Run challenge tests** to see the system handle complex queries
3. **Add your own documents** to the `data/` directory
4. **Experiment with different queries** to test multi-hop reasoning

## Commands Cheat Sheet

```bash
# Setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run
python -m src.cli                          # Interactive
python -m src.cli --query "your question"  # Single query
python -m src.cli --rebuild-graph          # Rebuild graph

# Test
python test_challenge_questions.py

# Help
python -m src.cli --help
```

## Sample Session

```
💬 You: What is AuthService?

📝 ANSWER:
AuthService is a core authentication and authorization service that provides
centralized authentication capabilities including user login/registration, JWT
token management, OAuth 2.0 integration, and role-based access control.
According to authentication_service.md, it is used by multiple projects
including ProjectAlpha, ProjectBeta, ProjectGamma, and AnalyticsModule.

───────────────────────

💬 You: Which projects depend on it?

📝 ANSWER:
Based on the knowledge graph, the following projects depend on AuthService:
1. ProjectAlpha - Main customer-facing application
2. ProjectBeta - Internal admin dashboard
3. ProjectGamma - Mobile application backend
4. AnalyticsModule - For tracking authenticated user behavior

───────────────────────

💬 You: /exit

Goodbye! 👋
```

## Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review the [Architecture section](README.md#architecture)
- See [Design Decisions](README.md#design-decisions) for rationale
- Look at [Limitations](README.md#limitations) for known issues

Happy querying! 🚀
