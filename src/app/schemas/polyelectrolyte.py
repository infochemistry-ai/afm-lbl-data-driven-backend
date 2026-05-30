from pydantic import BaseModel, ConfigDict


class PolyelectrolyteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    charge_sign: int
    charge_group: str
    is_strong: bool
    pka: float | None
    monomer_mw_g_mol: float
    monomer_smiles: str
    backbone_type: str
