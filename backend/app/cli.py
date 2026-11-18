import argparse
import asyncio
import json
import sys
from backend.app.db.session import async_session_maker
from backend.app.services.admin_service import admin_service
from backend.app.synthetic.generator import SyntheticConfig


async def run_seed(args):
    config = SyntheticConfig(
        seed=args.seed,
        num_students=args.students,
        num_faculty=args.faculty,
        num_publications=args.publications,
        num_relevance_judgments=args.judgments,
    )
    print(f"[*] Starting synthetic data generation with seed={config.seed}...")
    print(f"[*] Targets: {config.num_students} students, {config.num_faculty} faculty, {config.num_publications} publications, {config.num_relevance_judgments} judgments.")

    async with async_session_maker() as db:
        result = await admin_service.seed_synthetic_dataset(
            db, config=config, reset_existing=args.reset
        )
        print("\n[+] Synthetic Seeding Complete!")
        print(f"    Job ID:            {result['job_id']}")
        print(f"    Status:            {result['status']}")
        print(f"    Records Processed: {result['records_processed']}")
        print(f"    Records Created:   {result['records_created']}")
        print(f"    Records Updated:   {result['records_updated']}")
        if result.get("reset_summary"):
            print(f"    Reset Summary:     {result['reset_summary']}")


async def run_reset(args):
    print("[*] Safely purging all synthetic records from database...")
    async with async_session_maker() as db:
        res = await admin_service.reset_synthetic_data(db)
        print(f"[+] Purge complete: {res['deleted']}")


async def run_counts(args):
    async with async_session_maker() as db:
        counts = await admin_service.get_data_counts(db)
        print(json.dumps(counts, indent=2))


async def run_generate_embeddings(args):
    """Generate vector embeddings for all entities in the database."""
    from backend.app.embeddings.service import EmbeddingService

    print("[*] Initializing embedding service...")
    service = EmbeddingService()
    print(f"    Model:     {service.model_name}")
    print(f"    Dimension: {service.dimension}")
    print(f"    Version:   {service.model_version}")
    encoder_type = "SentenceTransformer" if service._st_model else "Deterministic Projection"
    print(f"    Encoder:   {encoder_type}")

    print("\n[*] Generating embeddings for all entities...")
    async with async_session_maker() as db:
        stats = await service.sync_all_embeddings(db)

    print("\n[+] Embedding Generation Complete!")
    print(f"    Students Embedded:     {stats['students_embedded']}")
    print(f"    Projects Embedded:     {stats['projects_embedded']}")
    print(f"    Faculty Embedded:      {stats['faculty_embedded']}")
    print(f"    Publications Embedded: {stats['publications_embedded']}")
    total = sum(stats.values())
    print(f"    Total Embeddings:      {total}")


async def run_evaluation(args):
    """Run offline benchmark evaluation."""
    from backend.app.evaluation.evaluator import benchmark_evaluator

    k_values = [int(k.strip()) for k in args.k_values.split(",") if k.strip().isdigit()]
    if not k_values:
        k_values = [5, 10]

    print(f"[*] Running benchmark evaluation suite: {args.suite}")
    print(f"    K values: {k_values}")

    async with async_session_maker() as db:
        result = await benchmark_evaluator.run_evaluation(
            db, benchmark_suite=args.suite, k_values=k_values
        )

    print("\n[+] Evaluation Results:")
    print(json.dumps(result, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(
        prog="python -m backend.app.cli",
        description="CLI Utility for Researcher-Student Collaboration Platform",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Seed command
    seed_parser = subparsers.add_parser("seed-synthetic", help="Generate and seed synthetic data")
    seed_parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    seed_parser.add_argument("--students", type=int, default=30, help="Number of students (default: 30)")
    seed_parser.add_argument("--faculty", type=int, default=25, help="Number of faculty (default: 25)")
    seed_parser.add_argument("--publications", type=int, default=60, help="Number of publications (default: 60)")
    seed_parser.add_argument("--judgments", type=int, default=40, help="Number of relevance judgments (default: 40)")
    seed_parser.add_argument("--reset", action="store_true", help="Purge existing synthetic data before seeding")

    # Reset command
    subparsers.add_parser("reset-synthetic", help="Safely delete all synthetic records")

    # Data counts command
    subparsers.add_parser("data-counts", help="View entity counts by data mode")

    # Generate embeddings command
    embed_parser = subparsers.add_parser(
        "generate-embeddings",
        help="Generate vector embeddings for all entities",
    )

    # Run evaluation command
    eval_parser = subparsers.add_parser(
        "run-evaluation",
        help="Run offline benchmark evaluation (NDCG, Precision@K, Recall@K, MRR)",
    )
    eval_parser.add_argument(
        "--suite",
        type=str,
        default="standard_eval_v1",
        help="Benchmark suite name (default: standard_eval_v1)",
    )
    eval_parser.add_argument(
        "--k-values",
        type=str,
        default="5,10",
        dest="k_values",
        help="Comma-separated K values for evaluation metrics (default: 5,10)",
    )

    parsed = parser.parse_args()

    if parsed.command == "seed-synthetic":
        asyncio.run(run_seed(parsed))
    elif parsed.command == "reset-synthetic":
        asyncio.run(run_reset(parsed))
    elif parsed.command == "data-counts":
        asyncio.run(run_counts(parsed))
    elif parsed.command == "generate-embeddings":
        asyncio.run(run_generate_embeddings(parsed))
    elif parsed.command == "run-evaluation":
        asyncio.run(run_evaluation(parsed))


if __name__ == "__main__":
    main()

