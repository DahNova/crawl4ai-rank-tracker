# Crawl4AI Rank Tracker

Sistema di monitoraggio posizioni SERP utilizzando crawl4ai per tracciare le posizioni di domini su Google per migliaia di keywords.

## Caratteristiche

- ✅ **Web Interface**: Dashboard intuitiva per configurazione e monitoraggio
- ✅ **Gestione Keywords**: Supporta fino a 3000 keywords per progetto
- ✅ **Scheduling Automatico**: Check automatici programmabili (ogni ora, giorno, settimana)
- ✅ **SERP Parsing**: Estrazione intelligente posizioni da Google SERPs
- ✅ **Rate Limiting**: Gestione automatica per evitare ban
- ✅ **Proxy Support**: Sistema di rotazione proxy per scalabilità
- ✅ **Database SQLite**: Storage risultati con storico completo
- ✅ **Grafici Trend**: Visualizzazione andamento posizioni nel tempo
- ✅ **Background Processing**: Check in background senza bloccare UI

## Installazione

1. **Clona/Scarica il progetto**
```bash
cd "crawl4ai rank tracker"
```

2. **Installa dipendenze**
```bash
pip install -r requirements.txt
```

3. **Avvia l'applicazione**
```bash
python app.py
```

4. **Accedi alla dashboard**
Apri il browser su: http://localhost:8000

## Utilizzo

### 1. Creare un Progetto
- Clicca "Nuovo Progetto" nella dashboard
- Inserisci nome progetto e dominio target
- Incolla le keywords (una per riga, fino a 3000)
- Imposta frequenza check (consigliato: 24 ore per grandi volumi)

### 2. Monitoraggio
- La dashboard mostra tutti i progetti attivi
- Clicca "Dettagli" per vedere risultati e trend
- Usa "Run Check" per controlli manuali immediati

### 3. Risultati
- Posizioni trovate con codici colore (verde=top3, giallo=top10)
- Confronto con posizioni precedenti
- Grafici trend per visualizzare andamenti
- Export dati disponibile

## Configurazione Avanzata

### Rate Limiting
Il sistema include rate limiting automatico:
- 2-4 secondi tra requests
- Batch processing (10 keywords alla volta)
- Pausa 10-15 secondi tra batch
- Per 3000 keywords: ~15-20 minuti per check completo

### Proxy Configuration
Per scale maggiori, configura proxy in `rank_tracker.py`:
```python
# Aggiungi lista proxy
PROXY_LIST = [
    "http://proxy1:port",
    "http://proxy2:port"
]
```

### Database
SQLite database automatico in `rank_tracker.db`:
- Tabella `projects`: configurazioni progetti
- Tabella `keywords`: lista keywords per progetto  
- Tabella `ranking_results`: storico risultati con timestamp

## Limitazioni e Best Practices

### Google Rate Limits
- **Max 100 risultati** per ricerca Google
- **Rate limiting essenziale** per evitare ban IP
- **User-agent rotation** inclusa
- **Headless browser** per JavaScript rendering

### Prestazioni
- **Batch size**: 10 keywords per batch (configurabile)
- **Concurrent projects**: Max 1 progetto in check simultaneo
- **Memory usage**: ~50-100MB per 1000 keywords

### Raccomandazioni
- **Check frequency**: 24-48 ore per progetti con 1000+ keywords
- **Proxy rotation**: Necessaria per 2000+ keywords/giorno
- **VPS hosting**: Consigliato per monitoring 24/7
- **Backup database**: Importante per storico risultati

## Struttura File

```
crawl4ai rank tracker/
├── app.py              # FastAPI application
├── rank_tracker.py     # Core SERP scraping logic
├── database.py         # SQLite database management
├── scheduler.py        # Background job scheduling
├── requirements.txt    # Python dependencies
├── templates/
│   ├── dashboard.html      # Main dashboard
│   └── project_detail.html # Project results page
└── rank_tracker.db     # SQLite database (auto-created)
```

## Troubleshooting

### Errori Comuni
1. **"Crawler failed"**: Verifica connessione internet e rate limits
2. **"No results found"**: Google potrebbe aver bloccato, prova con proxy
3. **"Database locked"**: Chiudi altre istanze dell'app

### Performance Issues
- Riduci batch size per connessioni lente
- Aumenta delay tra requests se hai errori 429
- Usa proxy per volumi elevati

## Tecnologie

- **Backend**: FastAPI, SQLite, APScheduler
- **Frontend**: TailwindCSS, Alpine.js, Plotly.js
- **Scraping**: Crawl4AI, Chromium headless
- **Database**: SQLite con indici ottimizzati