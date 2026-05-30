import shutil
import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Build vendored native components")

LACUNARITY_DIR = Path("src/app/features/_lacunarity")


@app.command("lacunarity")
def lacunarity() -> None:
    """Build the vendored C++ lacunarity library via CMake."""
    if shutil.which("cmake") is None:
        typer.echo("cmake not found in PATH. Install cmake first.", err=True)
        raise typer.Exit(code=1)
    src = LACUNARITY_DIR
    build = LACUNARITY_DIR / "build"
    if not src.is_dir():
        typer.echo(f"Source directory missing: {src}", err=True)
        raise typer.Exit(code=1)
    subprocess.run(["cmake", "-S", str(src), "-B", str(build)], check=True)
    subprocess.run(["cmake", "--build", str(build)], check=True)
    typer.echo(f"Built lacunarity library under {build}")
