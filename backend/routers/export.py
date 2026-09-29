from fastapi import APIRouter

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/")
async def export_data():
    return {"message": "Data exported successfully"}
