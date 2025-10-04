"""
Internationalization (i18n) service for FLORASAT
Supports Spanish and English for NASA Space Apps international presentation
"""
from typing import Dict, Any
from app.core.config import settings

class TranslationService:
    """Provides translation services for FLORASAT interface"""
    
    def __init__(self):
        self.translations = {
            "es": {
                # Main interface
                "app_title": "FLORASAT Dashboard",
                "app_subtitle": "Monitoreo Inteligente de Cultivos | NASA Space Apps 2025 | Valencia → Global",
                "main_description": "¿Qué significa cada cosa?",
                
                # NDVI and data explanations
                "ndvi_explanation": "Índice de Vegetación (0-1). Valores altos = vegetación saludable, bajos = suelo desnudo",
                "region_map_explanation": "Área de Valencia. Rectángulo rojo = zona analizada. Marcadores = eventos de floración detectados",
                "phenology_explanation": "Eventos de floración detectados con fecha pico, duración, amplitud, anomalías",
                "data_source": "Simulación basada en patrones reales de MODIS NDVI. Para datos reales: configurar credenciales NASA Earthdata.",
                
                # Charts and sections
                "ndvi_time_series": "Serie Temporal NDVI",
                "region_map": "Mapa Regional (haz clic para seleccionar zona)",
                "phenology_events": "Eventos Fenológicos Detectados",
                "phenology_description": "Ciclos de crecimiento identificados automáticamente por IA satellite + NASA data",
                
                # Metrics
                "events_detected": "Eventos Detectados",
                "avg_ndvi": "NDVI Promedio",
                "health_status": "Estado de Salud",
                "excellent": "Excelente",
                "good": "Bueno",
                "regular": "Regular",
                "poor": "Pobre",
                
                # Table headers
                "peak_date": "📅 Fecha Pico",
                "start_date": "🌱 Inicio",
                "duration_days": "⏱️ Duración (días)",
                "amplitude": "📈 Amplitud",
                "anomaly": "⚠️ Anomalía",
                "reliability": "✅ Confiabilidad",
                "temperature": "🌡️ Temp",
                "yield": "🚜 Rendimiento",
                
                # Crop management
                "crop_management": "🌱 Gestión Inteligente de Cultivos",
                "crop_management_description": "Selecciona qué cultivo tienes en la zona para obtener recomendaciones personalizadas basadas en datos satelitales",
                "current_crop": "Cultivo actual:",
                "analysis_recommendations": "✨ Análisis y Recomendaciones",
                
                # Crops
                "bare_soil": "🏜️ Suelo desnudo/Sin cultivo",
                "rice": "🌾 Arroz",
                "wheat": "🌾 Trigo",
                "corn": "🌽 Maíz",
                "tomato": "🍅 Tomate",
                "orange": "🍊 Naranja",
                "olive": "🫒 Oliva",
                
                # Weather intelligence
                "weather_intelligence": "🌦️ Inteligencia Meteorológica Multi-Fuente",
                "weather_competitive_advantage": "VENTAJA COMPETITIVA: Combina datos de AEMET + Meteomatics (Partner NASA) + Satélites NASA",
                "weather_data_source": "Fuente de datos meteorológicos:",
                "irrigation_intelligence": "🧠 Inteligencia de Riego",
                "compare_sources": "📊 Comparar Fuentes",
                
                # Weather providers
                "fusion_recommended": "🚀 FUSION (AEMET + Meteomatics) - RECOMENDADO",
                "aemet_spanish": "🇪🇸 AEMET (Servicio Meteorológico Español)",
                "meteomatics_nasa": "🌍 Meteomatics (NASA Space Apps Partner)",
                "auto_selection": "⚡ AUTO (Selección automática)",
                
                # Recommendation sections
                "intelligent_analysis": "💡 Análisis Inteligente para",
                "current_status": "📊 Estado Actual",
                "optimal_season": "🗓️ Temporada Óptima",
                "immediate_recommendations": "✅ Recomendaciones Inmediatas",
                "next_actions": "🎯 Próximas Acciones",
                "risks_monitor": "⚠️ Riesgos a Monitorear",
                "expected_yield": "📈 Rendimiento Esperado",
                
                # Status and alerts
                "loading_weather": "🔄 Obteniendo inteligencia meteorológica multi-fuente...",
                "loading_comparison": "🔄 Comparando proveedores meteorológicos...",
                "error_recommendations": "❌ Error al obtener recomendaciones. Verifica que el servidor esté funcionando.",
                "error_weather": "❌ Error al obtener inteligencia meteorológica:",
                "error_comparison": "❌ Error al comparar proveedores:",
                
                # Weather analysis
                "multi_source_irrigation": "🧠 Inteligencia de Riego Multi-Fuente",
                "fusion_analysis": "🔬 Análisis de Fusión de Datos",
                "data_consistency": "Consistencia:",
                "confidence": "Confianza:",
                "current_conditions": "Condiciones Actuales",
                "humidity": "💧 Humedad",
                "evapotranspiration": "💨 Evapotranspiración",
                "wind": "🌬️ Viento",
                "intelligent_irrigation_recommendations": "💡 Recomendaciones de Riego Inteligente",
                "satellite_correlation": "🛰️ Correlación Satelital (NASA)",
                "current_ndvi": "NDVI Actual:",
                
                # Provider comparison
                "provider_comparison": "📊 Comparación de Proveedores Meteorológicos",
                "providers_available": "Proveedores disponibles:",
                "data_consistency_label": "Consistencia de datos:",
                "recommended": "Recomendado:",
                "temperature_difference": "Diferencia de temperatura:",
                "precipitation": "Precipitación:",
                "accuracy": "Precisión:",
                
                # Language selector
                "language": "Idioma:",
                "spanish": "🇪🇸 Español",
                "english": "🇺🇸 English"
            },
            
            "en": {
                # Main interface
                "app_title": "FLORASAT Dashboard",
                "app_subtitle": "Smart Crop Monitoring | NASA Space Apps 2025 | Valencia → Global",
                "main_description": "What does each thing mean?",
                
                # NDVI and data explanations
                "ndvi_explanation": "Vegetation Index (0-1). High values = healthy vegetation, low = bare soil",
                "region_map_explanation": "Valencia area. Red rectangle = analyzed zone. Markers = detected flowering events",
                "phenology_explanation": "Flowering events detected with peak date, duration, amplitude, anomalies",
                "data_source": "Simulation based on real MODIS NDVI patterns. For real data: configure NASA Earthdata credentials.",
                
                # Charts and sections
                "ndvi_time_series": "NDVI Time Series",
                "region_map": "Region Map (click to select zone)",
                "phenology_events": "Detected Phenological Events",
                "phenology_description": "Growth cycles automatically identified by AI satellite + NASA data",
                
                # Metrics
                "events_detected": "Events Detected",
                "avg_ndvi": "Average NDVI",
                "health_status": "Health Status",
                "excellent": "Excellent",
                "good": "Good",
                "regular": "Fair",
                "poor": "Poor",
                
                # Table headers
                "peak_date": "📅 Peak Date",
                "start_date": "🌱 Start",
                "duration_days": "⏱️ Duration (days)",
                "amplitude": "📈 Amplitude",
                "anomaly": "⚠️ Anomaly",
                "reliability": "✅ Reliability",
                "temperature": "🌡️ Temp",
                "yield": "🚜 Yield",
                
                # Crop management
                "crop_management": "🌱 Smart Crop Management",
                "crop_management_description": "Select your crop type to get personalized recommendations based on satellite data",
                "current_crop": "Current crop:",
                "analysis_recommendations": "✨ Analysis & Recommendations",
                
                # Crops
                "bare_soil": "🏜️ Bare soil/No crop",
                "rice": "🌾 Rice",
                "wheat": "🌾 Wheat",
                "corn": "🌽 Corn",
                "tomato": "🍅 Tomato",
                "orange": "🍊 Orange",
                "olive": "🫒 Olive",
                
                # Weather intelligence
                "weather_intelligence": "🌦️ Multi-Source Weather Intelligence",
                "weather_competitive_advantage": "COMPETITIVE ADVANTAGE: Combines AEMET + Meteomatics (NASA Partner) + NASA Satellites",
                "weather_data_source": "Weather data source:",
                "irrigation_intelligence": "🧠 Irrigation Intelligence",
                "compare_sources": "📊 Compare Sources",
                
                # Weather providers
                "fusion_recommended": "🚀 FUSION (AEMET + Meteomatics) - RECOMMENDED",
                "aemet_spanish": "🇪🇸 AEMET (Spanish Weather Service)",
                "meteomatics_nasa": "🌍 Meteomatics (NASA Space Apps Partner)",
                "auto_selection": "⚡ AUTO (Automatic selection)",
                
                # Recommendation sections
                "intelligent_analysis": "💡 Intelligent Analysis for",
                "current_status": "📊 Current Status",
                "optimal_season": "🗓️ Optimal Season",
                "immediate_recommendations": "✅ Immediate Recommendations",
                "next_actions": "🎯 Next Actions",
                "risks_monitor": "⚠️ Risks to Monitor",
                "expected_yield": "📈 Expected Yield",
                
                # Status and alerts
                "loading_weather": "🔄 Getting multi-source weather intelligence...",
                "loading_comparison": "🔄 Comparing weather providers...",
                "error_recommendations": "❌ Error getting recommendations. Check that server is running.",
                "error_weather": "❌ Error getting weather intelligence:",
                "error_comparison": "❌ Error comparing providers:",
                
                # Weather analysis
                "multi_source_irrigation": "🧠 Multi-Source Irrigation Intelligence",
                "fusion_analysis": "🔬 Data Fusion Analysis",
                "data_consistency": "Consistency:",
                "confidence": "Confidence:",
                "current_conditions": "Current Conditions",
                "humidity": "💧 Humidity",
                "evapotranspiration": "💨 Evapotranspiration",
                "wind": "🌬️ Wind",
                "intelligent_irrigation_recommendations": "💡 Smart Irrigation Recommendations",
                "satellite_correlation": "🛰️ Satellite Correlation (NASA)",
                "current_ndvi": "Current NDVI:",
                
                # Provider comparison
                "provider_comparison": "📊 Weather Provider Comparison",
                "providers_available": "Providers available:",
                "data_consistency_label": "Data consistency:",
                "recommended": "Recommended:",
                "temperature_difference": "Temperature difference:",
                "precipitation": "Precipitation:",
                "accuracy": "Accuracy:",
                
                # Language selector
                "language": "Language:",
                "spanish": "🇪🇸 Español",
                "english": "🇺🇸 English"
            }
        }
        
        self.current_language = settings.DEFAULT_LANGUAGE
    
    def get_text(self, key: str, language: str = None) -> str:
        """Get translated text for a given key"""
        lang = language or self.current_language
        
        if lang not in self.translations:
            lang = settings.DEFAULT_LANGUAGE
        
        return self.translations[lang].get(key, key)
    
    def get_all_translations(self, language: str = None) -> Dict[str, str]:
        """Get all translations for a language"""
        lang = language or self.current_language
        
        if lang not in self.translations:
            lang = settings.DEFAULT_LANGUAGE
        
        return self.translations[lang]
    
    def set_language(self, language: str) -> bool:
        """Set current language"""
        if language in settings.SUPPORTED_LANGUAGES:
            self.current_language = language
            return True
        return False
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages with display names"""
        return {
            "es": "🇪🇸 Español",
            "en": "🇺🇸 English"
        }

# Global translation service instance
translation_service = TranslationService()