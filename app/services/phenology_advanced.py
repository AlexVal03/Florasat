import numpy as np
try:
    from scipy.signal import savgol_filter, find_peaks  # type: ignore
    _SCIPY_AVAILABLE = True
except Exception:  # noqa
    _SCIPY_AVAILABLE = False
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import statistics
import asyncio

class AdvancedPhenology:
    def __init__(self, window: int = 5, poly: int = 2, deriv_threshold: float = 0.01):
        self.window = window if window % 2 == 1 else window + 1
        self.poly = poly
        self.deriv_threshold = deriv_threshold
        
    async def analyze_with_weather_data(self, dates: List[str], values: List[float], 
                                       lat: float = 39.4699, lon: float = -0.3763) -> List[Dict]:
        """
        🌡️ NEW: Análisis fenológico enriquecido con datos climáticos
        Combina NDVI + temperatura + precipitación para análisis completo
        """
        # Detectar eventos básicos primero
        events = self.detect(dates, values)
        
        # Enriquecer cada evento con datos climáticos
        for event in events:
            try:
                # Obtener datos de temperatura durante el período del evento
                temp_data = await self._get_temperature_for_period(
                    event['onset_date'], 
                    event['peak_date'], 
                    lat, lon
                )
                
                # Calcular rendimiento estimado
                yield_prediction = self._predict_yield(event, temp_data)
                
                # Añadir datos climáticos al evento
                event.update({
                    'temperature_data': temp_data,
                    'yield_prediction': yield_prediction,
                    'weather_impact': self._assess_weather_impact(event, temp_data)
                })
                
            except Exception as e:
                # Fallback si no hay datos climáticos
                event.update({
                    'temperature_data': {'avg_temp': 'N/A', 'status': f'Error: {str(e)}'},
                    'yield_prediction': {'estimated_yield': 'N/A', 'confidence': 'Low'},
                    'weather_impact': 'Data unavailable'
                })
        
        return events
        
    async def _get_temperature_for_period(self, start_date: str, end_date: str, 
                                         lat: float, lon: float) -> Dict:
        """Obtener datos de temperatura para un período específico"""
        try:
            # Importar aquí para evitar dependencias circulares
            from app.services.weather_coordinator import WeatherCoordinator
            
            weather = WeatherCoordinator()
            
            # Simular datos históricos para el período
            # En producción, esto haría llamadas a APIs históricas
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            # Para demo: simular temperaturas basadas en la fecha
            avg_temp = self._simulate_temperature_for_date(start_dt)
            max_temp = avg_temp + 8
            min_temp = avg_temp - 5
            
            # Obtener algunos datos actuales como referencia
            current_weather = await weather.get_current_weather("fusion", lat, lon)
            
            return {
                'period_start': start_date,
                'period_end': end_date,
                'avg_temp': round(avg_temp, 1),
                'max_temp': round(max_temp, 1),
                'min_temp': round(min_temp, 1),
                'current_reference': current_weather.get('temperature', avg_temp),
                'data_source': 'Simulated historical + Current fusion',
                'quality': 'Demo quality'
            }
            
        except Exception as e:
            return {
                'period_start': start_date,
                'period_end': end_date,
                'avg_temp': 'Error',
                'status': f'Could not fetch temperature data: {str(e)}',
                'quality': 'Unavailable'
            }
    
    def _simulate_temperature_for_date(self, date: datetime) -> float:
        """Simular temperatura basada en la época del año (Valencia)"""
        month = date.month
        day_of_year = date.timetuple().tm_yday
        
        # Simulación basada en clima de Valencia
        if month in [6, 7, 8]:  # Verano
            base_temp = 26 + 5 * np.sin((day_of_year - 150) * 2 * np.pi / 365)
        elif month in [12, 1, 2]:  # Invierno
            base_temp = 12 + 3 * np.sin((day_of_year - 365) * 2 * np.pi / 365)
        else:  # Primavera/Otoño
            base_temp = 19 + 6 * np.sin((day_of_year - 80) * 2 * np.pi / 365)
        
        # Añadir variación aleatoria pequeña
        variation = np.random.normal(0, 2)
        return max(5, min(40, base_temp + variation))
    
    def _predict_yield(self, event: Dict, temp_data: Dict) -> Dict:
        """
        🚜 Modelo predictivo de rendimiento basado en NDVI + temperatura
        Algoritmo simplificado para demo NASA Space Apps
        """
        try:
            # Parámetros del evento
            amplitude = event.get('amplitude', 0)
            duration = event.get('duration_days', 0)
            reliability = event.get('reliability', 0)
            
            # Datos de temperatura
            if isinstance(temp_data.get('avg_temp'), (int, float)):
                avg_temp = temp_data['avg_temp']
                
                # Algoritmo de predicción simplificado
                # Basado en temperatura óptima para cultivos mediterráneos (18-25°C)
                optimal_temp_range = (18, 25)
                
                if optimal_temp_range[0] <= avg_temp <= optimal_temp_range[1]:
                    temp_factor = 1.0  # Temperatura óptima
                elif avg_temp < optimal_temp_range[0]:
                    temp_factor = 0.7 + 0.3 * (avg_temp / optimal_temp_range[0])
                else:  # Temperatura alta
                    temp_factor = max(0.3, 1.0 - (avg_temp - optimal_temp_range[1]) / 20)
                
                # Cálculo de rendimiento estimado
                base_yield = amplitude * 100  # NDVI convertido a %
                duration_factor = min(1.0, duration / 120) if duration else 0.5
                reliability_factor = reliability
                
                estimated_yield_percent = (base_yield * temp_factor * 
                                         duration_factor * reliability_factor)
                
                # Traducir a escala interpretable
                yield_categories = {
                    (0, 15): ("Muy Bajo", "🔴"),
                    (15, 30): ("Bajo", "🟠"), 
                    (30, 50): ("Medio", "🟡"),
                    (50, 70): ("Bueno", "🟢"),
                    (70, 100): ("Excelente", "🟢🟢")
                }
                
                yield_category = "Medio"
                yield_emoji = "🟡"
                for (min_val, max_val), (category, emoji) in yield_categories.items():
                    if min_val <= estimated_yield_percent < max_val:
                        yield_category = category
                        yield_emoji = emoji
                        break
                
                return {
                    'estimated_yield_percent': round(estimated_yield_percent, 1),
                    'yield_category': yield_category,
                    'yield_emoji': yield_emoji,
                    'confidence': 'High' if reliability > 0.6 else 'Medium',
                    'factors': {
                        'ndvi_amplitude': round(amplitude, 3),
                        'duration_days': duration,
                        'temperature_factor': round(temp_factor, 2),
                        'reliability_score': round(reliability, 2)
                    },
                    'algorithm': 'FLORASAT AI v1.0 - NDVI + Temperature + Duration'
                }
            else:
                return {
                    'estimated_yield_percent': 'N/A',
                    'yield_category': 'No calculable',
                    'confidence': 'No data',
                    'note': 'Temperatura no disponible'
                }
                
        except Exception as e:
            return {
                'estimated_yield_percent': 'Error',
                'error': str(e),
                'confidence': 'Low'
            }
    
    def _assess_weather_impact(self, event: Dict, temp_data: Dict) -> str:
        """Evaluar el impacto del clima en el evento fenológico"""
        try:
            avg_temp = temp_data.get('avg_temp')
            if not isinstance(avg_temp, (int, float)):
                return "Sin datos de temperatura"
            
            # Análisis de impacto climático
            if avg_temp < 10:
                return "⚠️ Frío extremo - posible retraso en desarrollo"
            elif avg_temp < 15:
                return "🔵 Temperaturas bajas - crecimiento lento"
            elif 15 <= avg_temp <= 25:
                return "✅ Condiciones óptimas para crecimiento"
            elif 25 < avg_temp <= 30:
                return "🟠 Calor moderado - monitorear estrés hídrico"
            elif 30 < avg_temp <= 35:
                return "🔴 Estrés térmico - irrigación crítica"
            else:
                return "🚨 Calor extremo - riesgo alto para cultivos"
                
        except Exception:
            return "Error en análisis climático"

    def smooth(self, values: List[float]):
        if len(values) < self.window or not _SCIPY_AVAILABLE:
            # Simple moving average fallback
            arr = np.array(values, dtype=float)
            if len(arr) < 3:
                return arr
            k = min(5, len(arr))
            if k % 2 == 0:
                k -= 1
            pad = k // 2
            padded = np.pad(arr, (pad, pad), mode='edge')
            out = []
            for i in range(len(arr)):
                seg = padded[i:i + k]
                out.append(seg.mean())
            return np.array(out)
        return savgol_filter(values, self.window, self.poly)

    def detect(self, dates: List[str], values: List[float], historic_peaks: Optional[List[int]] = None) -> List[Dict]:
        if len(values) < 4:
            return []
        arr = np.array(values)
        smooth = self.smooth(arr.tolist())
        deriv = np.gradient(smooth)
        baseline = np.percentile(smooth, 10)  # Lowered from 20 to 10 for demo
        rel = smooth - baseline
        rel[rel < 0] = 0
        height_min = np.percentile(rel, 10)  # Lowered to 10 for demo to force events
        if _SCIPY_AVAILABLE:
            peaks, _ = find_peaks(rel, height=height_min, distance=2)
        else:
            # Naive peak detection: local maxima above threshold
            peaks = []
            for i in range(1, len(rel) - 1):
                if rel[i] >= rel[i-1] and rel[i] >= rel[i+1] and rel[i] >= height_min:
                    peaks.append(i)
            peaks = np.array(peaks, dtype=int)
        events = []
        import math
        for idx in peaks:
            peak_val = float(smooth[idx])
            onset_idx = max(0, idx - 1)
            for j in range(idx - 1, -1, -1):
                if deriv[j] < self.deriv_threshold or smooth[j] < baseline + 0.1 * (peak_val - baseline):
                    onset_idx = j
                    break
            half_level = baseline + 0.5 * (peak_val - baseline)
            end_idx = idx
            for k in range(idx + 1, len(smooth)):
                if smooth[k] < half_level:
                    end_idx = k
                    break
            duration = (self._dt(dates[end_idx]) - self._dt(dates[onset_idx])).days if end_idx > onset_idx else None
            anomaly = None
            if historic_peaks and len(historic_peaks) > 1:
                import statistics
                mean_peak = statistics.mean(historic_peaks)
                anomaly = (self._doy(dates[idx]) - mean_peak)
            reliability = min(1.0, (peak_val - baseline) / 0.5)
            events.append({
                'peak_date': dates[idx],
                'onset_date': dates[onset_idx],
                'duration_days': duration,
                'amplitude': round(peak_val - baseline, 3),
                'reliability': round(reliability, 2),
                'anomaly_days': round(anomaly, 1) if anomaly is not None else None,
                'peak_value': round(peak_val, 3),
                'baseline': round(float(baseline), 3),
                'supporting_peaks': len(peaks) - 1
            })
        return events

    def _dt(self, d: str) -> datetime:
        return datetime.fromisoformat(d)

    def _doy(self, d: str) -> int:
        return self._dt(d).timetuple().tm_yday
