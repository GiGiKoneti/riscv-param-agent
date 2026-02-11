# Architecture Documentation

## System Overview

The RISC-V Parameter Extractor is a production-grade agentic pipeline that transforms natural language RISC-V specifications into machine-readable YAML parameters. The system leverages LLMs with multi-model consensus, hallucination detection, and comprehensive validation.

## Architecture Diagram

```mermaid
graph TD
    A[RISC-V Spec Files] -->|Markdown/AsciiDoc| B[Spec Parser]
    B -->|Extract Chapters| C[Text Chunker]
    C -->|3000 tokens/chunk| D{Multi-Model?}
    
    E[UDB Examples] -->|Few-shot| F[Gemini 2.5 Flash]
    E -->|Few-shot| G[Llama 3.1]
    
    D -->|Yes| F
    D -->|Yes| G
    D -->|No| F
    
    F -->|Extraction| H[RLM Verifier]
    G -->|Extraction| H
    
    H -->|Self-correction| I[Consensus Generator]
    I -->|Confidence Scores| J{Validation Enabled?}
    
    J -->|Yes| K[Hallucination Detector]
    K -->|Verify Quotes| L{Tag Generation?}
    J -->|No| L
    
    L -->|Yes| M[GraphRAG Tag Generator]
    L -->|No| N[Output YAML]
    M -->|Context-aware Tags| N
    
    N -->|Structured Data| O[YAML/JSON Output]
    
    style F fill:#e1f5ff
    style G fill:#ffe1f5
    style H fill:#fff4e1
    style K fill:#e1ffe1
    style M fill:#f5e1ff
```

## Component Architecture

### 1. Parsing Layer

**Components:**
- `RISCVSpecParser`: Markdown/AsciiDoc parsing
- `TextChunker`: Intelligent chunking with overlap

**Responsibilities:**
- Extract chapters from spec files
- Chunk text for LLM processing
- Preserve context across chunks

**Key Features:**
- Format detection (Markdown/AsciiDoc)
- Chapter extraction with metadata
- Token-aware chunking

---

### 2. Extraction Layer

**Components:**
- `RISCVArchitecturalMiner`: DSPy signature for extraction
- `ModelComparator`: Multi-model consensus
- `RLMVerifier`: Recursive self-correction

**Responsibilities:**
- Extract parameters from text
- Compare multiple model outputs
- Generate confidence scores

**Key Features:**
- Few-shot prompting with UDB examples
- Multi-model consensus (Gemini + Llama)
- Confidence scoring (HIGH/MEDIUM/LOW)

---

### 3. Validation Layer

**Components:**
- `HallucinationDetector`: Source quote verification
- `TagGenerator`: GraphRAG-based naming
- `UDBValidator`: Schema validation (future)

**Responsibilities:**
- Verify extracted parameters
- Generate unique tags
- Validate against UDB schema

**Key Features:**
- Exact and fuzzy quote matching
- Suspicious pattern detection
- Context-aware tag generation

---

### 4. Configuration Layer

**Components:**
- `Config`: Pydantic-based settings
- `Logger`: Rich-formatted logging
- `Environment`: API key management

**Responsibilities:**
- Centralized configuration
- Structured logging
- Secret management

**Key Features:**
- YAML configuration
- Type-safe settings
- Environment variable support

---

## Data Flow

### Single-Model Extraction

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Parser
    participant Extractor
    participant Validator
    participant Output
    
    User->>CLI: Run extraction
    CLI->>Parser: Parse spec file
    Parser->>Parser: Extract chapter
    Parser->>Parser: Chunk text
    Parser-->>CLI: Text chunks
    
    loop For each chunk
        CLI->>Extractor: Extract parameters
        Extractor->>Extractor: Few-shot prompting
        Extractor->>Extractor: LLM inference
        Extractor-->>CLI: Parameters
    end
    
    CLI->>Validator: Validate parameters
    Validator->>Validator: Verify quotes
    Validator->>Validator: Generate tags
    Validator-->>CLI: Validated parameters
    
    CLI->>Output: Save YAML
    Output-->>User: Results
```

### Multi-Model Extraction

```mermaid
sequenceDiagram
    participant CLI
    participant Gemini
    participant Llama
    participant Comparator
    participant Output
    
    CLI->>Gemini: Extract (chunk)
    CLI->>Llama: Extract (chunk)
    
    Gemini-->>Comparator: Result A
    Llama-->>Comparator: Result B
    
    Comparator->>Comparator: Calculate confidence
    Comparator->>Comparator: Generate consensus
    Comparator->>Comparator: Create report
    
    Comparator-->>Output: Consensus + Report
```

---

## Module Structure

```
src/
├── agents/
│   └── signatures.py          # DSPy signatures
├── comparators/
│   └── model_comparator.py    # Multi-model comparison
├── config/
│   └── settings.py            # Configuration management
├── generators/
│   └── tag_generator.py       # GraphRAG tag generation
├── loaders/
│   └── udb_loader.py          # UDB examples loading
├── models/
│   └── schema.py              # Pydantic models
├── parsers/
│   └── spec_parser.py         # Spec file parsing
├── utils/
│   └── logger.py              # Logging system
├── validators/
│   └── hallucination_detector.py  # Quote verification
└── main.py                    # CLI entry point
```

---

## Configuration

### YAML Configuration (`config.yaml`)

```yaml
models:
  primary: "gemini/gemini-2.5-flash"
  temperature: 0.0
  max_tokens: 4000

extraction:
  chunk_size: 3000
  overlap: 200
  num_examples: 12

validation:
  similarity_threshold: 0.85
  enable_hallucination_detection: false

logging:
  level: "INFO"
  format: "rich"
```

### Environment Variables

```bash
GEMINI_API_KEY=your_api_key_here
```

---

## Deployment

### Docker

```bash
# Build image
docker build -t riscv-param-extractor .

# Run extraction
docker run -v $(pwd)/specs:/app/specs \
           -v $(pwd)/outputs:/app/outputs \
           -e GEMINI_API_KEY=$GEMINI_API_KEY \
           riscv-param-extractor \
           python -m src.main --spec-path /app/specs/riscv-privileged.md --chapter 3
```

### Docker Compose

```bash
# Start services
docker-compose up

# With Ollama for multi-model
docker-compose up extractor ollama
```

---

## Performance Characteristics

### Benchmarks

- **Parsing**: 14.2K ops/sec (70.4 μs/op)
- **Chunking**: 2.2M ops/sec (0.45 μs/op)

### Scalability

- **Chunk Processing**: Parallel-ready (currently sequential)
- **Multi-Model**: Concurrent API calls
- **Memory**: O(n) where n = spec file size

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \      Integration Tests (10)
      /____\
     /      \    Unit Tests (71)
    /________\
```

### Coverage

- **Overall**: 68%
- **Critical Modules**: 93-100%
- **Integration**: End-to-end pipeline

---

## Future Enhancements

1. **Parallel Processing**: Process chunks concurrently
2. **Caching**: Cache LLM responses
3. **Streaming**: Stream results for large specs
4. **Web UI**: Browser-based interface
5. **API Server**: REST API for integration

---

## References

- [DSPy Documentation](https://github.com/stanfordnlp/dspy)
- [RISC-V Specifications](https://riscv.org/technical/specifications/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
