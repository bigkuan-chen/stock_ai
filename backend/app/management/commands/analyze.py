import json
from django.core.management.base import BaseCommand

from app.pipeline import run_analysis
from app.config import DEFAULT_LOOKBACK_DAYS


class Command(BaseCommand):
    help = "Crawl and calculate policy opportunity scores"

    def add_arguments(self, parser):
        parser.add_argument(
            "--lookback-days",
            type=int,
            default=DEFAULT_LOOKBACK_DAYS,
            help="Number of days to look back for policy documents",
        )
        parser.add_argument(
            "--offline",
            action="store_true",
            help="Use bundled samples instead of live crawling",
        )

    def handle(self, *args, **options):
        lookback_days = options["lookback_days"]
        offline = options["offline"]

        self.stdout.write(f"Starting analysis (lookback-days: {lookback_days}, offline: {offline})...")

        result = run_analysis(lookback_days=lookback_days, offline=offline)

        self.stdout.write(
            json.dumps(
                {
                    "status": "ok",
                    "policies": result["policies"],
                    "industries": result["industries"],
                    "companies": result["companies"],
                    "run_at": result["run_at"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
