"""
AEMET (Spanish Weather Service) Client for FLORASAT
Provides irrigation intelligence by combining weather data with satellite imagery
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from .smart_data_simulator import smart_simulator

class AEMETClient:
    """
    Client for AEMET Open Data API
    Provides weather data for precision irrigation recommendations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJxdWlxdWVudEBnbWFpbC5jb20iLCJqdGkiOiJlYTQwNjYzYi00Y2Q4LTRkYWYtYTY5My04OWJhNjBkNzY2ZGEiLCJpc3MiOiJBRU1FVCIsImlhdCI6MTczMzE2MTgzOCwidXNlcklkIjoiZWE0MDY2M2ItNGNkOC00ZGFmLWE2OTMtODliYTYwZDc2NmRhIiwicm9sZSI6IiJ9.oeSE-xrcoEiT2IUGO0rjqvnz-6ZLNcOSNwRMxT1sVnI"
        self.base_url = "https://opendata.aemet.es/opendata/api"
        self.valencia_station = "8416A"  # Valencia Airport weather station
        
    async def _make_request(self, endpoint: str) -> Dict:
        """Make authenticated request to AEMET API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"api_key": self.api_key}
            
            # Get data URL first
            response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
            response.raise_for_status()
            
            data_info = response.json()
            if not data_info.get("datos"):
                raise ValueError(f"No data URL returned from AEMET: {data_info}")
            
            # Get actual data
            data_response = await client.get(data_info["datos"])
            data_response.raise_for_status()
            
            return data_response.json()
    
    async def get_current_weather(self, station_id: str = None) -> Dict:
        """Get current weather conditions for Valencia area"""
        station = station_id or self.valencia_station
        endpoint = f"/observacion/convencional/datos/estacion/{station}"
        
        try:
            data = await self._make_request(endpoint)
            if not data:
                return self._simulate_weather_data()
            
            latest = data[0] if isinstance(data, list) else data
            
            return {
                "station": station,
                "datetime": latest.get("fint", datetime.now().isoformat()),
                "temperature": self._safe_float(latest.get("ta")),
                "humidity": self._safe_float(latest.get("hr")),
                "precipitation": self._safe_float(latest.get("prec", 0)),
                "wind_speed": self._safe_float(latest.get("vv")),
                "wind_direction": self._safe_float(latest.get("dv")),
                "pressure": self._safe_float(latest.get("pres")),
                "soil_temperature": self._safe_float(latest.get("tss", latest.get("ta", 20))),
                "evapotranspiration_estimate": self._calculate_et0(
                    latest.get("ta", 20), 
                    latest.get("hr", 60), 
                    latest.get("vv", 2)
                )
            }
        except Exception as e:
            print(f"AEMET API error: {e}, using simulated data")
            return self._simulate_weather_data()
    
    async def get_forecast(self, days: int = 7) -> List[Dict]:
        """Get weather forecast for irrigation planning"""
        endpoint = f"/prediccion/especifica/municipio/diaria/46250"  # Valencia city code
        
        try:
            data = await self._make_request(endpoint)
            if not data:
                return self._simulate_forecast_data(days)
            
            forecast_data = data[0] if isinstance(data, list) else data
            daily_forecasts = forecast_data.get("prediccion", {}).get("dia", [])
            
            processed_forecast = []
            for day_data in daily_forecasts[:days]:
                fecha = day_data.get("fecha")
                
                # Extract temperature ranges
                temp_data = day_data.get("temperatura", {})
                temp_max = self._extract_temp_value(temp_data.get("maxima"))
                temp_min = self._extract_temp_value(temp_data.get("minima"))
                temp_avg = (temp_max + temp_min) / 2 if temp_max and temp_min else 20
                
                # Extract precipitation probability
                lluvia = day_data.get("probPrecipitacion", [])
                precip_prob = self._extract_precip_probability(lluvia)
                
                # Extract humidity
                humidity_data = day_data.get("humedadRelativa", {})
                humidity = self._extract_humidity_value(humidity_data)
                
                # Extract wind
                viento = day_data.get("viento", [])
                wind_speed = self._extract_wind_speed(viento)
                
                processed_forecast.append({
                    "date": fecha,
                    "temp_max": temp_max,
                    "temp_min": temp_min,
                    "temp_avg": temp_avg,
                    "precipitation_probability": precip_prob,
                    "humidity": humidity,
                    "wind_speed": wind_speed,
                    "irrigation_need": self._calculate_irrigation_need(
                        temp_avg, humidity, wind_speed, precip_prob
                    ),
                    "et0_estimate": self._calculate_et0(temp_avg, humidity, wind_speed)
                })
            
            return processed_forecast
            
        except Exception as e:
            print(f"AEMET forecast error: {e}, using simulated data")
            return self._simulate_forecast_data(days)
    
    def _safe_float(self, value, default: float = 0.0) -> float:
        """Safely convert value to float"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def _extract_temp_value(self, temp_data) -> Optional[float]:
        """Extract temperature from AEMET complex structure"""
        if isinstance(temp_data, (int, float)):
            return float(temp_data)
        elif isinstance(temp_data, list) and temp_data:
            return self._safe_float(temp_data[0].get("valor") if isinstance(temp_data[0], dict) else temp_data[0])
        elif isinstance(temp_data, dict):
            return self._safe_float(temp_data.get("valor"))
        return None
    
    def _extract_precip_probability(self, lluvia_data) -> float:
        """Extract precipitation probability"""
        if isinstance(lluvia_data, list) and lluvia_data:
            # Take maximum probability for the day
            probs = []
            for item in lluvia_data:
                if isinstance(item, dict) and "value" in item:
                    probs.append(self._safe_float(item["value"]))
                elif isinstance(item, (int, float)):
                    probs.append(self._safe_float(item))
            return max(probs) if probs else 0.0
        return self._safe_float(lluvia_data, 0.0)
    
    def _extract_humidity_value(self, humidity_data) -> float:
        """Extract humidity from complex structure"""
        if isinstance(humidity_data, dict):
            maxima = humidity_data.get("maxima")
            minima = humidity_data.get("minima")
            if maxima and minima:
                max_val = self._extract_temp_value(maxima)
                min_val = self._extract_temp_value(minima)
                return (max_val + min_val) / 2 if max_val and min_val else 60.0
        return 60.0  # Default humidity
    
    def _extract_wind_speed(self, viento_data) -> float:
        """Extract wind speed"""
        if isinstance(viento_data, list) and viento_data:
            for item in viento_data:
                if isinstance(item, dict) and "velocidad" in item:
                    velocidad = item["velocidad"]
                    if isinstance(velocidad, list) and velocidad:
                        return self._safe_float(velocidad[0].get("value") if isinstance(velocidad[0], dict) else velocidad[0], 2.0)
        return 2.0  # Default wind speed
    
    def _calculate_et0(self, temp: float, humidity: float, wind_speed: float) -> float:
        """
        Calculate reference evapotranspiration (ET0) using simplified Penman-Monteith
        Essential for irrigation scheduling
        """
        # Simplified ET0 calculation for irrigation guidance
        # Real implementation would use full Penman-Monteith equation
        delta = 4098 * (0.6108 * pow(2.718, (17.27 * temp) / (temp + 237.3))) / pow(temp + 237.3, 2)
        gamma = 0.665  # Psychrometric constant
        
        # Simplified radiation estimate based on temperature
        radiation = max(0, 15 + 0.5 * temp)  # MJ/m²/day
        
        # Vapor pressure calculations
        es = 0.6108 * pow(2.718, (17.27 * temp) / (temp + 237.3))
        ea = es * humidity / 100
        
        # Simplified ET0 (mm/day)
        et0 = (0.408 * delta * radiation + gamma * 900 / (temp + 273) * wind_speed * (es - ea)) / (delta + gamma * (1 + 0.34 * wind_speed))
        
        return max(0, round(et0, 2))
    
    def _calculate_irrigation_need(self, temp: float, humidity: float, wind_speed: float, precip_prob: float) -> str:
        """Calculate irrigation need based on weather conditions"""
        et0 = self._calculate_et0(temp, humidity, wind_speed)
        
        # Risk factors
        heat_stress = temp > 30
        low_humidity = humidity < 40
        high_wind = wind_speed > 4
        no_rain = precip_prob < 20
        
        if et0 > 6 and heat_stress and low_humidity:
            return "HIGH - Immediate irrigation needed"
        elif et0 > 4 and (heat_stress or low_humidity or high_wind) and no_rain:
            return "MEDIUM - Plan irrigation within 24h"
        elif et0 > 2 and no_rain:
            return "LOW - Monitor and prepare"
        elif precip_prob > 60:
            return "NONE - Rain expected"
        else:
            return "LOW - Normal monitoring"
    
    def _simulate_weather_data(self) -> Dict:
        """🧠 SIMULACIÓN INTELIGENTE - Usa SmartDataSimulator"""
        return smart_simulator.get_current_weather_simulation(self.valencia_station)
    
    def _simulate_forecast_data(self, days: int) -> List[Dict]:
        """🧠 SIMULACIÓN INTELIGENTE - Usa SmartDataSimulator para forecast"""
        return smart_simulator.generate_forecast(days=days)

    async def get_irrigation_intelligence(self, crop_type: str = "arroz") -> Dict:
        """
        Combine current weather + forecast to provide irrigation intelligence
        This is the core competitive advantage feature
        """
        current_weather = await self.get_current_weather()
        forecast = await self.get_forecast(7)
        
        # Crop-specific water requirements (mm/day)
        crop_coefficients = {
            "arroz": {"kc": 1.2, "critical_stages": ["tillering", "flowering"], "flood_irrigation": True},
            "trigo": {"kc": 1.15, "critical_stages": ["grain_filling"], "flood_irrigation": False},
            "maiz": {"kc": 1.2, "critical_stages": ["silking", "grain_filling"], "flood_irrigation": False},
            "tomate": {"kc": 1.1, "critical_stages": ["flowering", "fruit_development"], "flood_irrigation": False},
            "naranja": {"kc": 0.7, "critical_stages": ["flowering", "fruit_set"], "flood_irrigation": False},
            "oliva": {"kc": 0.6, "critical_stages": ["flowering"], "flood_irrigation": False}
        }
        
        crop_info = crop_coefficients.get(crop_type, crop_coefficients["arroz"])
        
        # Calculate water balance
        current_et0 = current_weather["evapotranspiration_estimate"]
        crop_et = current_et0 * crop_info["kc"]
        
        # Analyze forecast for irrigation timing
        total_forecast_precip = sum(day["precipitation_probability"] / 100 * 5 for day in forecast)  # Estimated mm
        total_forecast_et = sum(day["et0_estimate"] * crop_info["kc"] for day in forecast)
        
        water_deficit = total_forecast_et - total_forecast_precip
        
        # Generate recommendations
        recommendations = []
        
        if crop_info["flood_irrigation"]:
            recommendations.append("🌾 Rice requires flooded fields - maintain 5-10cm water level")
        
        if water_deficit > 20:
            recommendations.append(f"⚠️ High water deficit predicted ({water_deficit:.1f}mm) - increase irrigation frequency")
        elif water_deficit > 10:
            recommendations.append(f"📊 Moderate deficit ({water_deficit:.1f}mm) - monitor closely")
        else:
            recommendations.append(f"✅ Water balance adequate ({water_deficit:.1f}mm deficit)")
        
        # Timing recommendations
        high_stress_days = [day for day in forecast if day["irrigation_need"].startswith("HIGH")]
        if high_stress_days:
            recommendations.append(f"🔥 {len(high_stress_days)} high-stress days coming - pre-irrigate now")
        
        rain_days = [day for day in forecast if day["precipitation_probability"] > 70]
        if rain_days:
            recommendations.append(f"🌧️ Rain expected on {len(rain_days)} days - delay irrigation if possible")
        
        return {
            "crop_type": crop_type,
            "current_conditions": current_weather,
            "forecast_summary": {
                "days": len(forecast),
                "avg_temperature": round(sum(day["temp_avg"] for day in forecast) / len(forecast), 1),
                "total_rain_probability": round(sum(day["precipitation_probability"] for day in forecast) / len(forecast), 0),
                "water_deficit_mm": round(water_deficit, 1)
            },
            "crop_requirements": {
                "daily_water_need_mm": round(crop_et, 1),
                "weekly_water_need_mm": round(crop_et * 7, 1),
                "coefficient": crop_info["kc"],
                "critical_stages": crop_info["critical_stages"]
            },
            "recommendations": recommendations,
            "irrigation_schedule": self._generate_irrigation_schedule(forecast, crop_info),
            "competitive_advantage": "🚀 FLORASAT is the ONLY platform combining NASA satellite data + Spanish weather service for precision irrigation!"
        }
    
    def _generate_irrigation_schedule(self, forecast: List[Dict], crop_info: Dict) -> List[Dict]:
        """Generate day-by-day irrigation schedule"""
        schedule = []
        
        for day in forecast:
            date = day["date"]
            need = day["irrigation_need"]
            et0 = day["et0_estimate"]
            precip_prob = day["precipitation_probability"]
            
            if precip_prob > 70:
                action = "SKIP - Rain expected"
                amount_mm = 0
            elif need.startswith("HIGH"):
                action = "IRRIGATE - High priority"
                amount_mm = et0 * crop_info["kc"] * 1.2  # 20% extra for stress
            elif need.startswith("MEDIUM"):
                action = "MONITOR - Prepare irrigation"
                amount_mm = et0 * crop_info["kc"]
            else:
                action = "MONITOR - Normal conditions"
                amount_mm = et0 * crop_info["kc"] * 0.8
            
            schedule.append({
                "date": date,
                "action": action,
                "recommended_amount_mm": round(amount_mm, 1),
                "et0_mm": et0,
                "rain_probability": precip_prob,
                "temperature": day["temp_avg"]
            })
        
        return schedule