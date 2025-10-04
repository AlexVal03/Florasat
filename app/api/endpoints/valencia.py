from fastapi import APIRouter, Query
from typing import Optional, Dict
from datetime import datetime, timedelta
from app.services.nasa_data import NASADataService

router = APIRouter()
service = NASADataService()

@router.get('/ndvi')
async def get_valencia_ndvi(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
) -> Dict:
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    return await service.get_modis_ndvi_valencia(start_date, end_date)

@router.get('/ndvi-real')
async def get_valencia_ndvi_real(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
) -> Dict:
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    return await service.get_modis_ndvi_valencia(start_date, end_date, real=True)
