from django.core.management.base import BaseCommand
from video.models import Video
from video.services import extract_video_thumbnail
import os


class Command(BaseCommand):
    help = 'Generiert Thumbnails für alle Videos ohne Thumbnail'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-id',
            type=int,
            help='Generiere Thumbnail nur für ein bestimmtes Video (ID)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Überschreibe bestehende Thumbnails',
        )

    def handle(self, *args, **options):
        video_id = options.get('video_id')
        force = options.get('force', False)
        
        if video_id:
            videos = Video.objects.filter(id=video_id)
            if not videos.exists():
                self.stdout.write(
                    self.style.ERROR(f'Video mit ID {video_id} nicht gefunden')
                )
                return
        else:
            # Alle Videos ohne Thumbnail
            if force:
                videos = Video.objects.filter(video_file__isnull=False)
                self.stdout.write('Generiere Thumbnails für ALLE Videos (--force aktiviert)')
            else:
                videos = Video.objects.filter(
                    video_file__isnull=False,
                    thumbnail__isnull=True,
                    thumbnail_url__isnull=True
                )
                self.stdout.write('Generiere Thumbnails für Videos ohne Thumbnail')

        total_videos = videos.count()
        if total_videos == 0:
            self.stdout.write(
                self.style.WARNING('Keine Videos gefunden, die Thumbnails benötigen')
            )
            return

        self.stdout.write(f'Verarbeite {total_videos} Videos...')
        
        success_count = 0
        error_count = 0
        
        for video in videos:
            try:
                if not video.video_file or not video.video_file.name:
                    self.stdout.write(
                        self.style.WARNING(f'Video {video.id} ({video.title}): Keine Video-Datei')
                    )
                    continue
                
                # Prüfe ob bereits ein Thumbnail existiert (außer bei --force)
                if not force and (video.thumbnail or video.thumbnail_url):
                    self.stdout.write(
                        self.style.WARNING(f'Video {video.id} ({video.title}): Thumbnail bereits vorhanden')
                    )
                    continue
                
                video_path = video.video_file.path
                if not os.path.exists(video_path):
                    self.stdout.write(
                        self.style.ERROR(f'Video {video.id} ({video.title}): Datei nicht gefunden: {video_path}')
                    )
                    error_count += 1
                    continue
                
                # Thumbnail generieren
                self.stdout.write(f'Generiere Thumbnail für Video {video.id} ({video.title})...')
                result = extract_video_thumbnail(video_path, video.id)
                
                if result.get('success'):
                    # Thumbnail im Model speichern
                    video.thumbnail = result['thumbnail_path']
                    video.save(update_fields=['thumbnail'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Thumbnail für Video {video.id} erstellt: {result["thumbnail_path"]}')
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Fehler bei Video {video.id}: {result.get("error")}')
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Unerwarteter Fehler bei Video {video.id}: {str(e)}')
                )
                error_count += 1
        
        # Zusammenfassung
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Zusammenfassung:')
        self.stdout.write(f'  Erfolgreich: {success_count}')
        self.stdout.write(f'  Fehler: {error_count}')
        self.stdout.write(f'  Gesamt: {total_videos}')
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ {success_count} Thumbnails erfolgreich generiert!')
            )
        
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'\n✗ {error_count} Fehler aufgetreten')
            )
