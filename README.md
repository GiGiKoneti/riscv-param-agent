# RISC-V Architectural Parameter Extractor 

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![DSPy](https://img.shields.io/badge/Orchestration-DSPy-red)](https://github.com/stanfordnlp/dspy)

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

* **Model:** Gemini 2.5 Flash (Optimized for low-latency technical reasoning) & Llama 3.1 Ollama (for comparision)
* **Orchestration:** [DSPy](https://github.com/stanfordnlp/dspy) (Typed Signatures for schema enforcement)
* **Validation:** [Pydantic](https://docs.pydantic.dev/) (Strict architectural data contracts)
* **Resilience:** [Tenacity](https://tenacity.readthedocs.io/) (Exponential backoff for API rate-limiting)

## 🛡️ Hallucination Control

As a student researcher at **DSCE** and a member of **Point Blank**, I built this tool with a "Verification-First" mindset:
1.  **Source Grounding:** Mandatory `source_quote` field requires the LLM to provide verbatim proof for every parameter.
2.  **Chain-of-Thought (CoT):** Forced `rationale` generation ensures linguistic triggers (may, should, optional) are logically parsed before extraction.
3.  **Deterministic Output:** Temperature is set to `0.0` to ensure architectural fidelity over creative variance.

## Research Focus
As a student researcher at **DSCE** and a member of **Point Blank**, I tend to build  this tool using advanced modular cognitive architectures:
1.  **Recursive Language Models (RLMs):** Utilizing recursive extraction loops to prevent "context rot" during dense ISA parsing.
2.  **Neural-Symbolic Verification:** Forced `rationale` and `source_quote` fields ensure every extraction is grounded in verbatim text.
3.  **GraphRAG Dependency Mapping:** Navigation of CSR hierarchies to ensure stable naming conventions across disparate spec snippets.

## 📦 Installation

```bash
# Clone the repository
git clone [https://github.com/yourusername/riscv-param-agent.git](https://github.com/yourusername/riscv-param-agent.git)
cd riscv-param-agent

# Set up virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Usage

1. Create a `.env` file and add your `GEMINI_API_KEY`.
2. Run the extraction pipeline:
```bash
python -m src.main
```
3. View the results in outputs/extracted_parameters.yaml.

## 📊 Sample Output

```yaml
- name: cache_block_size
  param_type: integer
  constraints:
  - rule: Must be a power-of-two (NAPOT) value
    is_hard_constraint: true
  implementation_defined: true
  source_quote: "represents a contiguous, naturally aligned power-of-two (or NAPOT) range of memory locations."
  ```

  ## 📄 License
  Distributed under the MIT License. See LICENSE for more information.