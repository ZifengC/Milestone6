# Part 1 RAG Evaluation Report

## System Summary

This RAG system uses 10 Markdown documents as its knowledge base. The pipeline chunks documents, embeds chunks with `sentence-transformers/all-MiniLM-L6-v2`, stores normalized vectors in a FAISS `IndexFlatIP` index, retrieves the top 5 chunks for each query, and sends a grounded prompt to the local `qwen2.5:7b` model served through Ollama.

The evaluation was run on 10 test questions covering RAG, chunking, embeddings, vector stores, grounding, local LLM serving, LLM memory, LLM agents, recommender systems, and personalization bias.

## Configuration

| Component | Setting |
|---|---|
| Local LLM | `qwen2.5:7b` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector database | FAISS `IndexFlatIP` |
| Chunk size | 320 approximate tokens |
| Chunk overlap | 60 approximate tokens |
| Retrieval `top_k` | 5 |
| Documents | 10 Markdown files |
| Generated chunks | 10 |
| Serving stack | Ollama local HTTP API |
| Runtime environment | Linux `6.1.0-44-cloud-amd64` with NVIDIA GPU available |

## Retrieval Results

| Metric | Result |
|---|---:|
| Average precision@5 | 0.22 |
| Average recall@5 | 1.00 |

The retrieval system found all expected source documents across the 10 test questions, giving recall@5 of 1.00. Precision@5 is low because each query retrieves 5 chunks from a very small 10-chunk collection. In most cases, only one or two retrieved chunks are labeled relevant, so even correct retrieval produces precision around 0.20 to 0.40.

This is acceptable for the draft dataset because the goal is to verify that the relevant evidence is available to the model. For a larger final dataset, precision should become more meaningful because the retriever will rank among more chunks.

## Latency Results

| Stage | Average Latency |
|---|---:|
| Document loading | 0.60 ms |
| Chunking | 0.34 ms |
| Embedding | 257.13 ms |
| Indexing | 0.12 ms |
| Retrieval | 15.26 ms |
| Generation | 2898.63 ms |
| Total query | 2914.23 ms |

Retrieval is fast, averaging about 15 ms per query. Generation is the dominant cost, averaging about 2.9 seconds per query. This is expected because Qwen2.5-7B is running locally and generation is much more expensive than vector search for a small dataset.

## Per-Question Analysis

| ID | Retrieval Result | Generation Result | Failure Type | Notes |
|---|---|---|---|---|
| q1 | Relevant source retrieved at rank 1 | Grounded | No failure | Correctly identifies indexing and query stages from `rag_overview.md`. |
| q2 | Relevant sources retrieved at ranks 1 and 2 | Grounded | No failure | Correctly explains hallucination reduction using retrieved RAG and grounding context. |
| q3 | Relevant source retrieved at rank 1 | Grounded | No failure | Correctly reports 256-512 tokens and 40-80 token overlap from `chunking.md`. |
| q4 | Relevant source retrieved at rank 1 | Grounded | No failure | Correctly explains Ollama as the local runtime/API and Qwen as the model. |
| q5 | Relevant source retrieved at rank 1 | Grounded | No failure | Correctly defines embeddings as dense vectors for semantic similarity. |
| q6 | Relevant source retrieved at rank 1 | Grounded | No failure | Correctly explains short-term/long-term memory and personalization benefits. |
| q7 | Relevant source retrieved at rank 1 | Grounded | No failure | Correctly lists tool registry, routing/planning, execution logic, and trace logging. |
| q8 | Relevant source retrieved at rank 2 | Grounded | Minor retrieval ranking issue | The relevant vector database source was retrieved but not ranked first. The answer is still supported. |
| q9 | Relevant source retrieved at rank 1 | Grounded | No failure | Correctly lists recommender personalization signals. |
| q10 | Relevant source retrieved at rank 1 | Mostly grounded | Minor generation expansion | Answer is supported overall, but some phrasing expands beyond the exact wording of the context. |

## Hallucination Review

No severe hallucination was observed in this run. The answers generally stay within the retrieved context and cite or mention the correct source documents.

Two minor issues should be noted:

- q8 has a retrieval ranking issue: `vector_databases.md` is retrieved, but it appears after `personalization_bias.md`. The generated answer is still grounded because the relevant chunk is in the top-5 context.
- q10 includes slightly expanded wording when describing mitigation strategies. The core claims are supported by `personalization_bias.md`, but the phrasing is more detailed than the original context.

## Retrieval vs. Generation Errors

The main weakness in this run is retrieval precision, not generation quality. Recall is perfect, so the model usually receives the necessary evidence. Low precision comes from the small dataset and `top_k=5`, which retrieves half of the full chunk collection for every query.

Generation quality is mostly acceptable. The model follows the grounded prompt and usually answers from the relevant context. The most important residual risk is that the model may expand phrasing beyond the exact retrieved wording, as seen mildly in q10.

## Design Decisions

The chunk size of 320 approximate tokens was chosen because the assignment suggests 256-512 tokens. This keeps chunks focused while leaving enough surrounding context for answer generation.

The overlap of 60 approximate tokens was chosen to reduce boundary loss. Since the documents are short, each document currently produces one chunk, but the same setting will still work if longer documents are added.

The embedding model `all-MiniLM-L6-v2` was chosen because it is fast, lightweight, and suitable for small RAG prototypes. It produces 384-dimensional embeddings, which keeps indexing and retrieval inexpensive.

FAISS `IndexFlatIP` was chosen because the dataset is small and exact search is simple to explain. Embeddings are normalized, so inner product ranking behaves like cosine similarity.

The default `top_k=5` was chosen to maximize recall for the first working version. The results show that this succeeds for recall but lowers precision. A future version could compare `top_k=3` against `top_k=5` to reduce irrelevant context.

## Conclusion

Part 1 is functionally complete. The system implements the full chain from documents to chunks, embeddings, FAISS retrieval, grounded prompt construction, local Qwen generation, retrieval metrics, groundedness review, and latency measurement. The current results show strong recall, acceptable grounded generation, and low retrieval precision caused mainly by the small dataset and high `top_k` setting.
