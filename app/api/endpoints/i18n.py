"""
Internationalization API endpoints for FLORASAT
Provides translation services for multi-language support
"""
from fastapi import APIRouter, Query
from typing import Dict
from app.services.translation_service import translation_service
from app.core.config import settings

router = APIRouter()

@router.get('/languages')
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "status": "success",
        "supported_languages": settings.SUPPORTED_LANGUAGES,
        "default_language": settings.DEFAULT_LANGUAGE,
        "language_names": translation_service.get_supported_languages(),
        "current_language": translation_service.current_language
    }

@router.get('/translations')
async def get_translations(
    language: str = Query(None, description="Language code (es, en)")
):
    """Get all translations for a specific language"""
    if language and language not in settings.SUPPORTED_LANGUAGES:
        return {
            "status": "error",
            "message": f"Unsupported language: {language}. Supported: {settings.SUPPORTED_LANGUAGES}"
        }
    
    translations = translation_service.get_all_translations(language)
    
    return {
        "status": "success",
        "language": language or translation_service.current_language,
        "translations": translations,
        "nasa_space_apps_note": "FLORASAT supports international presentation for NASA Space Apps 2025"
    }

@router.post('/set-language')
async def set_language(language: str = Query(..., description="Language code to set")):
    """Set the current language"""
    success = translation_service.set_language(language)
    
    if success:
        return {
            "status": "success",
            "message": f"Language set to {language}",
            "current_language": translation_service.current_language,
            "international_ready": True
        }
    else:
        return {
            "status": "error",
            "message": f"Unsupported language: {language}",
            "supported_languages": settings.SUPPORTED_LANGUAGES
        }

@router.get('/translate')
async def translate_text(
    key: str = Query(..., description="Translation key"),
    language: str = Query(None, description="Target language")
):
    """Translate a specific text key"""
    translated_text = translation_service.get_text(key, language)
    
    return {
        "status": "success",
        "key": key,
        "language": language or translation_service.current_language,
        "translated_text": translated_text,
        "fallback_used": translated_text == key  # True if no translation found
    }