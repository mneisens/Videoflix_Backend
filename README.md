# Videoflix Backend

Ein Django-basiertes Backend für eine Video-Streaming-Plattform mit Authentifizierung, Video-Verwaltung und Redis-basierten Aufgaben.

## 🚀 Features

- **Authentifizierung**: JWT-basierte Benutzerauthentifizierung
- **Video-Management**: Upload, Verarbeitung und Streaming von Videos
- **Redis Integration**: Asynchrone Aufgabenverarbeitung mit RQ
- **PostgreSQL**: Robuste Datenbankunterstützung
- **Docker**: Einfache Entwicklungsumgebung
- **REST API**: Vollständige API für Frontend-Integration

## 📋 Voraussetzungen

- Docker und Docker Compose
- Python 3.11+ (für lokale Entwicklung)
- Git

## 🛠️ Installation

### 1. Repository klonen
```bash
git clone https://github.com/mneisens/Videoflix_Backend.git
cd Videoflix_Backend
```

### 2. Umgebungsvariablen konfigurieren
Erstellen Sie eine `.env` Datei basierend auf der `.env.template`:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=videoflix_password
DB_HOST=db
DB_PORT=5432

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis
REDIS_URL=redis://localhost:6379/0

# pgAdmin
PGADMIN_EMAIL=admin@videoflix.com
PGADMIN_PASSWORD=admin123
```

### 3. Mit Docker starten (Empfohlen)
```bash
# Alle Services starten
docker-compose up --build

# Im Hintergrund starten
docker-compose up -d --build
```

### 4. Alternative: Lokale Entwicklung
```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Datenbank-Migrationen
python manage.py migrate

# Server starten
python manage.py runserver
```

## 🌐 Zugriff auf Services

Nach dem Start sind folgende Services verfügbar:

| Service | URL | Port | Beschreibung |
|---------|-----|-------|--------------|
| Django Backend | http://localhost:8000 | 8000 | Haupt-API |
| Django Admin | http://localhost:8000/admin | 8000 | Admin-Interface |
| pgAdmin | http://localhost:8082 | 8082 | Datenbank-Verwaltung |
| Redis Commander | http://localhost:8081 | 8081 | Redis-Monitoring |
| PostgreSQL | - | 5432 | Datenbank |
| Redis | - | 6379 | Cache & Queue |

## 🔧 Erste Schritte

### 1. Datenbank-Migrationen
```bash
docker-compose exec web python manage.py migrate
```

### 2. Superuser erstellen
```bash
docker-compose exec web python manage.py createsuperuser
```

### 3. Statische Dateien sammeln
```bash
docker-compose exec web python manage.py collectstatic
```

### 4. RQ Worker starten (für Hintergrundaufgaben)
```bash
docker-compose exec web python manage.py start_rq_worker
```

## 📁 Projektstruktur

```
Videoflix_Backend/
├── auth_app/           # Authentifizierung
│   ├── api/           # Auth-API-Endpoints
│   ├── models.py      # Benutzermodelle
│   └── services.py    # Auth-Services
├── video/             # Video-Management
│   ├── api/           # Video-API-Endpoints
│   ├── models.py      # Video-Modelle
│   ├── tasks.py       # Hintergrundaufgaben
│   └── services.py    # Video-Services
├── core/              # Django-Projekt-Konfiguration
│   ├── settings.py    # Hauptkonfiguration
│   └── urls.py        # URL-Routing
├── docker-compose.yml # Docker-Services
└── requirements.txt   # Python-Abhängigkeiten
```

## 🔐 API-Endpoints

### Authentifizierung
- `POST /api/auth/register/` - Benutzer registrieren
- `POST /api/auth/login/` - Benutzer anmelden
- `POST /api/auth/refresh/` - Token erneuern
- `POST /api/auth/logout/` - Benutzer abmelden

### Videos
- `GET /api/videos/` - Alle Videos abrufen
- `POST /api/videos/` - Neues Video hochladen
- `GET /api/videos/{id}/` - Video-Details abrufen
- `PUT /api/videos/{id}/` - Video bearbeiten
- `DELETE /api/videos/{id}/` - Video löschen

## 🐛 Häufige Probleme

### 1. PostgreSQL-Versionskonflikt
```bash
# Alle Container und Volumes stoppen
docker-compose down -v

# Neu starten
docker-compose up --build
```

### 2. Berechtigungsprobleme mit Entrypoint
```bash
# Ausführungsberechtigung setzen
chmod +x backend.entrypoint.sh

# Container neu starten
docker-compose restart web
```

### 3. Port bereits belegt
```bash
# Ports überprüfen
lsof -i :8000

# Container stoppen
docker-compose down
```

## 🧪 Tests

```bash
# Alle Tests ausführen
docker-compose exec web python manage.py test

# Spezifische App testen
docker-compose exec web python manage.py test auth_app
docker-compose exec web python manage.py test video
```

## 📊 Monitoring

### Logs anzeigen
```bash
# Alle Services
docker-compose logs

# Spezifischer Service
docker-compose logs web
docker-compose logs db
docker-compose logs redis
```

### Container-Status
```bash
docker-compose ps
docker-compose top
```

## 🚀 Deployment

### Produktionsumgebung
1. `DEBUG=False` in `.env` setzen
2. Sichere `SECRET_KEY` generieren
3. `ALLOWED_HOSTS` konfigurieren
4. SSL-Zertifikate einrichten
5. Datenbank-Backups konfigurieren

### Umgebungsvariablen für Produktion
```env
DEBUG=False
SECRET_KEY=<sicherer-schlüssel>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:port/dbname
```

## 🤝 Beitragen

1. Fork des Repositories
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert.

## 📞 Support

Bei Fragen oder Problemen:
- Issue im GitHub-Repository erstellen
- Dokumentation überprüfen
- Logs analysieren mit `docker-compose logs`

## 🔄 Updates

```bash
# Neueste Änderungen holen
git pull origin main

# Container neu bauen
docker-compose up --build

# Datenbank-Migrationen
docker-compose exec web python manage.py migrate
```

---

**Viel Erfolg mit Ihrem Videoflix-Projekt! 🎬✨**


