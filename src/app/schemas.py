from pydantic import BaseModel, ConfigDict, field_validator


class ItemBase(BaseModel):
    ticket_code: str
    vl_total: float
    operation_type: str
    success: bool
    message: str
    num_ped_ecf: str | None = None
    num_cupom: int | None = None
    num_caixa: int | None = None
    hostname: str | None = None

    @field_validator("num_ped_ecf", mode="before")
    @classmethod
    def coerce_num_ped_ecf(cls, v):
        """Aceita int de clientes antigos e converte para str."""
        if isinstance(v, int):
            return str(v)
        return v

    @field_validator("operation_type", mode="before")
    @classmethod
    def coerce_operation_type(cls, v):
        """Aceita int de clientes antigos e converte para str."""
        if isinstance(v, int):
            mapping = {
                15: "MANUAL_VALIDATION",
                16: "AUTOMATIC_VALIDATION",
            }
            return mapping.get(v, "UNKNOWN")
        return v


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)