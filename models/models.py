from pydantic import BaseModel


class InputSchema(BaseModel):
    query: str
    curl_file: str
    output_file: str