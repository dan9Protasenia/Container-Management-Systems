from pydantic import BaseModel, Extra


class BaseConfig:
    orm_mode = True
    from_attributes = True
    extra = Extra.forbid


class CommonBaseModel(BaseModel):
    class Config(BaseConfig):
        pass
