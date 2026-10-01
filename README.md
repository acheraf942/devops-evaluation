# DevOps Evaluation — CI/CD, Docker, Métriques

Application Flask avec Redis, conteneurisée, testée, surveillée avec Prometheus, et déployée automatiquement via GitHub Actions.

## Lancer le projet en local

```bash
docker compose up -d --build
```

Trois services démarrent : `web` (l'application, port 5004), `redis` (port 6379) et `prometheus` (port 9090).

Vérifier que tout fonctionne :
```bash
curl http://localhost:5004/health
curl http://localhost:5004/status
```

Arrêter :
```bash
docker compose down
```

## Endpoints de l'application

| Endpoint | Rôle |
|---|---|
| `/health` | Vérifie la connexion à Redis. Renvoie `200` si Redis répond, `503` sinon. |
| `/status` | Renvoie le nom du service et la version (SHA du commit) actuellement déployée. |
| `/visits` | Incrémente un compteur de visites stocké dans Redis. |
| `/simulate-error` | Renvoie toujours une erreur `500`, pour tester les alertes. |
| `/metrics` | Expose les métriques au format Prometheus. |

## Lancer les tests en local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r starter-app/requirements.txt
docker run -d --name redis-demo -p 6379:6379 redis:7-alpine
cd starter-app
pytest -v
flake8 . --max-line-length=100
cd ..
docker rm -f redis-demo
```

## Métriques exposées (`/metrics`)

- **`http_requests_total`** (compteur) — nombre de requêtes, avec les labels `method`, `endpoint`, `code`.
- **`http_request_duration_seconds`** (histogramme) — durée des requêtes par endpoint, permet de calculer un p95/p99.
- **`app_version_info`** (jauge) — SHA du commit actuellement déployé.

## Alertes Prometheus (`prometheus/alert_rules.yml`)

| Alerte | Condition | Durée avant déclenchement |
|---|---|---|
| `TauxErreur5xxEleve` | Plus de 5% des requêtes en erreur 5xx | 30 secondes |
| `LatenceP95Elevee` | p95 des temps de réponse supérieur à 1 seconde | 1 minute |

Consultables sur `http://localhost:9090/rules` une fois la stack démarrée.

## Pipeline CI (`.github/workflows/ci.yml`)

Déclenché sur chaque push et pull request. Quatre jobs enchaînés :

1. **lint** — vérifie le style du code (flake8).
2. **test** — exécute les tests sur Python 3.11 et 3.12 en parallèle, avec un vrai service Redis. Publie les rapports en artefact.
3. **build** — construit l'image Docker, pour vérifier que le Dockerfile fonctionne.
4. **ci-ok** — dépend des trois précédents. C'est ce check qui est requis pour merger sur `main`.

Un workflow séparé (`lint-yaml.yml`) vérifie la syntaxe de tous les fichiers YAML du dépôt.

## Pipeline CD (`.github/workflows/cd.yml`)

Déclenché sur chaque push vers `main`, ou manuellement via `workflow_dispatch`.

1. **build-and-push** — construit l'image et la pousse sur `ghcr.io`, avec trois tags : `latest`, le SHA court du commit, et un tag semver (`v1.0.<numéro de run>`).
2. **deploy** — s'exécute sur un runner self-hosted. Déploie la nouvelle image, vérifie `/health` avec 3 tentatives espacées de 5 secondes. Si le healthcheck échoue, l'ancienne version est automatiquement restaurée (rollback).

## Image publiée
ghcr.io/acheraf942/devops-evaluation


## Dockerfile

Build multi-stage sur `python:3.12-slim` :
- Premier stage : installe les dépendances.
- Second stage : ne garde que le nécessaire à l'exécution, tourne avec un utilisateur non-root (`appuser`), inclut un `HEALTHCHECK` qui appelle réellement `/health`.