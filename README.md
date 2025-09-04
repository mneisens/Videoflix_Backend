# Videoflix Backend

A Django-based backend for a video streaming platform with authentication, video management, and Redis-based task processing.

## Features

- **Authentication**: JWT-based user authentication
- **Video Management**: Upload, processing, and streaming of videos
- **Redis Integration**: Asynchronous task processing with RQ
- **PostgreSQL**: Robust database support
- **Docker**: Easy development environment
- **REST API**: Complete API for frontend integration
- **HLS Streaming**: Adaptive video streaming with multiple resolutions

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git
- Redis (for local development)

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/mneisens/Videoflix_Backend.git
cd Videoflix_Backend
```

### 2. Docker Setup
```bash
# Create .env file
cp .env.template .env

# Start all services
docker-compose up --build

# Start in background
docker-compose up -d --build
```

## API Endpoints

### Authentication
- `POST /api/register/` - Register new user
- `POST /api/login/` - User login
- `POST /api/refresh/` - Refresh token
- `POST /api/logout/` - User logout
- `GET /api/activate/{user_id}/{token}/` - Activate user account

### Videos
- `GET /api/video/` - Get all videos
- `POST /api/video/` - Upload new video
- `GET /api/video/{id}/` - Get video details
- `PUT /api/video/{id}/` - Update video
- `DELETE /api/video/{id}/` - Delete video
- `GET /api/video/{id}/{resolution}/index.m3u8` - HLS manifest
- `GET /api/video/{id}/{resolution}/{segment}` - HLS video segment

## Configuration

### Environment Variables
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `REDIS_HOST`: Redis host (localhost for local development)
- `EMAIL_HOST`: SMTP server for email sending
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password


