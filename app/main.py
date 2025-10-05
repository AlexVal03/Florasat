from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import valencia, hls, phenology, weather, i18n, flowering_risk

app = FastAPI(
    title='FLORASAT Valencia',
    description='NASA Space Apps Challenge 2025 - FLORASAT: Flowering Land Observation via Remote Analysis SATellite (Valencia focus, global-ready)',
    version='0.1.0'
)

app.mount('/static', StaticFiles(directory='app/static'), name='static')

app.include_router(valencia.router, prefix='/api/valencia', tags=['valencia'])
app.include_router(hls.router, prefix='/api/hls', tags=['hls'])
app.include_router(phenology.router, prefix='/api/phenology', tags=['phenology'])
app.include_router(weather.router, prefix='/api/weather', tags=['weather'])
app.include_router(i18n.router, prefix='/api/i18n', tags=['internationalization'])
app.include_router(flowering_risk.router, prefix='/api/flowering-risk', tags=['flowering-risk'])

@app.get('/', response_class=HTMLResponse)
async def root():
    try:
        with open('app/static/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
    except UnicodeDecodeError:
        # Fallback: try with errors='replace'
        with open('app/static/index.html', 'r', encoding='utf-8', errors='replace') as f:
            html = f.read()
    return HTMLResponse(content=html)

@app.get('/map', response_class=HTMLResponse)
async def interactive_map():
    """🌍 Mapa interactivo con timeline para navegación temporal de eventos fenológicos"""
    try:
        with open('app/static/map.html', 'r', encoding='utf-8') as f:
            html = f.read()
    except UnicodeDecodeError:
        with open('app/static/map.html', 'r', encoding='utf-8', errors='replace') as f:
            html = f.read()
    return HTMLResponse(content=html)

@app.get('/map.html', response_class=HTMLResponse)
async def interactive_map_html():
    """🌍 Mapa interactivo - ruta alternativa con .html"""
    return await interactive_map()

@app.get('/valencia-simple', response_class=HTMLResponse)
async def valencia_simple_map():
    """🌸 Mapa simplificado de Valencia para pruebas"""
    try:
        with open('app/static/valencia-simple.html', 'r', encoding='utf-8') as f:
            html = f.read()
    except UnicodeDecodeError:
        with open('app/static/valencia-simple.html', 'r', encoding='utf-8', errors='replace') as f:
            html = f.read()
    return HTMLResponse(content=html)

@app.get('/health')
async def health():
    return {'status': 'ok'}
