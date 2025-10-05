from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, timedelta
from app.services.nasa_data import NASADataService
from app.services.phenology_advanced import AdvancedPhenology
from app.models.bloom_models import PhenologyAnalysis, BloomEvent, AnomalyAlert, CropRecommendation
import numpy as np

router = APIRouter()
nasa_service = NASADataService()
adv = AdvancedPhenology()

@router.get('/analyze-enhanced', response_model=PhenologyAnalysis)
async def phenology_analyze_enhanced(
    bbox: Optional[str] = Query(None, description='lon_min,lat_min,lon_max,lat_max'),
    years: Optional[str] = Query(None, description='Comma-separated years e.g. 2023,2024,2025'),
    product: str = Query('MODIS'),
    species: str = Query('arroz', description='Crop species for phenology thresholds'),
    region: str = Query('valencia', description='Region preset or custom')
):
    """
    🚀 NUEVA FUNCIONALIDAD: Análisis fenológico enriquecido con datos climáticos
    Combina NDVI satelital + temperatura histórica + predicción de rendimiento
    """
    end = datetime.now()
    if years:
        year_list = [int(y.strip()) for y in years.split(',') if y.strip()]
    else:
        year_list = [end.year]

    # Parse bbox
    if bbox:
        bbox_list = [float(x) for x in bbox.split(',')]
    elif region == 'valencia':
        bbox_list = [-0.6, 39.2, -0.1, 39.7]  # Default Valencia
    else:
        bbox_list = [-0.6, 39.2, -0.1, 39.7]  # Fallback

    # Coordenadas para datos climáticos
    center_lat = (bbox_list[1] + bbox_list[3]) / 2
    center_lon = (bbox_list[0] + bbox_list[2]) / 2

    series_all = []
    peak_doys_hist = []

    for y in year_list:
        yr_start = datetime(y, 1, 1).strftime('%Y-%m-%d')
        yr_end = datetime(y, 12, 31).strftime('%Y-%m-%d')
        # For now, still using Valencia simulation - in future, use bbox for real data
        data = await nasa_service.get_modis_ndvi_valencia(yr_start, yr_end)
        for point in data['data']:
            series_all.append({'date': point['date'], 'value': point['ndvi'], 'year': y})
        peak_doys_hist.append(max(
            ((datetime.fromisoformat(p['date']).timetuple().tm_yday, p['ndvi']) for p in data['data']),
            key=lambda t: t[1]
        )[0])

    latest_year = max(year_list)
    series_latest = [s for s in series_all if s['year'] == latest_year]
    dates = [s['date'] for s in series_latest]
    values = [s['value'] for s in series_latest]

    # 🌡️ NUEVA FUNCIONALIDAD: Análisis enriquecido con clima
    try:
        events_enhanced = await adv.analyze_with_weather_data(
            dates, values, lat=center_lat, lon=center_lon
        )
        
        # Convertir a BloomEvent con campos adicionales
        events = []
        for e in events_enhanced:
            # Datos básicos del evento
            bloom_event = BloomEvent(**{k: v for k, v in e.items() 
                                      if k in ['peak_date', 'onset_date', 'duration_days', 
                                              'amplitude', 'reliability', 'anomaly_days', 
                                              'peak_value', 'baseline', 'supporting_peaks']})
            
            # Añadir datos climáticos como atributos adicionales
            if 'temperature_data' in e:
                bloom_event.temperature_data = e['temperature_data']
            if 'yield_prediction' in e:
                bloom_event.yield_prediction = e['yield_prediction']
            if 'weather_impact' in e:
                bloom_event.weather_impact = e['weather_impact']
                
            events.append(bloom_event)
            
    except Exception as ex:
        # Fallback al análisis básico si falla el enriquecido
        events_raw = adv.detect(dates, values, historic_peaks=peak_doys_hist[:-1] if len(peak_doys_hist) > 1 else None)
        events = [BloomEvent(**e) for e in events_raw]
        for event in events:
            event.temperature_data = {'avg_temp': 'N/A', 'error': str(ex)}
            event.yield_prediction = {'estimated_yield': 'N/A', 'error': str(ex)}

    return PhenologyAnalysis(
        region=region,
        bbox=bbox_list,
        product=product,
        years=year_list,
        events=events,
        series=series_all,
        notes=f'🚀 Análisis fenológico enriquecido para {species} en {region}. NDVI + Temperatura + Predicción de rendimiento. NASA Space Apps 2025!'
    )

