from pydantic import BaseModel


class InputSchema(BaseModel):
    query: str
    output_file: str