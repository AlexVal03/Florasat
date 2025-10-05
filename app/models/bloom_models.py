from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class BloomEvent(BaseModel):
    peak_date: str
    onset_date: Optional[str]
    duration_days: Optional[int]
    amplitude: Optional[float]
    reliability: float
    anomaly_days: Optional[float]
    peak_value: float
    baseline: Optional[float]
    supporting_peaks: int
    
    # 🌡️ NUEVOS CAMPOS CLIMÁTICOS
    temperature_data: Optional[Dict[str, Any]] = None
    yield_prediction: Optional[Dict[str, Any]] = None
    weather_impact: Optional[str] = None
    
    class Config:
        extra = "allow"  # Permite campos adicionales

class AnomalyAlert(BaseModel):
    date: str
    type: str  # 'drought_stress', 'fire_risk', 'vegetation_anomaly'
    severity: float  # 0-1 scale
    description: str
    location: str
    recommendation: str

class CropRecommendation(BaseModel):
    crop: str
    current_status: str
    recommendations: List[str]
    next_actions: str
    risks: str
    optimal_planting_season: Optional[str] = None
    expected_yield: Optional[str] = None

class PhenologyAnalysis(BaseModel):
    region: str
    bbox: List[float]
    product: str
    years: List[int]
    events: List[BloomEvent]
    series: List[dict]
    notes: Optional[str] = None
