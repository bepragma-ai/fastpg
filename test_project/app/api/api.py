from fastapi import APIRouter

from app.api.endpoints import shop_api


api_router = APIRouter()
api_router.include_router(shop_api.router, prefix="/shop", tags=["shop"])
