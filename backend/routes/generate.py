from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.llm import generate_text
from services.auth import get_current_user

generate_router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str = ""


class GenerateResponse(BaseModel):
    text: str


@generate_router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, _user=Depends(get_current_user)):
    """Send text + prompt to LLM, return generated response."""
    try:
        result = await generate_text(req.prompt, req.system_prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    return GenerateResponse(text=result)
