"""Small explicit commands; no automatic assessment or paid calls."""

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

from .catalog import validate_repository
from .market import market_report
from .progress import build_progress


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["verify", "status", "readme", "llm-smoke", "market-export"]:
        commands.add_parser(name)
    serve = commands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "::1"])
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "serve":
            import uvicorn

            from .app import create_app

            uvicorn.run(create_app(root), host=args.host, port=args.port)
            return
        if args.command == "llm-smoke":
            from .provider import ProviderConfig, provider_smoke

            print(
                json.dumps(
                    asyncio.run(provider_smoke(ProviderConfig.from_env())), ensure_ascii=False, indent=2
                )
            )
            return
        if args.command == "verify":
            errors = validate_repository(root)
            if (root / "research/market/batches").exists():
                market_report(root)
            print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
            sys.exit(bool(errors))
        if args.command == "market-export":
            report = market_report(root)
            target = root / "research/market/requirement-matrix.csv"
            fields = [
                "vacancy_id",
                "company",
                "url",
                "checked_on",
                "verification",
                "importance",
                "requirement",
                "mapping",
                "skill_ids",
                "outcome_ids",
                "project_ids",
            ]
            with target.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                for row in report["matrix"]:
                    writer.writerow(
                        {
                            key: ";".join(row[key]) if isinstance(row[key], list) else row[key]
                            for key in fields
                        }
                    )
            print(f"{target}: {len(report['matrix'])} requirements")
            return
        progress = build_progress(root)
        if args.command == "status":
            print(json.dumps(progress, ensure_ascii=False, indent=2))
        elif args.command == "readme":
            path = root / "README.md"
            text = path.read_text()
            start, end = "<!-- PROGRESS_START -->", "<!-- PROGRESS_END -->"
            if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
                raise ValueError("README must contain one ordered progress marker pair")
            lines = [
                f"\n\nОсвоено **{progress['mastered_outcomes']}/{progress['total_outcomes']}** результатов ({progress['percent']}%).",
                f"Попыток: {progress['attempt_count']}. Подтверждённых demo: {progress['ready_projects']}/6.\n",
            ]
            for module in progress["modules"]:
                done = round(module["percent"] / 10)
                lines.append(
                    f"- {module['id']} {module['title']}: `{'█' * done}{'░' * (10 - done)}` {module['mastered']}/{module['total']}"
                )
            block = "\n".join(lines) + "\n\n"
            path.write_text(text[: text.index(start) + len(start)] + block + text[text.index(end) :])
            print(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
