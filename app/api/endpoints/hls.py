from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
from app.services.hls_data import HLSDataService

router = APIRouter()
svc = HLSDataService()

@router.get('/series')
async def hls_series(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=240)).strftime('%Y-%m-%d')
    return svc.get_hls_series(start_date, end_date)

@router.get('/tile-snapshot')
async def hls_tile_snapshot(
    date: Optional[str] = Query(None, description='YYYY-MM-DD')
):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    return svc.simulate_highres_ndvi_grid(date)
