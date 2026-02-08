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

## 🐧 OS-Aware System Discovery

To ensure real-world utility, the agent is primed with **System Discovery Logic**. It prioritizes parameters required by the Linux kernel and low-level utilities:
* **Topology & Caches:** Mapping ISA descriptions to fields expected by `lscpu`.
* **Hardware Abstraction:** Extracting metadata necessary for `dmidecode` and Device Tree (DT) generation.
* **Feature Flags:** Identifying ISA extensions required for `/proc/cpuinfo` flags.

## 🛠️ Tech Stack

* **Model:** Gemini 2.5 Flash (Optimized for low-latency technical reasoning)
* **Orchestration:** [DSPy](https://github.com/stanfordnlp/dspy) (Typed Signatures for schema enforcement)
* **Validation:** [Pydantic](https://docs.pydantic.dev/) (Strict architectural data contracts)
* **Resilience:** [Tenacity](https://tenacity.readthedocs.io/) (Exponential backoff for API rate-limiting)

## 🛡️ Hallucination Control

As a student researcher at **DSCE** and a member of **Point Blank**, I built this tool with a "Verification-First" mindset:
1.  **Source Grounding:** Mandatory `source_quote` field requires the LLM to provide verbatim proof for every parameter.
2.  **Chain-of-Thought (CoT):** Forced `rationale` generation ensures linguistic triggers (may, should, optional) are logically parsed before extraction.
3.  **Deterministic Output:** Temperature is set to `0.0` to ensure architectural fidelity over creative variance.

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