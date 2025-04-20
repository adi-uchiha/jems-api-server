from fastapi import APIRouter, HTTPException
from sentence_transformers import SentenceTransformer
from app.schemas.encode import EncodeRequest, EncodeResponse
from app.core.config import settings

router = APIRouter()
model = SentenceTransformer(settings.EMBEDDING_MODEL)

@router.post("/encode", response_model=EncodeResponse)
async def generate_embedding(request: EncodeRequest):
    """Generate text embedding using sentence transformer model"""
    try:
        embedding = model.encode(request.text).tolist()
        return {"embedding": embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