@router.get('/analyze', response_model=PhenologyAnalysis)
async def phenology_analyze(
    bbox: Optional[str] = Query(None, description='lon_min,lat_min,lon_max,lat_max'),
    years: Optional[str] = Query(None, description='Comma-separated years e.g. 2023,2024,2025'),
    product: str = Query('MODIS'),
    species: str = Query('arroz', description='Crop species for phenology thresholds'),
    region: str = Query('valencia', description='Region preset or custom')
):
    end = datetime.now()
    if years:
        year_list = [int(y.strip()) for y in years.split(',') if y.strip()]
    else:
        year_list = [end.year]

    # Parse bbox
    if bbox:
        bbox_list = [float(x) for x in bbox.split(',')]
    elif region == 'valencia':
        bbox_list = [-0.6, 39.2, -0.1, 39.7]  # Default Valencia
    else:
        bbox_list = [-0.6, 39.2, -0.1, 39.7]  # Fallback

    series_all = []
    peak_doys_hist = []

    for y in year_list:
        yr_start = datetime(y, 1, 1).strftime('%Y-%m-%d')
        yr_end = datetime(y, 12, 31).strftime('%Y-%m-%d')
        # For now, still using Valencia simulation - in future, use bbox for real data
        data = await nasa_service.get_modis_ndvi_valencia(yr_start, yr_end)
        for point in data['data']:
            series_all.append({'date': point['date'], 'value': point['ndvi'], 'year': y})
        peak_doys_hist.append(max(
            ((datetime.fromisoformat(p['date']).timetuple().tm_yday, p['ndvi']) for p in data['data']),
            key=lambda t: t[1]
        )[0])

    latest_year = max(year_list)
    series_latest = [s for s in series_all if s['year'] == latest_year]
    dates = [s['date'] for s in series_latest]
    values = [s['value'] for s in series_latest]

    # Use species-specific phenology
    # adv.set_species(species)  # TODO: implement species-specific thresholds
    events_raw = adv.detect(dates, values, historic_peaks=peak_doys_hist[:-1] if len(peak_doys_hist) > 1 else None)
    events = [BloomEvent(**e) for e in events_raw]

    return PhenologyAnalysis(
        region=region,
        bbox=bbox_list,
        product=product,
        years=year_list,
        events=events,
        series=series_all,
        notes=f'Prototype phenology for {species} in {region}. Simulated NDVI. Replace with real AppEEARS for production.'
    )

