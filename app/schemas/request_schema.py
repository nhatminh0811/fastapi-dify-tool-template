from typing import Optional

from pydantic import BaseModel


class GenerateTextRequest(BaseModel):
    """Request model for generating text."""

    input_text: Optional[str] = None


class GenerateQuizz(BaseModel):
    num_questions: Optional[str] = None  
    file_path: Optional[str] = None
