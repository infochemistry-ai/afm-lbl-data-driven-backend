from app.db.models import (
    Experiment,
    Export,
    Feature,
    Layer,
    Polyelectrolyte,
    Sample,
    Scan,
)


def test_all_models_have_tablenames():
    for cls in [Experiment, Sample, Layer, Scan, Feature, Export, Polyelectrolyte]:
        assert cls.__tablename__


def test_feature_check_constraint_exists():
    constraints = [c.name for c in Feature.__table__.constraints if c.name]
    assert "ck_feature_scan_xor_sample" in constraints
