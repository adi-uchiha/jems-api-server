from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/")
async def create_task():
    try:
        return {"status": "Alive"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
