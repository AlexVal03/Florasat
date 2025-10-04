from pydantic_settings import BaseSettings
from typing import Optional, Tuple, List

class Settings(BaseSettings):
    NASA_EARTHDATA_USERNAME: Optional[str] = None
    NASA_EARTHDATA_PASSWORD: Optional[str] = None
    NASA_CMR_TOKEN: Optional[str] = None

    # Weather Data Providers Configuration
    WEATHER_PROVIDERS: str = "aemet,meteomatics"  # Comma-separated list: aemet, meteomatics, fusion
    PRIMARY_WEATHER_PROVIDER: str = "aemet"  # Primary provider when multiple available
    
    # AEMET (Spanish Weather Service) settings
    AEMET_API_KEY: Optional[str] = None
    AEMET_BASE_URL: str = "https://opendata.aemet.es/opendata/api"
    VALENCIA_WEATHER_STATION: str = "8416A"  # Valencia Airport
    
    # Meteomatics Weather API settings
    METEOMATICS_USERNAME: Optional[str] = None
    METEOMATICS_PASSWORD: Optional[str] = None
    METEOMATICS_BASE_URL: str = "https://api.meteomatics.com"

    # Valencia defaults
    VALENCIA_LAT: float = 39.4699
    VALENCIA_LON: float = -0.3763
    VALENCIA_BBOX: Tuple[float, float, float, float] = (39.2, -0.6, 39.7, -0.1)  # (lat_min, lon_min, lat_max, lon_max)
    VALENCIA_MUNICIPALITY_CODE: str = "46250"  # For AEMET forecasts

    # Internationalization
    DEFAULT_LANGUAGE: str = "es"  # Spanish by default
    SUPPORTED_LANGUAGES: List[str] = ["es", "en"]  # Spanish, English

    DEBUG: bool = True

    class Config:
        env_file = '.env'

settings = Settings()
