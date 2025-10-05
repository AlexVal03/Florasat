"""
FloraSat Flowering Risk Calculator
Fórmula mágica que combina NDVI + Temperatura + Humedad + GDD para calcular riesgo de floración
"""
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FloweringRiskResult:
    date: str
    risk_score: float  # 0-1, donde 1 = máximo riesgo de floración
    confidence: float  # 0-1, confianza en la predicción
    factors: Dict[str, float]  # Contribución de cada factor
    recommendation: str
    is_forecast: bool = False


class FloweringRiskCalculator:
    """
    🌸 ALGORITMO FLORASAT: Cálculo de Riesgo de Floración
    
    Fórmula: RIESGO = f(NDVI, Temperatura, Humedad, GDD, Estacionalidad)
    """
    
    def __init__(self):
        # Umbrales por tipo de cultivo
        self.crop_thresholds = {
            'arroz': {
                'ndvi_flowering': 0.75,
                'optimal_temp_range': (20, 30),
                'gdd_threshold': 1200,
                'humidity_optimal': (70, 85),
                'flowering_months': [6, 7, 8]  # Junio-Agosto
            },
            'trigo': {
                'ndvi_flowering': 0.70,
                'optimal_temp_range': (15, 25),
                'gdd_threshold': 1500,
                'humidity_optimal': (60, 75),
                'flowering_months': [4, 5, 6]  # Abril-Junio
            },
            'maiz': {
                'ndvi_flowering': 0.80,
                'optimal_temp_range': (18, 28),
                'gdd_threshold': 1400,
                'humidity_optimal': (65, 80),
                'flowering_months': [7, 8, 9]  # Julio-Septiembre
            },
            'naranja': {
                'ndvi_flowering': 0.65,
                'optimal_temp_range': (16, 26),
                'gdd_threshold': 1000,
                'humidity_optimal': (55, 70),
                'flowering_months': [3, 4, 5]  # Marzo-Mayo
            },
            'oliva': {
                'ndvi_flowering': 0.60,
                'optimal_temp_range': (15, 25),
                'gdd_threshold': 800,
                'humidity_optimal': (50, 65),
                'flowering_months': [4, 5, 6]  # Abril-Junio
            },
            'tomate': {
                'ndvi_flowering': 0.78,
                'optimal_temp_range': (20, 28),
                'gdd_threshold': 900,
                'humidity_optimal': (60, 75),
                'flowering_months': [5, 6, 7, 8]  # Mayo-Agosto
            }
        }
    
    def calculate_flowering_risk(
        self,
        ndvi: float,
        temperature: float,
        humidity: float,
        date_str: str,
        crop: str = 'arroz',
        accumulated_gdd: Optional[float] = None,
        is_forecast: bool = False
    ) -> FloweringRiskResult:
        """
        🧮 FÓRMULA MÁGICA FLORASAT
        
        Calcula el riesgo de floración combinando múltiples factores
        """
        crop_params = self.crop_thresholds.get(crop, self.crop_thresholds['arroz'])
        date_obj = datetime.fromisoformat(date_str[:10])
        
        # 1. Factor NDVI (40% peso)
        ndvi_factor = self._calculate_ndvi_factor(ndvi, crop_params)
        
        # 2. Factor Temperatura (25% peso)
        temp_factor = self._calculate_temperature_factor(temperature, crop_params)
        
        # 3. Factor Humedad (15% peso)
        humidity_factor = self._calculate_humidity_factor(humidity, crop_params)
        
        # 4. Factor GDD - Growing Degree Days (10% peso)
        gdd_factor = self._calculate_gdd_factor(accumulated_gdd or self._estimate_gdd(date_obj), crop_params)
        
        # 5. Factor Estacional (10% peso)
        seasonal_factor = self._calculate_seasonal_factor(date_obj, crop_params)
        
        # FÓRMULA COMBINADA
        risk_score = (
            ndvi_factor * 0.40 +
            temp_factor * 0.25 +
            humidity_factor * 0.15 +
            gdd_factor * 0.10 +
            seasonal_factor * 0.10
        )
        
        # Confianza (menor para pronósticos futuros)
        confidence = 0.95 if not is_forecast else max(0.3, 0.95 - (abs((date_obj - datetime.now()).days) / 30) * 0.5)
        
        factors = {
            'ndvi': ndvi_factor,
            'temperature': temp_factor,
            'humidity': humidity_factor,
            'gdd': gdd_factor,
            'seasonal': seasonal_factor
        }
        
        recommendation = self._generate_recommendation(risk_score, factors, crop)
        
        return FloweringRiskResult(
            date=date_str,
            risk_score=risk_score,
            confidence=confidence,
            factors=factors,
            recommendation=recommendation,
            is_forecast=is_forecast
        )
    
    def _calculate_ndvi_factor(self, ndvi: float, crop_params: Dict) -> float:
        """Factor NDVI: Proximidad al umbral de floración"""
        threshold = crop_params['ndvi_flowering']
        
        if ndvi >= threshold:
            # Alto NDVI = alta probabilidad de floración inminente
            return min(1.0, (ndvi - threshold) / (1.0 - threshold) + 0.7)
        else:
            # NDVI bajo = floración menos probable
            return max(0.0, ndvi / threshold * 0.6)
    
    def _calculate_temperature_factor(self, temp: float, crop_params: Dict) -> float:
        """Factor Temperatura: Proximidad al rango óptimo"""
        min_temp, max_temp = crop_params['optimal_temp_range']
        
        if min_temp <= temp <= max_temp:
            # Temperatura óptima = alta probabilidad de floración
            return 0.9
        elif temp < min_temp:
            # Muy frío = floración retrasada
            return max(0.1, (temp / min_temp) * 0.4)
        else:
            # Muy calor = estrés, floración irregular
            return max(0.1, 0.8 - ((temp - max_temp) / 20) * 0.6)
    
    def _calculate_humidity_factor(self, humidity: float, crop_params: Dict) -> float:
        """Factor Humedad: Rango óptimo para floración"""
        min_hum, max_hum = crop_params['humidity_optimal']
        
        if min_hum <= humidity <= max_hum:
            return 0.8
        elif humidity < min_hum:
            # Muy seco = estrés hídrico
            return max(0.2, humidity / min_hum * 0.6)
        else:
            # Muy húmedo = riesgo de hongos
            return max(0.3, 0.7 - ((humidity - max_hum) / 30) * 0.4)
    
    def _calculate_gdd_factor(self, accumulated_gdd: float, crop_params: Dict) -> float:
        """Factor Growing Degree Days: Acumulación térmica"""
        threshold = crop_params['gdd_threshold']
        
        ratio = accumulated_gdd / threshold
        
        if ratio >= 0.9:
            # GDD suficientes = floración probable
            return min(1.0, ratio)
        else:
            # GDD insuficientes = floración temprana
            return max(0.1, ratio * 0.7)
    
    def _calculate_seasonal_factor(self, date_obj: datetime, crop_params: Dict) -> float:
        """Factor Estacional: Época típica de floración"""
        flowering_months = crop_params['flowering_months']
        current_month = date_obj.month
        
        if current_month in flowering_months:
            return 0.9
        
        # Calcular distancia al mes de floración más cercano
        distances = [min(abs(current_month - fm), 12 - abs(current_month - fm)) 
                    for fm in flowering_months]
        min_distance = min(distances)
        
        # Reducir factor según distancia
        return max(0.1, 0.8 - (min_distance / 6) * 0.6)
    
    def _estimate_gdd(self, date_obj: datetime) -> float:
        """Estimar GDD acumulados basado en la fecha (simulación)"""
        # Simulación: Acumular desde inicio de año
        start_year = datetime(date_obj.year, 1, 1)
        days_elapsed = (date_obj - start_year).days
        
        # Estimar temperatura media diaria basada en estacionalidad Valencia
        avg_temp = 15 + 8 * math.sin((date_obj.timetuple().tm_yday / 365) * 2 * math.pi - math.pi/2)
        base_temp = 10  # Temperatura base para GDD
        
        daily_gdd = max(0, avg_temp - base_temp)
        return daily_gdd * days_elapsed
    
    def _generate_recommendation(self, risk_score: float, factors: Dict, crop: str) -> str:
        """Generar recomendación basada en el riesgo"""
        if risk_score >= 0.8:
            return f"🚨 RIESGO ALTO: {crop} en período crítico de floración. Monitorear daily y preparar protección."
        elif risk_score >= 0.6:
            return f"⚠️ RIESGO MEDIO: {crop} aproximándose a floración. Verificar condiciones en próximos días."
        elif risk_score >= 0.4:
            return f"🟡 RIESGO BAJO: {crop} en pre-floración. Condiciones favorables para desarrollo."
        else:
            return f"✅ RIESGO MÍNIMO: {crop} no en período de floración. Mantener cuidados básicos."
    
    def calculate_forecast_risk(
        self,
        historical_data: List[Dict],
        forecast_data: List[Dict],
        crop: str = 'arroz'
    ) -> List[FloweringRiskResult]:
        """
        📈 PRONÓSTICO DE RIESGO DE FLORACIÓN
        
        Calcula riesgo para próximo mes basado en tendencias históricas
        """
        results = []
        
        # Calcular para datos históricos
        for data in historical_data:
            result = self.calculate_flowering_risk(
                ndvi=data.get('ndvi', 0.5),
                temperature=data.get('temperature', 20),
                humidity=data.get('humidity', 70),
                date_str=data['date'],
                crop=crop,
                is_forecast=False
            )
            results.append(result)
        
        # Calcular para pronósticos futuros
        for data in forecast_data:
            # Estimar NDVI futuro basado en tendencia
            estimated_ndvi = self._estimate_future_ndvi(historical_data, data['date'])
            
            result = self.calculate_flowering_risk(
                ndvi=estimated_ndvi,
                temperature=data.get('temperature', 20),
                humidity=data.get('humidity', 70),
                date_str=data['date'],
                crop=crop,
                is_forecast=True
            )
            results.append(result)
        
        return results
    
    def _estimate_future_ndvi(self, historical_data: List[Dict], target_date: str) -> float:
        """Estimar NDVI futuro basado en tendencia histórica"""
        if len(historical_data) < 3:
            return 0.5  # Valor por defecto
        
        # Extraer valores NDVI recientes
        recent_ndvi = [d.get('ndvi', 0.5) for d in historical_data[-10:]]
        
        # Calcular tendencia simple
        trend = (recent_ndvi[-1] - recent_ndvi[0]) / len(recent_ndvi)
        
        # Proyectar hacia adelante con límites
        days_ahead = (datetime.fromisoformat(target_date[:10]) - 
                     datetime.fromisoformat(historical_data[-1]['date'][:10])).days
        
        projected_ndvi = recent_ndvi[-1] + (trend * days_ahead)
        
        # Aplicar límites realistas
        return max(0.1, min(0.9, projected_ndvi))