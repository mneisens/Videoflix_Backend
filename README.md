# Videoflix Backend API

Ein Django-basiertes Backend für Video-Streaming mit HLS, JWT-Authentifizierung und Background-Task-Verarbeitung.

## Schnellstart

### Voraussetzungen
- Python 3.11+
- PostgreSQL
- Redis
- FFmpeg 

### 1. Repository klonen
```bash
git clone https://github.com/mneisens/Videoflix_Backend.git
cd Videoflix_Backend
```

### 2. Virtuelle Umgebung aktivieren
```bash
python -m venv env
source env/bin/activate  # macOS/Linux
# oder: env\Scripts\activate  # Windows
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. Environment konfigurieren
```bash
cp .env.template .env
# .env mit deinen Datenbank-Credentials bearbeiten
```

### 5. Datenbank einrichten
```bash
# PostgreSQL starten und Datenbank erstellen
python manage.py makemigrations
python manage.py migrate
```

### 6. Superuser erstellen
```bash
python manage.py createsuperuser
```

### 7. Server starten
```bash
python manage.py runserver
```

## 🐳 Docker (Alternative)

```bash
docker-compose up --build
```

## 📱 API-Endpunkte

- **Auth**: `/api/auth/register/`, `/api/auth/login/`
- **Videos**: `/api/videos/`, `/api/videos/<id>/`
- **HLS**: `/api/videos/<id>/hls/manifest/`, `/api/videos/<id>/hls/segment/<segment>/`

## 🔧 Wichtige Features

- **JWT-Authentifizierung**
- **HLS Video-Streaming**
- **Background-Task-Verarbeitung (Django RQ)**
- **Redis-Caching**
- **PostgreSQL-Datenbank**
- **Admin-Interface**: `/admin/`

```

##  Fehlerbehebung

- **Redis-Verbindung**: `redis-server` starten
- **PostgreSQL**: Datenbank-Service starten
- **FFmpeg**: Für Video-Verarbeitung installieren


