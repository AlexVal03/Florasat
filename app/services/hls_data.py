import math
import datetime as dt
import numpy as np
from typing import List, Dict
from app.core.config import settings
from app.services.phenology_advanced import AdvancedPhenology

class HLSDataService:
    def __init__(self):
        self.bbox = settings.VALENCIA_BBOX
        self.phenology = AdvancedPhenology()

    def simulate_highres_ndvi_grid(self, date: str, size: int=40) -> Dict:
        np.random.seed(abs(hash(date)) % (2**32 - 1))
        x = np.linspace(0, 4*math.pi, size)
        y = np.linspace(0, 4*math.pi, size)
        xv, yv = np.meshgrid(x, y)
        base = 0.55 + 0.25 * np.sin(xv) * np.cos(yv)
        d = dt.datetime.fromisoformat(date)
        seasonal = 0.15 * math.sin((d.timetuple().tm_yday / 365) * 2 * math.pi - math.pi/4)
        noise = np.random.normal(0, 0.02, base.shape)
        ndvi = np.clip(base + seasonal + noise, 0.1, 0.9)
        return {
            'date': date,
            'grid_size': size,
            'bbox': self.bbox,
            'ndvi_mean': round(float(ndvi.mean()), 3),
            'ndvi_min': float(ndvi.min()),
            'ndvi_max': float(ndvi.max()),
            'ndvi_sample': ndvi[::5, ::5].round(3).tolist()
        }

    def get_time_series_simulated(self, start: str, end: str, step_days: int=16) -> List[Dict]:
        start_dt = dt.datetime.fromisoformat(start)
        end_dt = dt.datetime.fromisoformat(end)
        current = start_dt
        series = []
        while current <= end_dt:
            result = self.simulate_highres_ndvi_grid(current.strftime('%Y-%m-%d'))
            series.append({'date': result['date'], 'ndvi_mean': result['ndvi_mean']})
            current += dt.timedelta(days=step_days)
        return series

    def build_series_with_phenology(self, series):
        dates = [s['date'] for s in series]
        values = [s['ndvi_mean'] for s in series]
        events = self.phenology.detect(dates, values)
        return {
            'series': series,
            'phenology_events': events,
            'bbox': self.bbox,
            'source': 'HLS (simulated)',
            'notes': 'Simulated high-res NDVI pattern; replace with real HLS tiles later.'
        }

    def get_hls_series(self, start: str, end: str) -> Dict:
        series = self.get_time_series_simulated(start, end)
        return self.build_series_with_phenology(series)