@router.get('/anomalies', response_model=List[AnomalyAlert])
async def detect_anomalies(
    bbox: Optional[str] = Query(None, description='lon_min,lat_min,lon_max,lat_max'),
    years: Optional[str] = Query(None, description='Comma-separated years e.g. 2023,2024,2025'),
    species: str = Query('arroz', description='Crop species for anomaly thresholds'),
    region: str = Query('valencia', description='Region preset or custom')
):
    """Detect anomalies: drought stress, fire risk, unusual vegetation changes"""
    end = datetime.now()
    if years:
        year_list = [int(y.strip()) for y in years.split(',') if y.strip()]
    else:
        year_list = [end.year]

    # Parse bbox
    if bbox:
        bbox_list = [float(x) for x in bbox.split(',')]
    elif region == 'valencia':
        bbox_list = [-0.6, 39.2, -0.1, 39.7]
    else:
        bbox_list = [-0.6, 39.2, -0.1, 39.7]

    alerts = []

    for y in year_list:
        yr_start = datetime(y, 1, 1).strftime('%Y-%m-%d')
        yr_end = datetime(y, 12, 31).strftime('%Y-%m-%d')

        data = await nasa_service.get_modis_ndvi_valencia(yr_start, yr_end)
        series = data['data']

        if len(series) < 10:
            continue

        # Convert to numpy for analysis
        dates = [datetime.fromisoformat(p['date']) for p in series]
        values = np.array([p['ndvi'] for p in series])

        # Calculate rolling statistics
        window = min(10, len(values))
        rolling_mean = np.convolve(values, np.ones(window)/window, mode='valid')
        rolling_std = np.array([np.std(values[max(0, i-window//2):min(len(values), i+window//2)])
                               for i in range(len(values))])

        # Species-specific thresholds
        species_thresholds = {
            'arroz': {'drought': 0.3, 'fire_risk': 0.2, 'stress_drop': 0.15},
            'trigo': {'drought': 0.25, 'fire_risk': 0.18, 'stress_drop': 0.12},
            'maiz': {'drought': 0.35, 'fire_risk': 0.25, 'stress_drop': 0.18}
        }
        thresholds = species_thresholds.get(species, species_thresholds['arroz'])

        # Detect anomalies
        for i, (date, value) in enumerate(zip(dates, values)):
            if i < window // 2:
                continue

            mean_idx = i - window // 2
            if mean_idx >= len(rolling_mean):
                continue

            expected = rolling_mean[mean_idx]
            deviation = abs(value - expected)

            # Drought stress detection
            if value < thresholds['drought'] and deviation > thresholds['stress_drop']:
                alerts.append(AnomalyAlert(
                    date=date.strftime('%Y-%m-%d'),
                    type='drought_stress',
                    severity=round(deviation / expected, 2),
                    description=f'NDVI {value:.2f} below drought threshold {thresholds["drought"]}',
                    location=f'{region} ({bbox_list[0]:.2f}, {bbox_list[1]:.2f})',
                    recommendation='Increase irrigation, monitor soil moisture'
                ))

            # Fire risk detection (sudden drops in summer)
            elif (date.month in [6, 7, 8] and
                  value < thresholds['fire_risk'] and
                  deviation > thresholds['stress_drop'] * 1.5):
                alerts.append(AnomalyAlert(
                    date=date.strftime('%Y-%m-%d'),
                    type='fire_risk',
                    severity=round(deviation / expected, 2),
                    description=f'Sudden NDVI drop {value:.2f} in summer - potential fire/incendio',
                    location=f'{region} ({bbox_list[0]:.2f}, {bbox_list[1]:.2f})',
                    recommendation='Monitor fire weather indices, prepare emergency response'
                ))

            # Unusual vegetation changes
            elif deviation > rolling_std[i] * 3:  # 3-sigma rule
                alerts.append(AnomalyAlert(
                    date=date.strftime('%Y-%m-%d'),
                    type='vegetation_anomaly',
                    severity=round(deviation / expected, 2),
                    description=f'Unusual vegetation change: NDVI {value:.2f} vs expected {expected:.2f}',
                    location=f'{region} ({bbox_list[0]:.2f}, {bbox_list[1]:.2f})',
                    recommendation='Investigate land use changes, pest/disease outbreaks'
                ))

    return alerts

@router.get('/recommendations', response_model=CropRecommendation)
async def get_crop_recommendations(
    crop: str = Query(..., description='Crop type: arroz, trigo, maiz, tomate, naranja, oliva, nada'),
    bbox: Optional[str] = Query(None, description='Bounding box for analysis')
):
    """Get crop management recommendations based on phenology data"""
    current_month = datetime.now().month
    current_season = 'verano' if current_month in [6,7,8] else 'invierno' if current_month in [12,1,2] else 'primavera' if current_month in [3,4,5] else 'otoño'

    # Get recent phenology data for context
    try:
        analysis_response = await phenology_analyze(bbox=bbox, years=[datetime.now().year], species=crop if crop != 'nada' else 'arroz')
        has_recent_events = len(analysis_response.events) > 0
        latest_ndvi = analysis_response.series[-1]['value'] if analysis_response.series else 0.3
    except:
        has_recent_events = False
        latest_ndvi = 0.3

    crop_info = {
        'nada': {
            'current_status': f'Suelo desnudo en {current_season}. NDVI actual: {latest_ndvi:.2f}',
            'recommendations': [
                'Analizar suelo antes de plantar',
                'Considerar rotación de cultivos',
                'Monitorear condiciones climáticas'
            ],
            'next_actions': 'Evaluar qué cultivar basado en mercado y condiciones',
            'risks': 'Erosión del suelo, pérdida de nutrientes',
            'optimal_planting_season': 'Depende del cultivo elegido',
            'expected_yield': 'N/A - suelo sin cultivar'
        },
        'arroz': {
            'current_status': f'Arroz en temporada de {current_season}. NDVI: {latest_ndvi:.2f}. Eventos recientes: {"Sí" if has_recent_events else "No"}',
            'recommendations': [
                'Mantener nivel de agua constante (5-10cm)',
                'Monitorear plagas de arroz (nilaparvata lugens)',
                'Aplicar fertilizantes nitrogenados en etapas críticas',
                'Preparar para cosecha si NDVI > 0.7 en verano'
            ],
            'next_actions': 'Cosecha en agosto-septiembre, preparación para siguiente ciclo',
            'risks': 'Estrés hídrico, enfermedades fungosas, competencia con malezas',
            'optimal_planting_season': 'Marzo-Mayo',
            'expected_yield': '6-8 toneladas/hectárea'
        },
        'trigo': {
            'current_status': f'Trigo en temporada de {current_season}. NDVI: {latest_ndvi:.2f}. Eventos recientes: {"Sí" if has_recent_events else "No"}',
            'recommendations': [
                'Monitorear roya del trigo',
                'Aplicar fungicidas preventivos',
                'Optimizar riego en etapas de espigado',
                'Preparar cosecha si NDVI pico detectado'
            ],
            'next_actions': 'Cosecha en junio-julio, siembra de invierno en octubre',
            'risks': 'Royas, mildiu, estrés térmico en floración',
            'optimal_planting_season': 'Octubre-Diciembre (invierno)',
            'expected_yield': '4-6 toneladas/hectárea'
        },
        'maiz': {
            'current_status': f'Maíz en temporada de {current_season}. NDVI: {latest_ndvi:.2f}. Eventos recientes: {"Sí" if has_recent_events else "No"}',
            'recommendations': [
                'Monitorear barrenador del maíz',
                'Aplicar herbicidas selectivos',
                'Aumentar riego en etapa de grano lechoso',
                'Proteger de pájaros durante maduración'
            ],
            'next_actions': 'Cosecha en septiembre-octubre',
            'risks': 'Plagas, enfermedades, competencia con malezas',
            'optimal_planting_season': 'Marzo-Abril',
            'expected_yield': '8-12 toneladas/hectárea'
        },
        'tomate': {
            'current_status': f'Tomate en temporada de {current_season}. NDVI: {latest_ndvi:.2f}. Eventos recientes: {"Sí" if has_recent_events else "No"}',
            'recommendations': [
                'Monitorear mildiu y otras enfermedades',
                'Aplicar tratamientos preventivos',
                'Podar plantas para mejorar aireación',
                'Controlar plagas (mosca blanca, áfidos)'
            ],
            'next_actions': 'Cosecha continua, renovación de plantas',
            'risks': 'Enfermedades fungosas, plagas, calidad del fruto',
            'optimal_planting_season': 'Todo el año (invernaderos)',
            'expected_yield': '80-120 toneladas/hectárea'
        },
        'naranja': {
            'current_status': f'Naranjo en temporada de {current_season}. NDVI: {latest_ndvi:.2f}. Eventos recientes: {"Sí" if has_recent_events else "No"}',
            'recommendations': [
                'Monitorear tristeza de los cítricos',
                'Aplicar tratamientos contra cochinilla',
                'Podar árboles en invierno',
                'Fertilizar con equilibrio NPK'
            ],
            'next_actions': 'Cosecha en invierno, poda de mantenimiento',
            'risks': 'Enfermedades víricas, plagas, estrés hídrico',
            'optimal_planting_season': 'Septiembre-Marzo',
            'expected_yield': '20-40 toneladas/hectárea'
        },
        'oliva': {
            'current_status': f'Olivar en temporada de {current_season}. NDVI: {latest_ndvi:.2f}. Eventos recientes: {"Sí" if has_recent_events else "No"}',
            'recommendations': [
                'Monitorear repilo y otras plagas',
                'Aplicar tratamientos de cobre',
                'Podar en verano para controlar crecimiento',
                'Fertilizar moderadamente'
            ],
            'next_actions': 'Cosecha en noviembre-enero, poda invernal',
            'risks': 'Repilo, tuberculosis, sequía',
            'optimal_planting_season': 'Noviembre-Febrero',
            'expected_yield': '2-5 toneladas/hectárea'
        }
    }

    info = crop_info.get(crop, crop_info['nada'])

    return CropRecommendation(
        crop=crop,
        current_status=info['current_status'],
        recommendations=info['recommendations'],
        next_actions=info['next_actions'],
        risks=info['risks'],
        optimal_planting_season=info['optimal_planting_season'],
        expected_yield=info['expected_yield']
    )
