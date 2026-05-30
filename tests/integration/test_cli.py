from typer.testing import CliRunner

from app.cli import app


def test_seed_polyelectrolytes(db_session):
    runner = CliRunner()
    r = runner.invoke(app, ["seed", "polyelectrolytes"])
    assert r.exit_code == 0, r.output
    assert "Seeded" in r.stdout
