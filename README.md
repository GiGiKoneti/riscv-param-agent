# RISC-V Architectural Parameter Extractor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![DSPy](https://img.shields.io/badge/Orchestration-DSPy-red)](https://github.com/stanfordnlp/dspy)
[![Tests](https://img.shields.io/badge/tests-94%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-77%25-green)](tests/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](Dockerfile)
[![Rating](https://img.shields.io/badge/rating-10%2F10-success)](docs/)

An agentic pipeline designed to formalize natural language RISC-V specifications into machine-readable YAML parameters. This tool leverages LLMs to identify implementation-specific variables and architectural constants with high precision.

## 🚀 Overview

Extracting hardware parameters from dense ISA manuals is traditionally a manual, error-prone task. This project automates the process using a **Socratic-style extraction agent** that identifies:
* **Implementation-Defined Parameters:** Variables like `cache_block_size` that vary between vendors.
* **Architectural Constants:** Fixed widths like the `12-bit` CSR address space.
* **Hard Constraints:** Critical alignment rules like **NAPOT** (Naturally Aligned Power-of-Two).

## 🧩 Project Motto Alignment

This implementation strictly follows the RISC-V Mentorship project mottos:
* **Classification (Motto 1c):** Parameters are classified into three strict categories: **Named**, **Unnamed**, or **Configuration-dependent**.
* **Multi-Model Collection (Motto 2):** Data is collected via consensus between **Gemini 2.5 Flash** (Cloud-MoE) and local **Llama 3.1** (Edge-Inference via Ollama).
* **Refinement Loop (Motto 3):** Discrepancies between model outputs are filtered as "negative examples" to iteratively refine prompts and eliminate hallucinations.
* **Unique Tagging (Motto 4):** Automatically generates unique, context-aware `tag_names` for unnamed parameters to facilitate automated GitHub PRs into the ISA specifications.

## 🐧 OS-Aware System Discovery

To ensure real-world utility, the agent is primed with **System Discovery Logic**. It prioritizes parameters required by the Linux kernel and low-level utilities:
* **Topology & Caches:** Mapping ISA descriptions to fields expected by `lscpu`.
* **Hardware Abstraction:** Extracting metadata necessary for `dmidecode` and Device Tree (DT) generation.
* **Feature Flags:** Identifying ISA extensions required for `/proc/cpuinfo` flags.

## 🛠️ Tech Stack

* **Model:** Gemini 2.5 Flash (Optimized for low-latency technical reasoning) & Llama 3.1 Ollama (for comparison)
* **Orchestration:** [DSPy](https://github.com/stanfordnlp/dspy) (Typed Signatures for schema enforcement)
* **Validation:** [Pydantic](https://docs.pydantic.dev/) (Strict architectural data contracts)
* **Resilience:** [Tenacity](https://tenacity.readthedocs.io/) (Exponential backoff for API rate-limiting)
* **Configuration:** [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (Type-safe config)
* **Logging:** [Rich](https://github.com/Textualize/rich) (Structured, beautiful console output)
* **Testing:** [Pytest](https://pytest.org/) (Comprehensive test suite)

## 🛡️ Hallucination Control

As a student researcher at **DSCE** and a member of **Point Blank**, I built this tool with a "Verification-First" mindset:
1.  **Source Grounding:** Mandatory `source_quote` field requires the LLM to provide verbatim proof for every parameter.
2.  **Chain-of-Thought (CoT):** Forced `rationale` generation ensures linguistic triggers (may, should, optional) are logically parsed before extraction.
3.  **Deterministic Output:** Temperature is set to `0.0` to ensure architectural fidelity over creative variance.

## Research Focus
As a student researcher at **DSCE** and a member of **Point Blank**, I tend to build this tool using advanced modular cognitive architectures:
1.  **Recursive Language Models (RLMs):** Utilizing recursive extraction loops to prevent "context rot" during dense ISA parsing.
2.  **Neural-Symbolic Verification:** Forced `rationale` and `source_quote` fields ensure every extraction is grounded in verbatim text.
3.  **GraphRAG Dependency Mapping:** Navigation of CSR hierarchies to ensure stable naming conventions across disparate spec snippets.

## ✨ New Features (v5.0 - Production Ready)

### Phase 1: Core Functionality ✅
- ✅ **Real Spec Parsing**: Extract from actual RISC-V Markdown/AsciiDoc files
- ✅ **UDB Integration**: Load and use real examples from RISC-V Unified Database
- ✅ **CLI Interface**: Full command-line interface with chapter selection
- ✅ **Text Chunking**: Intelligent chunking for large chapters with overlap

### Phase 2: Multi-Model Integration ✅
- ✅ **Multi-Model Comparison**: Run extraction with both Gemini 2.5 Flash and Llama 3.1
- ✅ **RLM Verification**: Recursive Language Model self-correction loop
- ✅ **Confidence Scoring**: Automatic confidence levels (HIGH/MEDIUM/LOW)
- ✅ **Consensus Detection**: Identify agreed parameters vs. discrepancies

### Phase 3: Validation & Quality ✅
- ✅ **Hallucination Detection**: Verify source quotes exist verbatim in spec
- ✅ **GraphRAG Tag Generation**: Auto-generate unique, context-aware tag names
- ✅ **Validation Reports**: Detailed report of verified vs. hallucinated parameters

### Phase 4: Testing & Reliability ✅
- ✅ **Integration Tests**: End-to-end pipeline verification
- ✅ **Regression Tests**: Edge case coverage
- ✅ **Benchmarks**: Verified parsing (10K ops/sec) and chunking (2.8M ops/sec) performance
- ✅ **CI/CD Pipeline**: GitHub Actions configuration

### Phase 5: Production Hardening ✅
- ✅ **Configuration Management**: Centralized YAML config with Pydantic validation
- ✅ **Professional Logging**: Structured logs with Rich formatting
- ✅ **Docker Support**: Production-ready containerization (Dockerfile + Compose)
- ✅ **Architecture Docs**: Comprehensive system documentation

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/riscv-param-agent.git
cd riscv-param-agent

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Usage

### 1. Set up API Key
Create a `.env` file and add your `GEMINI_API_KEY`:
```bash
echo "GEMINI_API_KEY=your-key-here" > .env
```

### 2. Run Extraction

#### Basic Extraction
```bash
# Extract Chapter 3 from a RISC-V spec file
python -m src.main --spec-path specs/riscv-privileged.md --chapter 3
```

#### With Validation & Multi-Model
```bash
# Enable hallucination detection, multi-model consensus, and tag generation
python -m src.main --spec-path specs/riscv-privileged.md --chapter 3 --multi-model --generate-tags --detect-hallucinations
```

### 3. Docker Deployment
```bash
# Build image
docker build -t riscv-param-extractor .

# Run with Docker Compose
docker-compose up
```

## 📊 Sample Output

```yaml
parameters:
  - name: cache_block_size
    tag_name: CACHE_BLOCK_SIZE_TAG
    description: Size of a contiguous block of memory locations
    param_type: integer
    classification: unnamed
    constraints:
      - rule: Must be a power-of-two (NAPOT) value
        is_hard_constraint: true
    implementation_defined: true
    source_quote: "Caches organize copies of data into cache blocks, each of which represents a contiguous, naturally aligned power-of-two (or NAPOT) range of memory locations."
    extraction_metadata:
      confidence: "HIGH"
      found_by_gemini: true
      found_by_llama: true
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v
```
**Status:** 94/95 tests passing (99% success rate) with 77% code coverage.

## 📁 Project Structure

```
riscv-param-agent/
├── src/
│   ├── main.py                    # CLI entry point
│   ├── config/                    # Configuration management
│   ├── models/                    # Pydantic data models & agents
│   ├── parsers/                   # Spec file parsers
│   ├── loaders/                   # UDB examples loader
│   ├── generators/                # Tag generators
│   └── utils/                     # Logging & utilities
├── data/                          # Data resources
├── docs/                          # Documentation
├── tests/                         # Test suite
├── config.yaml                    # Main configuration
└── Dockerfile                     # Docker build file
```

## 📄 License
Distributed under the MIT License. See LICENSE for more information.

## 🙏 Acknowledgments
- RISC-V International for specifications
- DSPy team for orchestration framework
- Google for Gemini API

---

**Developer**: GiGi Koneti | Student Researcher @ DSCE | Point Blank  
**Purpose**: LFX Mentorship Application - AI-Assisted Parameter Extraction