# RAG Pipeline Diagram

## Architecture

```mermaid
flowchart TD
    A[Markdown documents in ./data/documents] --> B[Chunk documents]
    B --> C[Generate chunk embeddings with all-MiniLM-L6-v2]
    C --> D[Store vectors in FAISS IndexFlatIP]
    D --> E[Vector store files in ./data/vector_store]

    F[User question] --> G[Generate query embedding]
    G --> H[FAISS top-k similarity search]
    E --> H
    H --> I[Retrieved context chunks with source metadata]
    I --> J[Build grounded prompt]
    F --> J
    J --> K[Ollama local API]
    K --> L[Qwen2.5-7B-Instruct]
    L --> M[Grounded answer]

    H --> N[Retrieval metrics: precision@k and recall@k]
    M --> O[Groundedness review]
    G --> P[Latency tracking]
    H --> P
    K --> P
```

## Data Flow

1. Documents are stored as Markdown files in `./data/documents`.
2. `rag_pipeline.py prepare` loads the documents, chunks them, generates embeddings, and writes the FAISS index to `./data/vector_store`.
3. At query time, the user question is embedded with the same embedding model.
4. FAISS retrieves the top-k most similar chunks.
5. Retrieved chunks are formatted into a grounded prompt with source labels.
6. The prompt is sent to the local Ollama API using `qwen2.5:7b`.
7. The generated answer and retrieval outputs are evaluated with precision@k, recall@k, groundedness review, and latency measurements.

## Key Files

| File or Folder | Purpose |
|---|---|
| `./data/documents/` | Input Markdown documents |
| `./data/vector_store/` | Saved FAISS index, chunk metadata, and manifest |
| `./rag_pipeline.py` | RAG implementation |
| `./evaluate.py` | 10-question evaluation script |
| `./data/results/` | Evaluation outputs |
