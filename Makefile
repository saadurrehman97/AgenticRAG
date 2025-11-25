.PHONY: help install setup test run clean

help:
	@echo "Mini Agentic RAG System - Makefile Commands"
	@echo ""
	@echo "  make install        - Install dependencies"
	@echo "  make setup          - Setup environment and download models"
	@echo "  make test           - Run challenge question tests"
	@echo "  make run            - Run interactive CLI"
	@echo "  make clean          - Clean generated files"
	@echo "  make rebuild-graph  - Rebuild knowledge graph"
	@echo ""

install:
	pip install -r requirements.txt

setup: install
	python -m spacy download en_core_web_sm || echo "Warning: spaCy model download failed"
	@echo ""
	@echo "Setup complete! Don't forget to:"
	@echo "1. Copy .env.example to .env"
	@echo "2. Add your OPENAI_API_KEY to .env"
	@echo ""

test:
	python test_challenge_questions.py --verbose

run:
	python -m src.cli

rebuild-graph:
	python -m src.cli --rebuild-graph

clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf graph/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
