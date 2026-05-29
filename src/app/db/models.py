from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid_pk() -> Mapped[UUID]:
    return mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Polyelectrolyte(Base):
    __tablename__ = "polyelectrolytes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    charge_sign: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    charge_group: Mapped[str] = mapped_column(String(64), nullable=False)
    is_strong: Mapped[bool] = mapped_column(Boolean, nullable=False)
    pka: Mapped[float | None] = mapped_column(nullable=True)
    monomer_mw_g_mol: Mapped[float] = mapped_column(nullable=False)
    monomer_smiles: Mapped[str] = mapped_column(Text, nullable=False)
    backbone_type: Mapped[str] = mapped_column(String(32), nullable=False)


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _created_at()

    samples: Mapped[list["Sample"]] = relationship(back_populates="experiment", cascade="all, delete-orphan")


class Sample(Base):
    __tablename__ = "samples"
    __table_args__ = (UniqueConstraint("experiment_id", "name", name="uq_sample_experiment_name"),)

    id: Mapped[UUID] = _uuid_pk()
    experiment_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    substrate: Mapped[str] = mapped_column(String(64), nullable=False, default="Si")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _created_at()

    experiment: Mapped[Experiment] = relationship(back_populates="samples")
    layers: Mapped[list["Layer"]] = relationship(back_populates="sample", cascade="all, delete-orphan", order_by="Layer.position")
    scans: Mapped[list["Scan"]] = relationship(back_populates="sample", cascade="all, delete-orphan")


class Layer(Base):
    __tablename__ = "layers"
    __table_args__ = (UniqueConstraint("sample_id", "position", name="uq_layer_sample_position"),)

    id: Mapped[UUID] = _uuid_pk()
    sample_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    polyelectrolyte_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("polyelectrolytes.id"), nullable=False
    )
    molecular_weight_kda: Mapped[float | None] = mapped_column(nullable=True)
    concentration_mg_ml: Mapped[float | None] = mapped_column(nullable=True)
    ph: Mapped[float | None] = mapped_column(nullable=True)
    salt_concentration_m: Mapped[float | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped[Sample] = relationship(back_populates="layers")
    polyelectrolyte: Mapped[Polyelectrolyte] = relationship()


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[UUID] = _uuid_pk()
    sample_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    parser_name: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    width_um: Mapped[float | None] = mapped_column(nullable=True)
    height_um: Mapped[float | None] = mapped_column(nullable=True)
    pixels_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pixels_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    units: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    error_message: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    uploaded_at: Mapped[datetime] = _created_at()
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sample: Mapped[Sample] = relationship(back_populates="scans")


class Feature(Base):
    __tablename__ = "features"
    __table_args__ = (
        CheckConstraint(
            "(scan_id IS NOT NULL AND sample_id IS NULL AND extractor_scope = 'scan') "
            "OR (scan_id IS NULL AND sample_id IS NOT NULL AND extractor_scope = 'sample')",
            name="ck_feature_scan_xor_sample",
        ),
        Index(
            "uq_feature_scan_extractor",
            "scan_id", "extractor_name", "extractor_version", "params_hash",
            unique=True,
            postgresql_where="scan_id IS NOT NULL",
        ),
        Index(
            "uq_feature_sample_extractor",
            "sample_id", "extractor_name", "extractor_version", "params_hash",
            unique=True,
            postgresql_where="sample_id IS NOT NULL",
        ),
        Index("ix_feature_values_gin", "values", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scan_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=True
    )
    sample_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=True
    )
    extractor_name: Mapped[str] = mapped_column(String(64), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    extractor_scope: Mapped[str] = mapped_column(String(16), nullable=False)
    params_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    computed_at: Mapped[datetime] = _created_at()


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[UUID] = _uuid_pk()
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    filter: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    storage_backend: Mapped[str | None] = mapped_column(String(16), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = _created_at()
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
