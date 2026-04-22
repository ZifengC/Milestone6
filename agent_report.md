# Part 2 Agent Report

## Agent Design

The agent is a lightweight multi-tool controller implemented in `./agent_controller.py`. It uses the Part 1 RAG retriever as one tool and adds LLM-based summarization, extraction, reasoning, and final answer synthesis tools. The final evaluated runs should use the local open-weight `qwen2.5:7b` instruct model served through Ollama.

The controller records every decision as a trace entry. Each trace includes the selected tool, the reason for choosing it, the tool input, the tool output, retrieved sources, and latency.

## Tool Selection Policy

The agent uses a simple transparent policy:

1. Always run the retriever first, because every task must be grounded in the document collection.
2. Use the extractor when the task asks to list, extract, identify components, signals, or settings.
3. Use the reasoning tool when the task asks why, how, compare, explain, or relationship questions.
4. Use the summarizer when the task asks for a concise synthesis or checklist.
5. Use the final answer tool after the intermediate tool so the agent produces a complete response with evidence.

This is intentionally rule-based so that the decision logic is observable and easy to audit. The LLM is still integrated into the tool outputs and final answer generation.

## Retrieval Integration

Retrieval coordinates the rest of the agent workflow. The retriever returns top-k chunks from the FAISS index with source filenames, chunk IDs, ranks, and similarity scores. The summarizer, extractor, reasoning tool, and final answer tool receive the retrieved context and are instructed to use only that context.

This design keeps the agent grounded. The non-retrieval tools do not operate from the model's general memory alone; they operate on retrieved evidence.

## Evaluation Tasks

The agent evaluation contains 10 multi-step tasks:

1. Summarize the two-stage RAG pipeline.
2. Explain grounding and hallucination reduction.
3. Extract chunk size and overlap settings.
4. Compare short-term and long-term LLM memory.
5. Extract LLM agent controller components.
6. Explain the relationship between Ollama and Qwen.
7. List recommender personalization signals.
8. Explain personalization bias and mitigation.
9. Compare FAISS and Chroma for a small RAG project.
10. Create a concise local RAG implementation checklist.

The final evaluated run writes all 10 JSON traces into `./agent_traces/all_traces.json` and a compact table to `./agent_traces/trace_summary.md`. The code also supports `--plan-only` for structure inspection without importing RAG dependencies or calling Qwen, but those placeholder traces should not be treated as final evaluated outputs.

## Performance Analysis

The agent generally performs well when the requested information appears directly in one of the retrieved documents. Extraction tasks are the most reliable because the retrieved context contains explicit lists, settings, or named components. Reasoning tasks are also usually successful when the relevant source is retrieved in the top-k context.

The main performance cost is LLM generation. Each task uses at least two LLM calls after retrieval: one intermediate tool call and one final answer call. This makes the agent slower than the Part 1 RAG pipeline, which uses one generation call per query.

Across the 10 evaluated traces, the average agent task latency was 14649.54 ms. The fastest task was task_03 at 4500.66 ms, and the slowest task was task_09 at 25829.36 ms. The slower tasks require longer reasoning or comparison outputs, so they spend more time in local Qwen generation.

## Failure Analysis

The likely failure mode is retrieval noise. Because the document collection is small and `top_k=5`, the retriever often returns several partially related documents. This can make the final prompt longer and may encourage the model to blend concepts from multiple sources.

A second failure mode is over-expansion by the LLM. Even with grounded instructions, the model may phrase an answer more broadly than the source text. The traces make this easier to detect because each final answer can be compared against the retrieved chunks and intermediate tool output.

## Model Analysis

`qwen2.5:7b` is expected to be strong enough for summarization, extraction, and grounded reasoning over short retrieved contexts. In Part 1, it followed source-grounding instructions reasonably well and produced clear final answers. The trade-off is latency and memory use. The 7B model is slower than a hosted API or a smaller local model, and it can stress limited hardware during repeated 10-task evaluations.

The evaluated serving stack used Ollama's local HTTP API with `qwen2.5:7b`. The runtime environment reported Linux `6.1.0-44-cloud-amd64` with NVIDIA GPU support available to Ollama.

For debugging, a smaller model could be used, but final evaluated runs should use the required 7B-14B open-weight instruct model.

## Running Notes

Use `--dry-run` only to verify trace structure without calling Qwen:

```bash
python agent_controller.py --dry-run
```

Use `--plan-only` if the environment does not have FAISS, sentence-transformers, Ollama, or Qwen available:

```bash
python agent_controller.py --plan-only
```

For final evaluated traces, run without `--dry-run` after Ollama and `qwen2.5:7b` are available:

```bash
python agent_controller.py --model qwen2.5:7b --top-k 5
```
