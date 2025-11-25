"""Setup script for the Mini Agentic RAG System."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentic-rag",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A mini agentic RAG system with LangGraph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agentic-rag",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "agentic-rag=src.cli:main",
        ],
    },
)
