import re
from pathlib import Path

import typer
from sqlalchemy import select

from app.db.models import Experiment, Layer, Sample
from app.db.session import get_session_factory
from app.services.ingestion import ingest_scan
from app.workers.tasks import extract_features_task

app = typer.Typer(help="Bulk ingest tools")


LAYER_PRESETS = {
    "no_layers": [],
    "1_layer":   ["PEI"],
    "2_layers":  ["PEI", "PSS"],
    "3_layers":  ["PEI", "PSS", "PEI"],
    "4_layers":  ["PEI", "PSS", "PEI", "PSS"],
}


@app.command("raw-data")
def raw_data(
    root: Path = typer.Argument(..., exists=True, file_okay=False),
    experiment_name: str = typer.Option("baseline", "--experiment-name"),
    enqueue: bool = typer.Option(True, help="Enqueue feature extraction task per scan"),
) -> None:
    """
    Walks the layered subfolders of `root` (no_layers, 1_layer, ..., 4_layers),
    treats each filename prefix (e.g. 'PE11') as a Sample, and uploads the three
    scan files as separate Scans linked to it.
    """
    Session = get_session_factory()
    with Session() as session:
        exp = session.scalar(select(Experiment).where(Experiment.name == experiment_name))
        if exp is None:
            exp = Experiment(name=experiment_name, description=f"Bulk import from {root}")
            session.add(exp); session.flush()

        for subdir, layer_ids in LAYER_PRESETS.items():
            folder = root / subdir
            if not folder.is_dir():
                continue
            by_prefix: dict[str, list[Path]] = {}
            for f in folder.iterdir():
                if not f.is_file():
                    continue
                # Filename patterns: "PE11_1.txt" or "PE15aist1.txt". The sample
                # identifier is the "PE<digits>" prefix; anything after is a scan
                # index (with optional operator marker like "aist").
                m = re.match(r"^(PE\d+)", f.stem)
                if not m:
                    continue
                prefix = m.group(1)
                by_prefix.setdefault(prefix, []).append(f)
            for prefix, files in by_prefix.items():
                sample = session.scalar(select(Sample).where(Sample.experiment_id == exp.id, Sample.name == prefix))
                if sample is None:
                    sample = Sample(experiment_id=exp.id, name=prefix, substrate="Si",
                                    layers=[Layer(position=i + 1, polyelectrolyte_id=pid) for i, pid in enumerate(layer_ids)])
                    session.add(sample); session.flush()
                for fp in files:
                    with fp.open("rb") as fh:
                        scan = ingest_scan(session, sample_id=sample.id, filename=fp.name, file=fh)
                    session.commit()
                    if enqueue:
                        extract_features_task.delay(str(scan.id))
                    typer.echo(f"Ingested {fp.name} → scan {scan.id}")
        session.commit()
