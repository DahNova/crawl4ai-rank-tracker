from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from pathlib import Path
import json
from datetime import datetime
import asyncio

from rank_tracker import RankTracker
from database import Database
from scheduler import RankScheduler

# Inizializza componenti
db = Database()
tracker = RankTracker()
scheduler = RankScheduler(tracker, db)

def filter_target_domain_results(serp_results: dict, target_domain: str) -> dict:
    """Filtra i risultati SERP per mostrare solo quelli del dominio target"""
    # Pulisci il dominio target per il matching
    target_domain_clean = _clean_domain_for_matching(target_domain)
    
    filtered_results = {
        'organic': [],
        'ads': [],
        'featured_snippets': [],
        'local_pack': [],
        'shopping': []
    }
    
    for result_type, results_list in serp_results.items():
        if result_type not in filtered_results:
            continue
            
        for result in results_list:
            result_domain = result.get('domain', '')
            if _domains_match(target_domain_clean, result_domain):
                filtered_results[result_type].append(result)
    
    return filtered_results

def _clean_domain_for_matching(domain: str) -> str:
    """Pulisce il dominio per il matching"""
    if not domain:
        return domain
    
    # Rimuovi protocollo
    clean = domain.replace('https://', '').replace('http://', '')
    # Rimuovi slash finale
    clean = clean.rstrip('/')
    # Rimuovi www se presente
    if clean.startswith('www.'):
        clean = clean[4:]
    
    return clean.lower()

def _domains_match(target_domain: str, result_domain: str) -> bool:
    """Verifica se due domini corrispondono (include subdomini)"""
    if not target_domain or not result_domain:
        return False
    
    # Pulisci entrambi i domini
    clean_target = target_domain.lower().replace('www.', '').strip()
    clean_result = result_domain.lower().replace('www.', '').strip()
    
    # Match esatto
    if clean_target == clean_result:
        return True
    
    # Match root domain (es. shop.example.com vs example.com)
    target_parts = clean_target.split('.')
    result_parts = clean_result.split('.')
    
    if len(target_parts) >= 2 and len(result_parts) >= 2:
        target_root = '.'.join(target_parts[-2:])  # ultimi 2 parti (domain.tld)
        result_root = '.'.join(result_parts[-2:])
        
        # Match solo se i root domain sono identici
        if target_root == result_root:
            return True
    
    # Match subdominio: result è subdomain di target o viceversa
    if clean_result.endswith('.' + clean_target):  # result è subdomain di target
        return True
    if clean_target.endswith('.' + clean_result):  # target è subdomain di result
        return True
    
    return False

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    scheduler.load_existing_schedules()
    print("Applicazione avviata con scheduler attivo")
    yield
    # Shutdown
    scheduler.stop()
    await tracker.close_crawler()
    print("Applicazione chiusa")

app = FastAPI(title="Crawl4AI Rank Tracker", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Crea directory se non esistono
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    projects = db.get_all_projects()
    return templates.TemplateResponse("dashboard.html", {"request": request, "projects": projects})

@app.get("/project/{project_id}")
async def project_detail(request: Request, project_id: int):
    """Pagina dettaglio progetto con risultati SERP modulari"""
    project = db.get_project(project_id)
    keywords = db.get_keywords(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    
    # Ottieni i risultati SERP modulari più recenti
    all_serp_results = db.get_latest_serp_results(project_id)
    
    # Filtra solo risultati del dominio target
    target_domain = project['domain']
    filtered_serp_results = filter_target_domain_results(all_serp_results, target_domain)
    
    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "project": project,
        "keywords": keywords,
        "serp_results": filtered_serp_results
    })

