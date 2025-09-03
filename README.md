# Videoflix Backend

Ein Django-basiertes Backend für eine Video-Streaming-Plattform mit Authentifizierung, Video-Verwaltung und Redis-basierten Aufgaben.

## Features

- **Authentifizierung**: JWT-basierte Benutzerauthentifizierung
- **Video-Management**: Upload, Verarbeitung und Streaming von Videos
- **Redis Integration**: Asynchrone Aufgabenverarbeitung mit RQ
- **PostgreSQL**: Robuste Datenbankunterstützung
- **Docker**: Einfache Entwicklungsumgebung
- **REST API**: Vollständige API für Frontend-Integration

## Voraussetzungen

- Docker und Docker Compose
- Python 3.11+ (für lokale Entwicklung)
- Git

## Installation

### 1. Repository klonen
```bash
git clone https://github.com/mneisens/Videoflix_Backend.git
cd Videoflix_Backend
```

### 3. Mit Docker starten 
```bash
#.env erstellen
cp .env.template .env

# Alle Services starten
docker-compose up --build

# Im Hintergrund starten
docker-compose up -d --build
```

## API-Endpoints

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


