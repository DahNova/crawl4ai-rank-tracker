import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "rank_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inizializza il database con le tabelle necessarie"""
        with sqlite3.connect(self.db_path) as conn:
            # Migrazione: aggiungi colonne se non esistono
            self._migrate_localization_fields(conn)
            self._migrate_tracking_mode_fields(conn)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    schedule_hours INTEGER DEFAULT 24,
                    country_code TEXT DEFAULT 'IT',
                    language_code TEXT DEFAULT 'it',
                    city_code TEXT,
                    content_restriction BOOLEAN DEFAULT 1,
                    tracking_mode TEXT DEFAULT 'ORGANIC_ONLY',
                    track_ads BOOLEAN DEFAULT 0,
                    track_snippets BOOLEAN DEFAULT 0,
                    track_local BOOLEAN DEFAULT 0,
                    track_shopping BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_check TIMESTAMP,
                    active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    keyword TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ranking_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    keyword TEXT NOT NULL,
                    position INTEGER,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_project_date 
                ON ranking_results (project_id, checked_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_keyword_date 
                ON ranking_results (keyword, checked_at)
            """)
            
            # Nuova tabella per tracciare tutti i tipi di risultati SERP
            conn.execute("""
                CREATE TABLE IF NOT EXISTS serp_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    keyword TEXT NOT NULL,
                    result_type TEXT NOT NULL,
                    position INTEGER,
                    url TEXT,
                    title TEXT,
                    snippet TEXT,
                    domain TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_serp_features_project_type 
                ON serp_features (project_id, result_type, checked_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_serp_features_keyword_type 
                ON serp_features (keyword, result_type, checked_at)
            """)
    
    def create_project(self, 
                      name: str, 
                      domain: str, 
                      schedule_hours: int = 24,
                      country_code: str = 'IT',
                      language_code: str = 'it',
                      city_code: str = None,
                      content_restriction: bool = True,
                      tracking_mode: str = 'ORGANIC_ONLY',
                      track_ads: bool = False,
                      track_snippets: bool = False,
                      track_local: bool = False,
                      track_shopping: bool = False) -> int:
        """Crea un nuovo progetto con localizzazione moderna e opzioni tracking"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO projects 
                (name, domain, schedule_hours, country_code, language_code, city_code, content_restriction,
                 tracking_mode, track_ads, track_snippets, track_local, track_shopping) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, domain, schedule_hours, country_code, language_code, city_code, content_restriction,
                 tracking_mode, track_ads, track_snippets, track_local, track_shopping)
            )
            return cursor.lastrowid
    
    def add_keywords(self, project_id: int, keywords: List[str]):
        """Aggiunge keywords a un progetto"""
        with sqlite3.connect(self.db_path) as conn:
            for keyword in keywords:
                conn.execute(
                    "INSERT INTO keywords (project_id, keyword) VALUES (?, ?)",
                    (project_id, keyword.strip())
                )
    
    def get_all_projects(self) -> List[Dict]:
        """Recupera tutti i progetti"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT p.*, 
                       COUNT(k.id) as keyword_count,
                       COUNT(DISTINCT DATE(r.checked_at)) as check_days
                FROM projects p
                LEFT JOIN keywords k ON p.id = k.project_id
                LEFT JOIN ranking_results r ON p.id = r.project_id
                WHERE p.active = 1
                GROUP BY p.id
                ORDER BY p.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Recupera un progetto specifico"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM projects WHERE id = ? AND active = 1",
                (project_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_keywords(self, project_id: int) -> List[Dict]:
        """Recupera le keywords di un progetto"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM keywords WHERE project_id = ? ORDER BY keyword",
                (project_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def save_result(self, project_id: int, keyword: str, position: Optional[int]):
        """Salva un risultato di ranking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO ranking_results (project_id, keyword, position) VALUES (?, ?, ?)",
                (project_id, keyword, position)
            )
    
    def save_results_batch(self, project_id: int, results: Dict[str, Optional[int]]):
        """Salva multiple risultati in batch"""
        with sqlite3.connect(self.db_path) as conn:
            for keyword, position in results.items():
                conn.execute(
                    "INSERT INTO ranking_results (project_id, keyword, position) VALUES (?, ?, ?)",
                    (project_id, keyword, position)
                )
            
            # Aggiorna last_check del progetto
            conn.execute(
                "UPDATE projects SET last_check = CURRENT_TIMESTAMP WHERE id = ?",
                (project_id,)
            )
    
    def get_latest_results(self, project_id: int) -> List[Dict]:
        """Recupera gli ultimi risultati per un progetto"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT r1.keyword, r1.position, r1.checked_at,
                       r2.position as previous_position
                FROM ranking_results r1
                LEFT JOIN ranking_results r2 ON (
                    r1.keyword = r2.keyword 
                    AND r1.project_id = r2.project_id
                    AND r2.checked_at = (
                        SELECT MAX(checked_at) 
                        FROM ranking_results r3 
                        WHERE r3.keyword = r1.keyword 
                        AND r3.project_id = r1.project_id 
                        AND r3.checked_at < r1.checked_at
                    )
                )
                WHERE r1.project_id = ?
                AND r1.checked_at = (
                    SELECT MAX(checked_at) 
                    FROM ranking_results r4 
                    WHERE r4.keyword = r1.keyword 
                    AND r4.project_id = r1.project_id
                )
                ORDER BY r1.keyword
            """, (project_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_results_history(self, project_id: int, days: int = 30) -> List[Dict]:
        """Recupera lo storico risultati per grafici"""
        since_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT keyword, position, checked_at
                FROM ranking_results
                WHERE project_id = ? AND checked_at >= ?
                ORDER BY checked_at DESC, keyword
            """, (project_id, since_date.isoformat()))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_project_schedule(self, project_id: int, schedule_hours: int):
        """Aggiorna la frequenza di controllo di un progetto"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE projects SET schedule_hours = ? WHERE id = ?",
                (schedule_hours, project_id)
            )
    
    def get_project_localization(self, project_id: int) -> Dict:
        """Recupera la configurazione di localizzazione di un progetto"""
        project = self.get_project(project_id)
        if not project:
            return {}
            
        return {
            'country_code': project.get('country_code', 'IT'),
            'language_code': project.get('language_code', 'it'),
            'city_code': project.get('city_code'),
            'content_restriction': bool(project.get('content_restriction', True))
        }
    
    def _migrate_localization_fields(self, conn):
        """Migra progetti esistenti ai nuovi campi di localizzazione"""
        try:
            # Controlla se esistono i nuovi campi
            cursor = conn.execute("PRAGMA table_info(projects)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Aggiungi campi mancanti
            if 'country_code' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN country_code TEXT DEFAULT 'IT'")
            if 'language_code' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN language_code TEXT DEFAULT 'it'")
            if 'city_code' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN city_code TEXT")
            if 'content_restriction' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN content_restriction BOOLEAN DEFAULT 1")
                
            # Migra vecchi progetti con search_engine
            cursor = conn.execute("SELECT id, search_engine FROM projects WHERE search_engine IS NOT NULL")
            for project_id, search_engine in cursor.fetchall():
                if search_engine == 'google.it':
                    conn.execute("""
                        UPDATE projects 
                        SET country_code = 'IT', language_code = 'it', content_restriction = 1 
                        WHERE id = ?
                    """, (project_id,))
                elif search_engine == 'google.com':
                    conn.execute("""
                        UPDATE projects 
                        SET country_code = 'US', language_code = 'en', content_restriction = 0 
                        WHERE id = ?
                    """, (project_id,))
                    
        except Exception as e:
            print(f"Errore durante migrazione: {e}")

    def get_latest_serp_results(self, project_id: int) -> Dict:
        """Ottiene i risultati SERP modulari più recenti per tipo"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Trova la data di check più recente
            latest_check = conn.execute("""
                SELECT MAX(checked_at) as latest_date
                FROM serp_features 
                WHERE project_id = ?
            """, (project_id,)).fetchone()
            
            if not latest_check or not latest_check['latest_date']:
                return {}
            
            latest_date = latest_check['latest_date']
            
            # Ottieni tutti i risultati per quella data, raggruppati per tipo
            all_results = conn.execute("""
                SELECT * FROM serp_features 
                WHERE project_id = ? AND checked_at = ?
                ORDER BY result_type, position
            """, (project_id, latest_date)).fetchall()
            
            # Raggruppa per tipo di risultato
            serp_results = {
                'organic': [],
                'ads': [],
                'featured_snippets': [],
                'local_pack': [],
                'shopping': []
            }
            
            for row in all_results:
                result_data = dict(row)
                result_type = result_data['result_type']
                
                if result_type in serp_results:
                    serp_results[result_type].append(result_data)
            
            return serp_results
    
    def _migrate_tracking_mode_fields(self, conn):
        """Migra progetti esistenti ai nuovi campi di tracking mode"""
        try:
            cursor = conn.execute("PRAGMA table_info(projects)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Aggiungi campi mancanti per tracking mode
            if 'tracking_mode' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN tracking_mode TEXT DEFAULT 'ORGANIC_ONLY'")
            if 'track_ads' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN track_ads BOOLEAN DEFAULT 0")
            if 'track_snippets' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN track_snippets BOOLEAN DEFAULT 0")
            if 'track_local' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN track_local BOOLEAN DEFAULT 0")
            if 'track_shopping' not in columns:
                conn.execute("ALTER TABLE projects ADD COLUMN track_shopping BOOLEAN DEFAULT 0")
                
        except Exception as e:
            print(f"Errore durante migrazione tracking mode: {e}")
    
    def save_serp_feature(self, project_id: int, keyword: str, result_type: str, 
                         position: int, url: str = None, title: str = None, 
                         snippet: str = None, domain: str = None):
        """Salva un risultato SERP feature"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO serp_features 
                (project_id, keyword, result_type, position, url, title, snippet, domain) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (project_id, keyword, result_type, position, url, title, snippet, domain))
    
    def save_serp_features_batch(self, project_id: int, keyword: str, features: List[Dict]):
        """Salva multiple SERP features in batch"""
        with sqlite3.connect(self.db_path) as conn:
            for feature in features:
                conn.execute("""
                    INSERT INTO serp_features 
                    (project_id, keyword, result_type, position, url, title, snippet, domain) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id, 
                    keyword, 
                    feature['result_type'],
                    feature.get('position'),
                    feature.get('url'),
                    feature.get('title'),
                    feature.get('snippet'),
                    feature.get('domain')
                ))
    
    def get_project_tracking_config(self, project_id: int) -> Dict:
        """Recupera la configurazione di tracking di un progetto"""
        project = self.get_project(project_id)
        if not project:
            return {}
            
        return {
            'tracking_mode': project.get('tracking_mode', 'ORGANIC_ONLY'),
            'track_ads': bool(project.get('track_ads', False)),
            'track_snippets': bool(project.get('track_snippets', False)),
            'track_local': bool(project.get('track_local', False)),
            'track_shopping': bool(project.get('track_shopping', False))
        }
    
    def get_serp_features(self, project_id: int, keyword: str = None, 
                         result_type: str = None) -> List[Dict]:
        """Recupera SERP features per un progetto"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM serp_features WHERE project_id = ?"
            params = [project_id]
            
            if keyword:
                query += " AND keyword = ?"
                params.append(keyword)
            
            if result_type:
                query += " AND result_type = ?"
                params.append(result_type)
            
            query += " ORDER BY checked_at DESC, position"
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_project(self, project_id: int):
        """Disattiva un progetto (soft delete)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE projects SET active = 0 WHERE id = ?",
                (project_id,)
            )