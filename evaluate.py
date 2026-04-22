from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rag_pipeline import DEFAULT_DOCUMENTS_DIR, DEFAULT_MODEL, DEFAULT_DATA_ROOT, RAGPipeline


TEST_SET = [
    {
        "id": "q1",
        "query": "What are the two stages of a RAG pipeline?",
        "relevant_sources": ["rag_overview.md"],
    },
    {
        "id": "q2",
        "query": "Why does RAG reduce hallucination?",
        "relevant_sources": ["rag_overview.md", "grounding.md"],
    },
    {
        "id": "q3",
        "query": "What chunk size is a reasonable starting point for this project?",
        "relevant_sources": ["chunking.md"],
    },
    {
        "id": "q4",
        "query": "What is the relationship between Ollama and Qwen in this project?",
        "relevant_sources": ["local_llm.md"],
    },
    {
        "id": "q5",
        "query": "What does an embedding model do?",
        "relevant_sources": ["embeddings.md"],
    },
    {
        "id": "q6",
        "query": "What is LLM memory and why can it improve personalization?",
        "relevant_sources": ["llm_memory.md"],
    },
    {
        "id": "q7",
        "query": "What components does a basic LLM agent controller include?",
        "relevant_sources": ["llm_agents.md"],
    },
    {
        "id": "q8",
        "query": "What is the trade-off when choosing top-k?",
        "relevant_sources": ["vector_databases.md"],
    },
    {
        "id": "q9",
        "query": "What signals can recommender systems use for personalization?",
        "relevant_sources": ["recommender_systems.md"],
    },
    {
        "id": "q10",
        "query": "What is personalization bias and how can it be mitigated?",
        "relevant_sources": ["personalization_bias.md"],
    },
]


def precision_at_k(retrieved_sources: list[str], relevant_sources: list[str], k: int) -> float:
    retrieved_k = retrieved_sources[:k]
    if not retrieved_k:
        return 0.0
    relevant = set(relevant_sources)
    hits = sum(1 for source in retrieved_k if source in relevant)
    return hits / len(retrieved_k)


def recall_at_k(retrieved_sources: list[str], relevant_sources: list[str], k: int) -> float:
    relevant = set(relevant_sources)
    if not relevant:
        return 0.0
    retrieved_k = set(retrieved_sources[:k])
    return len(retrieved_k.intersection(relevant)) / len(relevant)


def simple_groundedness(answer: str, retrieved_texts: list[str]) -> dict[str, Any]:
    if not answer:
        return {"score": None, "note": "Generation skipped; score manually after running Ollama."}

    context_words = set(" ".join(retrieved_texts).lower().split())
    answer_words = [word.strip(".,:;!?()[]").lower() for word in answer.split()]
    content_words = [word for word in answer_words if len(word) > 4]
    if not content_words:
        return {"score": 0.0, "note": "Answer has too few content words."}

    supported = [word for word in content_words if word in context_words]
    score = len(supported) / len(content_words)
    return {
        "score": round(score, 3),
        "note": "Automatic lexical proxy only; final groundedness should be checked manually.",
    }


def run_evaluation(
    data_dir: Path,
    output_dir: Path,
    top_k: int,
    model: str,
    skip_generation: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = RAGPipeline(data_dir=data_dir)
    chunk_count = pipeline.ingest()

    results = []
    for item in TEST_SET:
        result = pipeline.answer(
            item["query"],
            top_k=top_k,
            ollama_model=model,
            skip_generation=skip_generation,
        )
        retrieved_sources = [chunk["source"] for chunk in result["retrieved_chunks"]]
        retrieved_texts = [chunk["text"] for chunk in result["retrieved_chunks"]]

        row = {
            "id": item["id"],
            "query": item["query"],
            "relevant_sources": item["relevant_sources"],
            "retrieved_sources": retrieved_sources,
            "precision_at_k": round(precision_at_k(retrieved_sources, item["relevant_sources"], top_k), 3),
            "recall_at_k": round(recall_at_k(retrieved_sources, item["relevant_sources"], top_k), 3),
            "answer": result["answer"],
            "groundedness_proxy": simple_groundedness(result["answer"], retrieved_texts),
        }
        results.append(row)

    avg_precision = sum(row["precision_at_k"] for row in results) / len(results)
    avg_recall = sum(row["recall_at_k"] for row in results) / len(results)

    report = {
        "config": {
            "llm": model,
            "embedding_model": pipeline.embedding_model_name,
            "vector_database": "FAISS IndexFlatIP with normalized embeddings",
            "chunk_tokens": pipeline.chunk_tokens,
            "overlap_tokens": pipeline.overlap_tokens,
            "top_k": top_k,
            "chunk_count": chunk_count,
            "generation_skipped": skip_generation,
        },
        "summary": {
            "average_precision_at_k": round(avg_precision, 3),
            "average_recall_at_k": round(avg_recall, 3),
            "timings": pipeline.timing_summary(),
        },
        "results": results,
    }

    (output_dir / "evaluation_results.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    write_markdown_report(report, output_dir / "evaluation_summary.md")
    return report


def write_markdown_report(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Evaluation Summary",
        "",
        "## Configuration",
        "",
    ]
    for key, value in report["config"].items():
        lines.append(f"- **{key}**: {value}")

    lines.extend(
        [
            "",
            "## Retrieval Metrics",
            "",
            f"- **Average precision@k**: {report['summary']['average_precision_at_k']}",
            f"- **Average recall@k**: {report['summary']['average_recall_at_k']}",
            "",
            "## Latency",
            "",
        ]
    )
    for stage, timing in report["summary"]["timings"].items():
        lines.append(
            f"- **{stage}**: avg {timing['avg_ms']} ms, total {timing['total_ms']} ms, count {timing['count']}"
        )

    lines.extend(["", "## Per-Question Results", ""])
    for row in report["results"]:
        lines.extend(
            [
                f"### {row['id']}: {row['query']}",
                "",
                f"- Relevant sources: {', '.join(row['relevant_sources'])}",
                f"- Retrieved sources: {', '.join(row['retrieved_sources'])}",
                f"- Precision@k: {row['precision_at_k']}",
                f"- Recall@k: {row['recall_at_k']}",
                f"- Groundedness proxy: {row['groundedness_proxy']}",
                "",
                "Answer:",
                "",
                row["answer"] or "_Generation skipped._",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the local RAG pipeline.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DOCUMENTS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DATA_ROOT / "results")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--skip-generation", action="store_true")
    args = parser.parse_args()

    report = run_evaluation(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        top_k=args.top_k,
        model=args.model,
        skip_generation=args.skip_generation,
    )
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
