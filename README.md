# TaskFlow API

Piccola API REST per gestire utenti e task, scritta in Flask con storage in-memory.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Il server parte su `http://127.0.0.1:5000`.

## Esempio d'uso

```bash
# Registrazione
curl -X POST localhost:5000/register \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "secret"}'

# Login (restituisce un token)
curl -X POST localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "secret"}'

# Creazione task (usa il token del login)
curl -X POST localhost:5000/tasks \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"title": "Comprare il latte", "priority": "high", "tags": ["spesa"]}'

# Lista task
curl localhost:5000/tasks -H 'Authorization: Bearer <TOKEN>'

# Statistiche
curl localhost:5000/tasks/stats -H 'Authorization: Bearer <TOKEN>'
```

## Endpoint

| Metodo | Path              | Descrizione                     | Auth |
|--------|-------------------|---------------------------------|------|
| POST   | `/register`       | Crea un utente                  | No   |
| POST   | `/login`          | Login, restituisce un token     | No   |
| GET    | `/tasks`          | Lista task (paginata)           | Sì   |
| POST   | `/tasks`          | Crea un task                    | Sì   |
| GET    | `/tasks/<id>`     | Dettaglio task                  | Sì   |
| PUT    | `/tasks/<id>`     | Aggiorna un task                | Sì   |
| DELETE | `/tasks/<id>`     | Elimina un task                 | Sì   |
| GET    | `/tasks/stats`    | Statistiche sui task            | Sì   |
