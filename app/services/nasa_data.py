import os
import pandas as pd
from typing import Dict, List
from app.core.config import settings
from datetime import datetime
from .appeears_client import AppEEARSClient

class NASADataService:
    def __init__(self):
        self.valencia_bbox = settings.VALENCIA_BBOX

    async def get_modis_ndvi_valencia(self, start_date: str, end_date: str, real: bool=False) -> Dict:
        if real:
            try:
                return await self._fetch_modis_real(start_date, end_date)
            except Exception as e:
                # Fallback to simulation with warning
                sim = await self._simulate_valencia_ndvi_data(start_date, end_date)
                sim["warning"] = f"Real MODIS fetch failed: {e}. Using simulated data."
                return sim
        return await self._simulate_valencia_ndvi_data(start_date, end_date)

    async def _fetch_modis_real(self, start_date: str, end_date: str) -> Dict:
        username = settings.NASA_EARTHDATA_USERNAME
        password = settings.NASA_EARTHDATA_PASSWORD
        if not (username and password):
            raise RuntimeError("Earthdata credentials not configured.")
        task_def = self._build_appeears_task(start_date, end_date)
        client = AppEEARSClient(username, password)
        task_id = client.create_task(task_def)
        status = client.wait_task(task_id, poll=25)
        if status.get("status") != "done":
            raise RuntimeError(f"AppEEARS task not done: {status}")
        out_dir = "data/processed"
        files = client.download_csv_files(task_id, out_dir)
        if not files:
            raise RuntimeError("No CSV files returned by AppEEARS")
        series = self._parse_appeears_ndvi(files)
        return {
            'location': 'Valencia, Spain',
            'coordinates': {'lat': settings.VALENCIA_LAT, 'lon': settings.VALENCIA_LON},
            'data': series,
            'source': 'MOD13Q1.061 via AppEEARS',
            'bbox': self.valencia_bbox
        }

    def _build_appeears_task(self, start: str, end: str) -> Dict:
        lat_min, lon_min, lat_max, lon_max = self.valencia_bbox
        return {
            "task_type": "area",
            "task_name": "valencia_mod13q1_ndvi",
            "params": {
                "dates": [{"startDate": start, "endDate": end}],
                "layers": [{"product": "MOD13Q1.061", "layer": "NDVI"}],
                "output": {"format": {"type": "csv"}, "projection": "geographic"},
                "geo": {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [lon_min, lat_min],
                            [lon_max, lat_min],
                            [lon_max, lat_max],
                            [lon_min, lat_max],
                            [lon_min, lat_min]
                        ]]
                    }
                }
            }
        }

    def _parse_appeears_ndvi(self, csv_files: List[str]) -> List[Dict]:
        # AppEEARS NDVI usually scaled (e.g. integer). We normalize if >1.
        aggregate = {}
        for path in csv_files:
            df = pd.read_csv(path)
            # Heuristic column detection
            ndvi_col = next((c for c in df.columns if 'NDVI' in c.upper()), None)
            date_col = next((c for c in df.columns if c.lower() in ('date','time','datetime')), None)
            if not ndvi_col or not date_col:
                continue
            for _, row in df.iterrows():
                raw_val = row[ndvi_col]
                if pd.isna(raw_val):
                    continue
                date_str = str(row[date_col])[:10]
                val = float(raw_val)
                if val > 1:  # scaled int
                    val = val / 10000.0
                if date_str not in aggregate:
                    aggregate[date_str] = []
                aggregate[date_str].append(val)
        series = []
        for d, vals in sorted(aggregate.items()):
            ndvi = sum(vals)/len(vals)
            series.append({
                'date': d,
                'ndvi': round(ndvi, 4),
                'bloom_probability': min(1.0, max(0.0, (ndvi - 0.4) / 0.4))
            })
        return series

    async def _simulate_valencia_ndvi_data(self, start_date: str, end_date: str) -> Dict:
        dates = pd.date_range(start=start_date, end=end_date, freq='16D')
        ndvi_values = []
        for date in dates:
            month = date.month
            if month in [3, 4, 5]:
                ndvi = 0.6 + (month - 3) * 0.1
            elif month in [6, 7, 8]:
                ndvi = 0.8 + 0.05 * (8 - month)
            elif month in [9, 10, 11]:
                ndvi = 0.7 - (month - 9) * 0.1
            else:
                ndvi = 0.4 + 0.05 * abs(6 - month)
            ndvi_values.append(round(ndvi, 3))
        return {
            'location': 'Valencia, Spain',
            'coordinates': {
                'lat': settings.VALENCIA_LAT,
                'lon': settings.VALENCIA_LON
            },
            'data': [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'ndvi': ndvi,
                    'bloom_probability': min(1.0, max(0.0, (ndvi - 0.4) / 0.4))
                }
                for date, ndvi in zip(dates, ndvi_values)
            ],
            'source': 'NASA MODIS Terra/Aqua (simulated)',
            'bbox': self.valencia_bbox
        }
