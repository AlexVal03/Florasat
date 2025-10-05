"""
🌍 SMART DATA SIMULATOR - FloraSat Advanced API Simulator
Simulador científicamente robusto para datos NASA, AEMET y forecasts 2022-2027

Características:
- Consistencia temporal y espacial
- Patrones climáticos realistas 
- Eventos extremos y anomalías
- Correlaciones entre variables
- Datos para múltiples cultivos
- Forecast probabilístico
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math
import random
from app.core.config import settings


@dataclass
class ClimateEvent:
    """Evento climático extremo"""
    name: str
    start_date: datetime
    duration_days: int
    intensity: float  # 0-1
    affects_ndvi: bool
    affects_temp: bool
    affects_humidity: bool


@dataclass
class SimulatedDataPoint:
    """Punto de datos simulado con metadata"""
    date: str
    ndvi: float
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    pressure: float
    source: str
    confidence: float
    anomaly_flags: List[str]


class SmartDataSimulator:
    """
    🧠 SIMULADOR INTELIGENTE DE DATOS CLIMÁTICOS
    
    Genera datos consistentes y realistas para:
    - NASA MODIS NDVI (2022-2027)
    - AEMET Weather (2022-2027) 
    - Forecasts probabilísticos (hasta 30 días)
    """
    
    def __init__(self):
        # Configuración de Valencia
        self.valencia_lat = settings.VALENCIA_LAT
        self.valencia_lon = settings.VALENCIA_LON
        
        # Parámetros climáticos base de Valencia
        self.climate_params = {
            'temp_annual_avg': 18.5,      # °C
            'temp_amplitude': 12.0,       # Variación estacional
            'humidity_avg': 65.0,         # %
            'humidity_variation': 20.0,   # Variación estacional
            'ndvi_base': 0.45,           # NDVI base
            'ndvi_crop_boost': 0.35,     # Incremento por cultivos
            'precipitation_annual': 450,  # mm/año
        }
        
        # Patrones de cultivos Valencia
        self.crop_cycles = {
            'arroz': {
                'planting': [90, 120],      # Día del año (abril-mayo)
                'flowering': [180, 210],    # Junio-julio
                'harvest': [240, 270],      # Agosto-septiembre
                'ndvi_peak': 0.85,
                'duration': 180
            },
            'naranja': {
                'flowering': [75, 135],     # Marzo-mayo
                'harvest': [300, 60],       # Nov-febrero (cruza año)
                'ndvi_peak': 0.70,
                'duration': 365
            },
            'trigo': {
                'planting': [300, 330],     # Octubre-noviembre
                'flowering': [105, 135],    # Abril-mayo
                'harvest': [165, 195],      # Junio-julio
                'ndvi_peak': 0.75,
                'duration': 240
            }
        }
        
        # Eventos climáticos históricos y futuros
        self.climate_events = self._generate_climate_events()
        
        # Cache para consistencia
        self._data_cache = {}
        
    def _generate_climate_events(self) -> List[ClimateEvent]:
        """Genera eventos climáticos realistas para 2022-2027"""
        events = []
        
        # Sequías ocasionales
        events.append(ClimateEvent(
            name="Sequía Mediterránea 2023",
            start_date=datetime(2023, 6, 15),
            duration_days=90,
            intensity=0.7,
            affects_ndvi=True,
            affects_temp=True,
            affects_humidity=True
        ))
        
        # Olas de calor
        events.append(ClimateEvent(
            name="Ola de Calor 2024",
            start_date=datetime(2024, 7, 10),
            duration_days=15,
            intensity=0.8,
            affects_ndvi=True,
            affects_temp=True,
            affects_humidity=False
        ))
        
        # Lluvias intensas
        events.append(ClimateEvent(
            name="Temporal Mediterráneo 2025",
            start_date=datetime(2025, 9, 20),
            duration_days=7,
            intensity=0.6,
            affects_ndvi=False,
            affects_temp=False,
            affects_humidity=True
        ))
        
        # Eventos futuros probabilísticos
        events.append(ClimateEvent(
            name="Sequía Proyectada 2026",
            start_date=datetime(2026, 5, 1),
            duration_days=60,
            intensity=0.5,
            affects_ndvi=True,
            affects_temp=True,
            affects_humidity=True
        ))
        
        return events
    
    def generate_ndvi_timeseries(
        self, 
        start_date: str, 
        end_date: str, 
        crop: str = 'mixed',
        lat: float = None,
        lon: float = None
    ) -> Dict:
        """
        🛰️ GENERA SERIE TEMPORAL NDVI REALISTA
        
        Combina:
        - Ciclos estacionales naturales
        - Patrones de cultivos específicos
        - Eventos climáticos extremos
        - Variabilidad espacial y temporal
        """
        lat = lat or self.valencia_lat
        lon = lon or self.valencia_lon
        
        cache_key = f"ndvi_{start_date}_{end_date}_{crop}_{lat}_{lon}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        # Generar fechas
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        dates = pd.date_range(start=start_dt, end=end_dt, freq='16D')  # MODIS cada 16 días
        
        data_points = []
        
        for date in dates:
            # 1. NDVI base estacional
            day_of_year = date.timetuple().tm_yday
            seasonal_ndvi = self.climate_params['ndvi_base'] + \
                          0.15 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/4)
            
            # 2. Influencia de cultivos
            crop_ndvi = self._calculate_crop_ndvi(day_of_year, crop)
            combined_ndvi = seasonal_ndvi + crop_ndvi
            
            # 3. Efectos de eventos climáticos
            event_factor = self._get_climate_event_factor(date, 'ndvi')
            combined_ndvi *= event_factor
            
            # 4. Variabilidad espacial y temporal
            spatial_factor = 1 + 0.05 * np.sin(lat * np.pi / 180) * np.cos(lon * np.pi / 180)
            temporal_noise = np.random.normal(0, 0.03)
            
            final_ndvi = combined_ndvi * spatial_factor + temporal_noise
            final_ndvi = max(0.1, min(0.9, final_ndvi))
            
            # 5. Detectar anomalías
            anomalies = self._detect_ndvi_anomalies(final_ndvi, day_of_year, crop)
            
            data_points.append({
                'date': date.strftime('%Y-%m-%d'),
                'ndvi': round(final_ndvi, 4),
                'bloom_probability': min(1.0, max(0.0, (final_ndvi - 0.4) / 0.4)),
                'anomaly_flags': anomalies,
                'confidence': 0.95 if date <= datetime.now() else max(0.3, 0.95 - (date - datetime.now()).days / 60)
            })
        
        result = {
            'location': 'Valencia, Spain (Simulated)',
            'coordinates': {'lat': lat, 'lon': lon},
            'data': data_points,
            'source': 'SmartSimulator - NASA MODIS Pattern',
            'crop_influence': crop,
            'temporal_range': f"{start_date} to {end_date}",
            'data_quality': 'High-fidelity simulation',
            'bbox': settings.VALENCIA_BBOX
        }
        
        self._data_cache[cache_key] = result
        return result
    
    def generate_weather_timeseries(
        self,
        start_date: str,
        end_date: str,
        lat: float = None,
        lon: float = None,
        daily: bool = True
    ) -> List[Dict]:
        """
        🌤️ GENERA SERIE TEMPORAL METEOROLÓGICA REALISTA
        
        Incluye:
        - Patrones estacionales mediterráneos
        - Correlaciones realistas entre variables
        - Eventos extremos
        - Forecasts probabilísticos
        """
        lat = lat or self.valencia_lat
        lon = lon or self.valencia_lon
        
        cache_key = f"weather_{start_date}_{end_date}_{lat}_{lon}_{daily}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        freq = 'D' if daily else 'H'
        dates = pd.date_range(start=start_dt, end=end_dt, freq=freq)
        
        weather_data = []
        
        for i, date in enumerate(dates):
            day_of_year = date.timetuple().tm_yday
            
            # 1. Temperatura con patrón mediterráneo
            base_temp = self.climate_params['temp_annual_avg'] + \
                       self.climate_params['temp_amplitude'] * \
                       np.sin((day_of_year / 365) * 2 * np.pi - np.pi/2)
            
            # Variación diaria si es horario
            if not daily and date.hour:
                daily_variation = 8 * np.sin((date.hour / 24) * 2 * np.pi - np.pi/2)
                base_temp += daily_variation
            
            # 2. Humedad correlacionada inversamente con temperatura
            base_humidity = self.climate_params['humidity_avg'] - \
                          (base_temp - self.climate_params['temp_annual_avg']) * 1.5
            
            # 3. Efectos de eventos climáticos
            temp_event_factor = self._get_climate_event_factor(date, 'temperature')
            humidity_event_factor = self._get_climate_event_factor(date, 'humidity')
            
            # 4. Aplicar factores y ruido
            final_temp = base_temp * temp_event_factor + np.random.normal(0, 2)
            final_humidity = base_humidity * humidity_event_factor + np.random.normal(0, 5)
            final_humidity = max(20, min(95, final_humidity))
            
            # 5. Variables adicionales
            pressure = 1013 + np.random.normal(0, 10) + 5 * np.sin(day_of_year / 365 * 2 * np.pi)
            wind_speed = max(0, 8 + np.random.normal(0, 4))
            precipitation = max(0, np.random.exponential(0.5) if np.random.random() < 0.1 else 0)
            
            # 6. Calcular métricas derivadas
            et0_estimate = self._calculate_et0(final_temp, final_humidity, wind_speed)
            irrigation_need = self._assess_irrigation_need(et0_estimate, precipitation, day_of_year)
            
            # 7. Confianza (menor para forecasts)
            confidence = 0.95 if date <= datetime.now() else max(0.4, 0.95 - (date - datetime.now()).days / 20)
            
            weather_data.append({
                'date': date.strftime('%Y-%m-%d %H:%M:%S' if not daily else '%Y-%m-%d'),
                'temperature': round(final_temp, 1),
                'humidity': round(final_humidity, 1),
                'pressure': round(pressure, 1),
                'wind_speed': round(wind_speed, 1),
                'precipitation': round(precipitation, 1),
                'et0_estimate': round(et0_estimate, 2),
                'irrigation_need': irrigation_need,
                'confidence': round(confidence, 2),
                'is_forecast': date > datetime.now(),
                'provider_info': {
                    'name': 'SmartSimulator',
                    'description': 'High-fidelity Mediterranean climate simulation',
                    'accuracy': 'Research grade simulation'
                }
            })
        
        self._data_cache[cache_key] = weather_data
        return weather_data
    
    def generate_forecast(
        self,
        days: int = 14,
        lat: float = None,
        lon: float = None
    ) -> List[Dict]:
        """
        📅 GENERA PRONÓSTICO METEOROLÓGICO PROBABILÍSTICO
        """
        today = datetime.now()
        end_date = today + timedelta(days=days)
        
        return self.generate_weather_timeseries(
            start_date=today.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            lat=lat,
            lon=lon,
            daily=True
        )
    
    def _calculate_crop_ndvi(self, day_of_year: int, crop: str) -> float:
        """Calcula influencia del cultivo en NDVI"""
        if crop == 'mixed' or crop not in self.crop_cycles:
            return 0.1  # Influencia mínima para paisaje mixto
        
        cycle = self.crop_cycles[crop]
        
        # Determinar fase del cultivo
        if crop == 'naranja':  # Perenne
            if 75 <= day_of_year <= 135:  # Floración
                return cycle['ndvi_peak'] * 0.8
            elif 300 <= day_of_year or day_of_year <= 60:  # Cosecha
                return cycle['ndvi_peak'] * 0.6
            else:
                return cycle['ndvi_peak'] * 0.4
        
        else:  # Cultivos anuales
            planting_start, planting_end = cycle['planting']
            flowering_start, flowering_end = cycle['flowering']
            harvest_start, harvest_end = cycle['harvest']
            
            if planting_start <= day_of_year <= flowering_start:
                # Fase de crecimiento
                progress = (day_of_year - planting_start) / (flowering_start - planting_start)
                return cycle['ndvi_peak'] * progress * 0.7
            
            elif flowering_start <= day_of_year <= flowering_end:
                # Fase de floración - NDVI máximo
                return cycle['ndvi_peak']
            
            elif flowering_end <= day_of_year <= harvest_end:
                # Fase de maduración
                progress = (harvest_end - day_of_year) / (harvest_end - flowering_end)
                return cycle['ndvi_peak'] * progress * 0.8
            
            else:
                return 0.05  # Campo en barbecho
    
    def _get_climate_event_factor(self, date: datetime, variable: str) -> float:
        """Obtiene factor de modificación por eventos climáticos"""
        factor = 1.0
        
        for event in self.climate_events:
            if event.start_date <= date <= event.start_date + timedelta(days=event.duration_days):
                days_into_event = (date - event.start_date).days
                intensity_curve = np.sin(np.pi * days_into_event / event.duration_days)
                current_intensity = event.intensity * intensity_curve
                
                if variable == 'ndvi' and event.affects_ndvi:
                    if 'Sequía' in event.name:
                        factor *= (1 - current_intensity * 0.3)  # NDVI baja en sequía
                    elif 'Calor' in event.name:
                        factor *= (1 - current_intensity * 0.2)  # NDVI baja con calor extremo
                
                elif variable == 'temperature' and event.affects_temp:
                    if 'Calor' in event.name:
                        factor *= (1 + current_intensity * 0.4)  # Temperatura alta
                    elif 'Sequía' in event.name:
                        factor *= (1 + current_intensity * 0.2)  # Temperatura moderadamente alta
                
                elif variable == 'humidity' and event.affects_humidity:
                    if 'Sequía' in event.name:
                        factor *= (1 - current_intensity * 0.3)  # Humedad baja
                    elif 'Temporal' in event.name:
                        factor *= (1 + current_intensity * 0.4)  # Humedad alta
        
        return max(0.3, min(2.0, factor))  # Limitar cambios extremos
    
    def _detect_ndvi_anomalies(self, ndvi: float, day_of_year: int, crop: str) -> List[str]:
        """Detecta anomalías en valores NDVI"""
        anomalies = []
        
        # NDVI extremadamente bajo
        if ndvi < 0.2:
            anomalies.append('very_low_vegetation')
        
        # NDVI extremadamente alto
        if ndvi > 0.85:
            anomalies.append('very_high_vegetation')
        
        # Anomalías estacionales
        expected_range = self._get_expected_ndvi_range(day_of_year, crop)
        if ndvi < expected_range[0]:
            anomalies.append('below_seasonal_normal')
        elif ndvi > expected_range[1]:
            anomalies.append('above_seasonal_normal')
        
        return anomalies
    
    def _get_expected_ndvi_range(self, day_of_year: int, crop: str) -> Tuple[float, float]:
        """Obtiene rango esperado de NDVI para la época del año"""
        seasonal_base = 0.45 + 0.15 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/4)
        crop_influence = self._calculate_crop_ndvi(day_of_year, crop)
        
        expected = seasonal_base + crop_influence
        margin = 0.15
        
        return (max(0.1, expected - margin), min(0.9, expected + margin))
    
    def _calculate_et0(self, temp: float, humidity: float, wind_speed: float) -> float:
        """Calcula evapotranspiración de referencia simplificada"""
        # Fórmula simplificada de Penman-Monteith
        delta = 4098 * (0.6108 * math.exp(17.27 * temp / (temp + 237.3))) / ((temp + 237.3) ** 2)
        gamma = 0.665  # kPa/°C
        u2 = wind_speed * 4.87 / math.log(67.8 * 10 - 5.42)  # Ajuste altura viento
        
        et0 = (0.408 * delta * (temp) + gamma * 900 / (temp + 273) * u2 * (0.01 * (100 - humidity))) / (delta + gamma * (1 + 0.34 * u2))
        
        return max(0, et0)
    
    def _assess_irrigation_need(self, et0: float, precipitation: float, day_of_year: int) -> str:
        """Evalúa necesidad de riego"""
        net_water_demand = et0 - precipitation
        
        # Ajuste estacional
        summer_factor = 1 + 0.5 * np.sin((day_of_year - 90) / 365 * 2 * np.pi)
        adjusted_demand = net_water_demand * summer_factor
        
        if adjusted_demand > 6:
            return "HIGH - Riego urgente recomendado"
        elif adjusted_demand > 4:
            return "MODERATE - Considerar riego"
        elif adjusted_demand > 2:
            return "LOW - Monitorear suelo"
        else:
            return "MINIMAL - Sin riego necesario"
    
    def get_current_weather_simulation(self, station_id: str = None) -> Dict:
        """Simula datos meteorológicos actuales formato AEMET"""
        now = datetime.now()
        current_data = self.generate_weather_timeseries(
            start_date=now.strftime('%Y-%m-%d'),
            end_date=now.strftime('%Y-%m-%d'),
            daily=False
        )[0]
        
        return {
            'temperature': current_data['temperature'],
            'humidity': current_data['humidity'],
            'pressure': current_data['pressure'],
            'wind_speed': current_data['wind_speed'],
            'precipitation': current_data['precipitation'],
            'et0_estimate': current_data['et0_estimate'],
            'irrigation_need': current_data['irrigation_need'],
            'station': station_id or "8416A_SIMULATED",
            'timestamp': now.isoformat(),
            'confidence': 0.95,
            'source': 'SmartSimulator - AEMET Pattern',
            'is_simulated': True
        }


# Instancia global
smart_simulator = SmartDataSimulator()