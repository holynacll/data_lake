from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    ticket_code: str
    vl_total: float
    operation_type: str
    success: bool
    message: str
    num_ped_ecf: int | None = None
    num_cupom: int | None =  None
    num_caixa: int | None = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)