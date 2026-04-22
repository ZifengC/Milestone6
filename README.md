# IDS568 Milestone 6

This folder contains the final Milestone 6 implementation for:

- Part 1: local RAG pipeline
- Part 2: multi-tool agent with retrieval integration

The evaluated local model is `qwen2.5:7b`, served through Ollama.

## File Structure

```text
script/
├── rag_pipeline.py              # Part 1 RAG implementation
├── evaluate.py                  # Part 1 evaluation runner
├── agent_controller.py          # Part 2 multi-tool agent
├── rag_evaluation_report.md     # Part 1 evaluation report
├── rag_pipeline_diagram.md      # RAG architecture diagram
├── agent_report.md              # Part 2 analysis report
├── agent_traces/                # Part 2 trace outputs
│   ├── all_traces.json
│   ├── trace_summary.md
│   └── README.md
├── requirements.txt             # Pinned dependencies
├── README.md                    # Setup and usage
├── agent_tasks.json             # 10 Part 2 evaluation tasks
└── data/
    ├── documents/               # 10 Markdown source documents
    └── results/                 # Part 1 evaluation outputs
        ├── evaluation_results.json
        └── evaluation_summary.md
```

## Setup

Create a Python environment and install dependencies:

```bash
cd script
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install and start Ollama:

```bash
brew install ollama
ollama serve
```

In a second terminal, pull the local 7B model and confirm the API is running:

```bash
ollama pull qwen2.5:7b
curl http://localhost:11434/api/tags
```

## Model Deployment Evidence

| Item | Value |
|---|---|
| Exact model | `qwen2.5:7b` |
| Size class | 7B open-weight instruct model |
| Serving stack | Ollama local HTTP API |
| API endpoint | `http://localhost:11434/api/generate` |
| Python model-serving client | `requests==2.31.0` calling the Ollama REST API |
| Runtime used for evaluated outputs | Linux `6.1.0-44-cloud-amd64` with NVIDIA GPU available through Ollama |
| Typical Part 1 generation latency | 2898.63 ms average |
| Typical Part 1 end-to-end query latency | 2914.23 ms average |
| Typical Part 2 task latency | 14649.54 ms average across 10 multi-tool tasks |

## Part 1: RAG Pipeline

The RAG pipeline performs:

```text
Markdown documents -> chunking -> embeddings -> FAISS retrieval -> grounded prompt -> Qwen answer
```

Prepare the vector store:

```bash
cd script
python rag_pipeline.py prepare
```

Run one query:

```bash
python rag_pipeline.py query --query "What is LLM memory?" --model qwen2.5:7b --top-k 5
```

Run the 10-question evaluation:

```bash
python evaluate.py --top-k 5 --model qwen2.5:7b
```

Current Part 1 results are saved in:

```text
data/results/evaluation_results.json
data/results/evaluation_summary.md
```

Current summary:

```text
Documents: 10 Markdown files
Generated chunks: 10
Average precision@5: 0.22
Average recall@5: 1.00
Average retrieval latency: 15.26 ms
Average generation latency: 2898.63 ms
Average total query latency: 2914.23 ms
```

The written Part 1 deliverables are:

```text
rag_pipeline.py
rag_evaluation_report.md
rag_pipeline_diagram.md
```

## Part 2: Multi-Tool Agent

The agent uses the Part 1 retriever plus task-specific tools:

- `retriever`: retrieves top-k evidence chunks from the RAG document collection
- `summarizer`: summarizes retrieved evidence
- `extractor`: extracts structured facts and lists
- `reasoning`: performs grounded comparison or explanation over retrieved evidence
- `final_answer`: synthesizes the final answer with an evidence trail

Tool-selection policy:

```text
Always retrieve first.
Use extractor for list/extract/component/settings tasks.
Use reasoning for compare/why/how/explain/relationship tasks.
Use summarizer for concise synthesis tasks.
Use final_answer after the intermediate tool.
```

Run the 10 multi-step agent tasks:

```bash
cd script
python agent_controller.py --model qwen2.5:7b --top-k 5
```

Current Part 2 results are saved in:

```text
agent_traces/all_traces.json
agent_traces/trace_summary.md
```

The current traces contain 10 tasks and use `qwen2.5:7b`. Each trace records:

- decision points
- selected tools
- reasons for tool choices
- retrieval results
- intermediate tool outputs
- final answer
- latency

The written Part 2 deliverables are:

```text
agent_controller.py
agent_report.md
agent_traces/
```

## Debugging Without Qwen

To inspect routing structure only without loading RAG dependencies or calling Qwen:

```bash
cd script
python agent_controller.py --plan-only
```

Do not submit `--plan-only` traces as final evaluated traces. They are placeholders only.

## Notes

This project uses Ollama only for local LLM generation. Chunking, embedding, vector search, retrieval evaluation, and agent orchestration are implemented in Python.
