import typer

from app.db.session import get_session_factory
from app.services.polyelectrolytes import seed_catalog

app = typer.Typer(help="Seed reference data")


@app.command("polyelectrolytes")
def polyelectrolytes() -> None:
    Session = get_session_factory()
    with Session() as session:
        n = seed_catalog(session)
        typer.echo(f"Seeded {n} polyelectrolytes")
