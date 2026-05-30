import typer

from app.cli.seed import app as seed_app
from app.cli.ingest import app as ingest_app
from app.cli.cleanup import app as cleanup_app

app = typer.Typer(help="AFM LbL backend CLI")
app.add_typer(seed_app, name="seed")
app.add_typer(ingest_app, name="ingest")
app.add_typer(cleanup_app, name="cleanup")


if __name__ == "__main__":
    app()
