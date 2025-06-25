from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from datetime import datetime
import logging

class RankScheduler:
    def __init__(self, rank_tracker, database):
        self.scheduler = AsyncIOScheduler()
        self.tracker = rank_tracker
        self.db = database
        self.running_jobs = set()
        
        # Configura logging
        logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    def start(self):
        """Avvia lo scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("Scheduler avviato")
    
    def stop(self):
        """Ferma lo scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Scheduler fermato")
    
    def schedule_project(self, project_id: int, hours: int = 24):
        """Schedula il controllo di un progetto"""
        job_id = f"project_{project_id}"
        
        # Rimuovi job esistente se presente
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # Aggiungi nuovo job
        self.scheduler.add_job(
            func=self._run_project_check,
            trigger=IntervalTrigger(hours=hours),
            args=[project_id],
            id=job_id,
            name=f"Rank Check Project {project_id}",
            replace_existing=True,
            max_instances=1  # Evita sovrapposizioni
        )
        
        print(f"Progetto {project_id} schedulato ogni {hours} ore")
    
    def remove_project_schedule(self, project_id: int):
        """Rimuove lo schedule di un progetto"""
        job_id = f"project_{project_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            print(f"Schedule rimosso per progetto {project_id}")
    
    async def _run_project_check(self, project_id: int):
        """Esegue il controllo di un progetto"""
        if project_id in self.running_jobs:
            print(f"Progetto {project_id} già in esecuzione, skip...")
            return
        
        try:
            self.running_jobs.add(project_id)
            print(f"Inizio check automatico progetto {project_id} - {datetime.now()}")
            
            # Recupera dati progetto
            project = self.db.get_project(project_id)
            if not project or not project['active']:
                print(f"Progetto {project_id} non trovato o inattivo")
                return
            
            keywords = self.db.get_keywords(project_id)
            if not keywords:
                print(f"Nessuna keyword trovata per progetto {project_id}")
                return
            
            keyword_list = [kw['keyword'] for kw in keywords]
            
            print(f"Controllo {len(keyword_list)} keywords per {project['domain']}")
            
            # Esegui il controllo con il nuovo sistema modulare
            localization_config = self.db.get_project_localization(project_id)
            tracking_config = self.db.get_project_tracking_config(project_id)
            
            results = await self.tracker.check_rankings_complete(
                domain=project['domain'], 
                keywords=keyword_list, 
                localization_config=localization_config,
                tracking_config=tracking_config
            )
            
            # Salva risultati modulari
            self._save_modular_results(project_id, results)
            
            # Statistiche
            found_count, avg_position = self._calculate_stats(results)
            
            print(f"✅ Check completato per progetto {project_id}:")
            print(f"  - Keywords trovate: {found_count}/{len(keyword_list)}")
            print(f"  - Posizione media: {avg_position:.1f}")
            print(f"  - Tracking mode: {tracking_config.get('tracking_mode', 'ORGANIC_ONLY')}")
            
        except Exception as e:
            print(f"Errore durante check progetto {project_id}: {str(e)}")
            
        finally:
            self.running_jobs.discard(project_id)
    
    def _save_modular_results(self, project_id: int, results: dict):
        """Salva i risultati modulari nel database"""
        for keyword, result_data in results.items():
            if 'error' in result_data:
                continue
            
            # Salva risultati organici nel vecchio formato per compatibilità
            organic_position = None
            target_positions = result_data.get('target_positions', {})
            if 'organic' in target_positions:
                organic_position = target_positions['organic'].get('position')
            
            # Salva nel vecchio formato
            self.db.save_result(project_id, keyword, organic_position)
            
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
                self.db.save_serp_features_batch(project_id, keyword, all_features)
        
        # Aggiorna last_check del progetto
        try:
            self.db.save_results_batch(project_id, {})  # Trigger per aggiornare last_check
        except:
            pass
    
    def _calculate_stats(self, results: dict) -> tuple:
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
    
    def get_scheduled_jobs(self):
        """Restituisce la lista dei job schedulati"""
        return [
            {
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            for job in self.scheduler.get_jobs()
        ]
    
    def load_existing_schedules(self):
        """Carica gli schedule esistenti dal database all'avvio"""
        projects = self.db.get_all_projects()
        for project in projects:
            if project['active']:
                self.schedule_project(project['id'], project['schedule_hours'])
        
        print(f"Caricati {len(projects)} schedule dal database")