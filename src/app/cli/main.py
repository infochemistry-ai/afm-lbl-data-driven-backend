import typer

from app.cli.seed import app as seed_app
from app.cli.ingest import app as ingest_app
from app.cli.cleanup import app as cleanup_app
from app.cli.build import app as build_app

app = typer.Typer(help="AFM LbL backend CLI")
app.add_typer(seed_app, name="seed")
app.add_typer(ingest_app, name="ingest")
app.add_typer(cleanup_app, name="cleanup")
app.add_typer(build_app, name="build")


if __name__ == "__main__":
    app()
