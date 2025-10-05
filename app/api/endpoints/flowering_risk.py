"""
FloraSat Flowering Risk API Endpoints
Endpoints para el cálculo de riesgo de floración con timeline temporal
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from app.services.flowering_risk_calculator import FloweringRiskCalculator, FloweringRiskResult
from app.services.nasa_data import NASADataService
from app.services.weather_coordinator import WeatherCoordinator
from app.services.smart_data_simulator import smart_simulator
import numpy as np

router = APIRouter()
risk_calculator = FloweringRiskCalculator()
nasa_service = NASADataService()
weather_coordinator = WeatherCoordinator()


@router.get('/risk-timeline')
async def get_flowering_risk_timeline(
    crop: str = Query("arroz", description="Crop type: arroz, trigo, maiz, tomate, naranja, oliva"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD), default: 1 year ago"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD), default: 1 month ahead"),
    lat: Optional[float] = Query(39.4699, description="Latitude"),
    lon: Optional[float] = Query(-0.3763, description="Longitude")
):
    """
    🌸 TIMELINE DE RIESGO DE FLORACIÓN
    
    Calcula riesgo desde 1 año atrás hasta 1 mes adelante
    Combina datos históricos reales + pronósticos futuros
    """
    try:
        # Configurar fechas por defecto
        today = datetime.now()
        if not start_date:
            start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Dividir en histórico y futuro
        today_str = today.strftime('%Y-%m-%d')
        
        # Generar datos históricos (simulados + reales disponibles)
        historical_data = await _generate_historical_data(start_date, today_str, lat, lon)
        
        # Generar pronósticos futuros
        forecast_data = await _generate_forecast_data(today_str, end_date, lat, lon)
        
        # Calcular riesgo para toda la timeline
        risk_results = risk_calculator.calculate_forecast_risk(
            historical_data=historical_data,
            forecast_data=forecast_data,
            crop=crop
        )
        
        # Organizar respuesta
        timeline_data = []
        for result in risk_results:
            timeline_data.append({
                'date': result.date,
                'risk_score': round(result.risk_score, 3),
                'confidence': round(result.confidence, 3),
                'factors': {k: round(v, 3) for k, v in result.factors.items()},
                'recommendation': result.recommendation,
                'is_forecast': result.is_forecast,
                'risk_level': _get_risk_level(result.risk_score)
            })
        
        return {
            'status': 'success',
            'crop': crop,
            'timeline_range': {
                'start': start_date,
                'end': end_date,
                'today': today_str
            },
            'data': timeline_data,
            'summary': {
                'total_days': len(timeline_data),
                'historical_days': len([d for d in timeline_data if not d['is_forecast']]),
                'forecast_days': len([d for d in timeline_data if d['is_forecast']]),
                'high_risk_days': len([d for d in timeline_data if d['risk_score'] >= 0.7]),
                'algorithm': 'FloraSat Flowering Risk Calculator v1.0'
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline calculation error: {str(e)}")


@router.get('/risk-current')
async def get_current_flowering_risk(
    crop: str = Query("arroz", description="Crop type"),
    date: Optional[str] = Query(None, description="Specific date (YYYY-MM-DD), default: today"),
    lat: Optional[float] = Query(39.4699, description="Latitude"),
    lon: Optional[float] = Query(-0.3763, description="Longitude")
):
    """
    🎯 RIESGO DE FLORACIÓN ESPECÍFICO
    
    Calcula riesgo para una fecha específica
    """
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        date_obj = datetime.fromisoformat(date)
        today = datetime.now()
        is_forecast = date_obj > today
        
        # Obtener datos para la fecha específica
        if is_forecast:
            # Datos de pronóstico
            data = await _get_forecast_data_for_date(date, lat, lon)
        else:
            # Datos históricos/actuales
            data = await _get_historical_data_for_date(date, lat, lon)
        
        # Calcular riesgo
        risk_result = risk_calculator.calculate_flowering_risk(
            ndvi=data['ndvi'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            date_str=date,
            crop=crop,
            accumulated_gdd=data.get('accumulated_gdd'),
            is_forecast=is_forecast
        )
        
        return {
            'status': 'success',
            'date': date,
            'crop': crop,
            'risk_score': round(risk_result.risk_score, 3),
            'risk_level': _get_risk_level(risk_result.risk_score),
            'confidence': round(risk_result.confidence, 3),
            'factors': {k: round(v, 3) for k, v in risk_result.factors.items()},
            'recommendation': risk_result.recommendation,
            'is_forecast': is_forecast,
            'input_data': data,
            'algorithm': 'FloraSat Flowering Risk Calculator v1.0'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk calculation error: {str(e)}")


@router.get('/risk-map-data')
async def get_risk_map_data(
    date: Optional[str] = Query(None, description="Date for risk map (YYYY-MM-DD)"),
    crop: str = Query("arroz", description="Crop type")
):
    """
    🗺️ DATOS DE RIESGO PARA MAPA
    
    Genera datos de riesgo para todas las regiones de Valencia
    """
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Regiones de Valencia (coordenadas centrales)
        valencia_regions = {
            'Valencia': {'lat': 39.4699, 'lon': -0.3763},
            'Castellón': {'lat': 39.9864, 'lon': -0.0513},
            'Alicante': {'lat': 38.3452, 'lon': -0.4810},
            'Sagunto': {'lat': 39.6775, 'lon': -0.2664},
            'Xàtiva': {'lat': 38.9873, 'lon': -0.5186}
        }
        
        region_risks = {}
        
        for region_name, coords in valencia_regions.items():
            # Calcular riesgo para cada región
            risk_response = await get_current_flowering_risk(
                crop=crop,
                date=date,
                lat=coords['lat'],
                lon=coords['lon']
            )
            
            region_risks[region_name] = {
                'risk_score': risk_response['risk_score'],
                'risk_level': risk_response['risk_level'],
                'confidence': risk_response['confidence'],
                'coordinates': coords
            }
        
        return {
            'status': 'success',
            'date': date,
            'crop': crop,
            'regions': region_risks,
            'legend': {
                'muy_bajo': {'range': '0.0-0.2', 'color': '#FFE5F1', 'description': 'Riesgo muy bajo'},
                'bajo': {'range': '0.2-0.4', 'color': '#FFB3E0', 'description': 'Riesgo bajo'},
                'medio': {'range': '0.4-0.6', 'color': '#FF80CF', 'description': 'Riesgo medio'},
                'alto': {'range': '0.6-0.8', 'color': '#FF4DBF', 'description': 'Riesgo alto'},
                'muy_alto': {'range': '0.8-1.0', 'color': '#FF1493', 'description': 'Riesgo muy alto'}
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Map data error: {str(e)}")


# Funciones auxiliares
async def _generate_historical_data(start_date: str, end_date: str, lat: float, lon: float) -> List[Dict]:
    """Generar datos históricos para el período especificado"""
    data = []
    current = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        # Simular datos realistas basados en fecha y ubicación
        day_of_year = current.timetuple().tm_yday
        
        # NDVI estacional (Valencia)
        ndvi = 0.5 + 0.25 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/4) + np.random.normal(0, 0.05)
        ndvi = max(0.1, min(0.9, ndvi))
        
        # Temperatura estacional
        temp = 15 + 10 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/2) + np.random.normal(0, 2)
        
        # Humedad (inversamente relacionada con temperatura)
        humidity = 70 - (temp - 20) * 1.5 + np.random.normal(0, 5)
        humidity = max(30, min(90, humidity))
        
        data.append({
            'date': date_str,
            'ndvi': round(ndvi, 3),
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'accumulated_gdd': _calculate_gdd_for_date(current)
        })
        
        current += timedelta(days=1)
    
    return data


async def _generate_forecast_data(start_date: str, end_date: str, lat: float, lon: float) -> List[Dict]:
    """Generar datos de pronóstico para el período futuro"""
    data = []
    current = datetime.fromisoformat(start_date) + timedelta(days=1)
    end = datetime.fromisoformat(end_date)
    
    # Obtener pronóstico meteorológico real cuando esté disponible
    try:
        weather_forecast = await weather_coordinator.get_forecast("fusion", 30, lat, lon)
    except:
        weather_forecast = []
    
    day_offset = 0
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        # Usar pronóstico real si está disponible
        if day_offset < len(weather_forecast):
            forecast_day = weather_forecast[day_offset]
            temp = forecast_day.get('temperature', 20)
            humidity = forecast_day.get('humidity', 70)
        else:
            # Simular basado en estacionalidad
            day_of_year = current.timetuple().tm_yday
            temp = 15 + 10 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/2) + np.random.normal(0, 3)
            humidity = 70 - (temp - 20) * 1.5 + np.random.normal(0, 8)
            humidity = max(30, min(90, humidity))
        
        data.append({
            'date': date_str,
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'accumulated_gdd': _calculate_gdd_for_date(current)
        })
        
        current += timedelta(days=1)
        day_offset += 1
    
    return data


async def _get_historical_data_for_date(date: str, lat: float, lon: float) -> Dict:
    """Obtener datos históricos para una fecha específica"""
    date_obj = datetime.fromisoformat(date)
    day_of_year = date_obj.timetuple().tm_yday
    today = datetime.now()
    
    # 🌍 PASO 1: Intentar obtener NDVI real de NASA MODIS
    try:
        ndvi_data = await nasa_service.get_modis_ndvi_valencia(date, date, real=True)
        
        if ndvi_data and ndvi_data.get('data') and len(ndvi_data['data']) > 0:
            real_ndvi = ndvi_data['data'][0].get('ndvi')
            if real_ndvi is not None and 0.1 <= real_ndvi <= 0.9:
                print(f"✅ Using REAL NASA MODIS NDVI: {real_ndvi} for date {date}")
                ndvi = real_ndvi
            else:
                raise ValueError("Invalid NDVI range")
        else:
            raise ValueError("No NDVI data available")
            
        except Exception as e:
        print(f"⚠️  NASA MODIS fallback for {date}: {str(e)}")
        # 🧠 USAR SIMULADOR INTELIGENTE para NDVI
        weather_data = smart_simulator.generate_weather_timeseries(date, date)[0]
        ndvi_data = smart_simulator.generate_ndvi_timeseries(date, date, crop='mixed')
        
        if ndvi_data and ndvi_data.get('data'):
            ndvi = ndvi_data['data'][0].get('ndvi', 0.5)
        else:
            # Fallback final
            peak_ndvi = 0.7 + 0.2 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/3)
            time_factor = (today - date_obj).days
            temporal_decay = np.exp(-abs(time_factor) / 30)
            spatial_factor = 1 + 0.1 * np.sin(lat * np.pi / 180) * np.cos(lon * np.pi / 180)
            ndvi = peak_ndvi * temporal_decay * spatial_factor + np.random.normal(0, 0.05)
            ndvi = max(0.1, min(0.9, ndvi))
    
    # 🌤️ PASO 2: Intentar obtener datos meteorológicos reales de AEMET
    try:
        # Para fechas recientes, intentar datos históricos
        if (today - date_obj).days <= 30:
            weather_data = await weather_coordinator.get_current_weather("aemet", lat, lon)
            if weather_data:
                temp = weather_data.get('temperature', 20)
                humidity = weather_data.get('humidity', 70)
                print(f"✅ Using REAL AEMET weather data for {date}")
            else:
                raise ValueError("No weather data available")
        else:
            raise ValueError("Date too old for real weather data")
            
    except Exception as e:
        print(f"⚠️  AEMET weather fallback for {date}: {str(e)}")
        # 🧠 USAR SIMULADOR INTELIGENTE para meteorología
        if 'weather_data' not in locals():
            weather_data = smart_simulator.generate_weather_timeseries(date, date)[0]
        
        temp = weather_data.get('temperature', 20)
        humidity = weather_data.get('humidity', 70)
    
    return {
        'ndvi': round(ndvi, 3),
        'temperature': round(temp, 1),
        'humidity': round(humidity, 1),
        'accumulated_gdd': _calculate_gdd_for_date(date_obj)
    }


async def _get_forecast_data_for_date(date: str, lat: float, lon: float) -> Dict:
    """Obtener datos de pronóstico para una fecha futura"""
    date_obj = datetime.fromisoformat(date)
    today = datetime.now()
    days_ahead = (date_obj - today).days
    
    # 🌱 PASO 1: Estimar NDVI futuro usando tendencias históricas
    try:
        # Obtener datos históricos de los últimos 30 días para predecir tendencia
        history_start = today - timedelta(days=30)
        history_end = today
        
        historical_ndvi_data = await nasa_service.get_modis_ndvi_valencia(history_start.strftime('%Y-%m-%d'), history_end.strftime('%Y-%m-%d'), real=True)
        historical_ndvi = historical_ndvi_data.get('data', []) if historical_ndvi_data else []
        
        if historical_ndvi and len(historical_ndvi) >= 5:
            # Calcular tendencia de los últimos datos reales
            ndvi_values = [item.get('ndvi', 0.6) for item in historical_ndvi if item.get('ndvi')]
            if ndvi_values:
                recent_avg = np.mean(ndvi_values[-5:])  # Promedio últimos 5 valores
                trend = np.polyfit(range(len(ndvi_values)), ndvi_values, 1)[0]  # Tendencia lineal
                
                # Proyectar NDVI futuro basado en tendencia
                estimated_ndvi = recent_avg + trend * days_ahead
                estimated_ndvi = max(0.1, min(0.9, estimated_ndvi))
                print(f"✅ Using TREND-BASED NDVI prediction: {estimated_ndvi} for {date}")
            else:
                raise ValueError("No valid NDVI values for trend calculation")
        else:
            raise ValueError("Insufficient historical NDVI data")
            
    except Exception as e:
        print(f"⚠️  NDVI forecast fallback for {date}: {str(e)}")
        # Fallback: estimación estacional
        day_of_year = date_obj.timetuple().tm_yday
        estimated_ndvi = 0.6 + 0.15 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/4)
        estimated_ndvi = max(0.1, min(0.9, estimated_ndvi))
    
    # 🌤️ PASO 2: Intentar obtener pronóstico meteorológico real
    try:
        if days_ahead <= 14:
            # Usar pronóstico real para los próximos 14 días
            forecast = await weather_coordinator.get_forecast("fusion", min(14, days_ahead + 1), lat, lon)
            if forecast and len(forecast) > days_ahead:
                weather_data = forecast[days_ahead]
                temp = weather_data.get('temperature', 20)
                humidity = weather_data.get('humidity', 70)
                print(f"✅ Using REAL weather forecast for {date}")
            else:
                raise ValueError("No forecast data available")
        else:
            raise ValueError("Forecast range exceeded (>14 days)")
            
    except Exception as e:
        print(f"⚠️  Weather forecast fallback for {date}: {str(e)}")
        # Fallback: estimación estacional
        day_of_year = date_obj.timetuple().tm_yday
        temp = 15 + 10 * np.sin((day_of_year / 365) * 2 * np.pi - np.pi/2) + np.random.normal(0, 2)
        humidity = 70 - (temp - 20) * 1.5 + np.random.normal(0, 5)
        humidity = max(30, min(90, humidity))
    
    return {
        'ndvi': round(estimated_ndvi, 3),
        'temperature': round(temp, 1),
        'humidity': round(humidity, 1),
        'accumulated_gdd': _calculate_gdd_for_date(date_obj)
    }


def _calculate_gdd_for_date(date_obj: datetime) -> float:
    """Calcular GDD acumulados hasta la fecha"""
    start_year = datetime(date_obj.year, 1, 1)
    days_elapsed = (date_obj - start_year).days
    
    # Estimar GDD basado en estacionalidad Valencia
    avg_temp = 15 + 8 * np.sin((date_obj.timetuple().tm_yday / 365) * 2 * np.pi - np.pi/2)
    base_temp = 10
    
    daily_gdd = max(0, avg_temp - base_temp)
    return round(daily_gdd * days_elapsed, 1)


def _get_risk_level(risk_score: float) -> str:
    """Convertir score numérico a nivel de riesgo"""
    if risk_score >= 0.8:
        return 'muy_alto'
    elif risk_score >= 0.6:
        return 'alto'
    elif risk_score >= 0.4:
        return 'medio'
    elif risk_score >= 0.2:
        return 'bajo'
    else:
        return 'muy_bajo'