from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api.endpoints import valencia, hls, phenology, weather, i18n

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

@app.get('/health')
async def health():
    return {'status': 'ok'}
