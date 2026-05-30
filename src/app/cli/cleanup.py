import typer
from sqlalchemy import select

from app.db.models import Export, Scan
from app.db.session import get_session_factory
from app.storage import get_storage

app = typer.Typer(help="Storage maintenance")


@app.command("orphans")
def orphans(delete: bool = typer.Option(False, "--delete", help="Actually delete orphaned files")) -> None:
    """Find files in storage that have no matching DB row."""
    Session = get_session_factory()
    storage = get_storage()
    with Session() as session:
        scan_keys = {s.storage_key for s in session.scalars(select(Scan))}
        export_keys = {e.storage_key for e in session.scalars(select(Export)) if e.storage_key}

    from app.storage.local import LocalStorage
    if not isinstance(storage, LocalStorage):
        typer.echo("cleanup orphans currently scans only local storage")
        raise typer.Exit(code=1)

    root = storage.root
    orphan_count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if rel.endswith(".manifest.json"):
            continue
        if rel not in scan_keys and rel not in export_keys:
            orphan_count += 1
            typer.echo(f"orphan: {rel}")
            if delete:
                path.unlink()
    typer.echo(f"Found {orphan_count} orphans")