@app.post("/create_project")
async def create_project(
    name: str = Form(...),
    domain: str = Form(...),
    keywords: str = Form(...),
    schedule_hours: int = Form(24),
    country_code: str = Form("IT"),
    language_code: str = Form("it"),
    city_code: str = Form(""),
    content_restriction: bool = Form(True),
    tracking_mode: str = Form("ORGANIC_ONLY"),
    track_ads: bool = Form(False),
    track_snippets: bool = Form(False),
    track_local: bool = Form(False),
    track_shopping: bool = Form(False)
):
    keyword_list = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
    
    project_id = db.create_project(
        name=name,
        domain=domain, 
        schedule_hours=schedule_hours,
        country_code=country_code,
        language_code=language_code,
        city_code=city_code if city_code else None,
        content_restriction=content_restriction,
        tracking_mode=tracking_mode,
        track_ads=track_ads,
        track_snippets=track_snippets,
        track_local=track_local,
        track_shopping=track_shopping
    )
    db.add_keywords(project_id, keyword_list)
    
    # Schedule il tracking
    scheduler.schedule_project(project_id, schedule_hours)
    
    return {"status": "success", "project_id": project_id}

@app.post("/run_check/{project_id}")
async def run_check(project_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_rank_check, project_id)
    return {"status": "started"}

async def run_rank_check(project_id: int):
    """Esegue check manuale con il nuovo sistema modulare"""
    project = db.get_project(project_id)
    keywords = db.get_keywords(project_id)
    
    if not project or not keywords:
        print(f"❌ Progetto {project_id} non trovato o senza keywords")
        return
    
    print(f"🚀 Avvio check manuale per progetto {project_id}: {project['name']}")
    
    # Configurazioni per il nuovo sistema
    localization_config = db.get_project_localization(project_id)
    tracking_config = db.get_project_tracking_config(project_id)
    keyword_list = [kw['keyword'] for kw in keywords]
    
    try:
        # Usa il nuovo metodo modulare
        results = await tracker.check_rankings_complete(
            domain=project['domain'],
            keywords=keyword_list,
            localization_config=localization_config,
            tracking_config=tracking_config
        )
        
        # Salva risultati usando la stessa logica dello scheduler
        save_modular_results(project_id, results)
        
        # Calcola statistiche
        found_count, avg_position = calculate_stats(results)
        
        print(f"✅ Check manuale completato per progetto {project_id}")
        print(f"   Keywords trovate: {found_count}/{len(keyword_list)}")
        print(f"   Posizione media: {avg_position:.1f}")
        
    except Exception as e:
        print(f"❌ Errore durante check manuale progetto {project_id}: {str(e)}")

def save_modular_results(project_id: int, results: dict):
    """Salva i risultati modulari nel database (condiviso con scheduler)"""
    for keyword, result_data in results.items():
        if 'error' in result_data:
            continue
        
        # Salva risultati organici nel vecchio formato per compatibilità
        organic_position = None
        target_positions = result_data.get('target_positions', {})
        if 'organic' in target_positions:
            organic_position = target_positions['organic'].get('position')
        
        # Salva nel vecchio formato
        db.save_result(project_id, keyword, organic_position)
        
        # Salva tutte le SERP features
        all_features = []
        for result_type, results_list in result_data.items():
            if result_type in ['metadata', 'target_positions']:
                continue
            
            if isinstance(results_list, list):
                for result in results_list:
                    all_features.append({
                        'result_type': result_type,
                        'position': result.get('position'),
                        'domain': result.get('domain'),
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'snippet': result.get('snippet')
                    })
        
        if all_features:
            db.save_serp_features_batch(project_id, keyword, all_features)

def calculate_stats(results: dict) -> tuple:
    """Calcola statistiche dai risultati modulari"""
    found_count = 0
    total_position = 0
    
    for keyword, result_data in results.items():
        if 'error' in result_data:
            continue
        
        target_positions = result_data.get('target_positions', {})
        if 'organic' in target_positions:
            organic_pos = target_positions['organic'].get('position')
            if organic_pos:
                found_count += 1
                total_position += organic_pos
    
    avg_position = total_position / max(found_count, 1)
    return found_count, avg_position

@app.get("/api/results/{project_id}")
async def get_results(project_id: int, days: int = 30):
    results = db.get_results_history(project_id, days)
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)