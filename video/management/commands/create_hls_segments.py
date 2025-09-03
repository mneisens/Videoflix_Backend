from django.core.management.base import BaseCommand
from video.models import Video
from video.services import create_hls_stream


class Command(BaseCommand):
    help = 'Erstellt HLS-Segmente für alle Videos oder spezifische Videos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-id',
            type=int,
            help='Spezifische Video-ID für die HLS-Segmente erstellt werden sollen'
        )
        parser.add_argument(
            '--resolution',
            type=str,
            choices=['480p', '720p', '1080p', 'all'],
            default='all',
            help='Auflösung für die HLS-Segmente erstellt werden sollen (Standard: alle)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Überschreibt existierende HLS-Segmente'
        )

    def handle(self, *args, **options):
        video_id = options.get('video_id')
        resolution = options.get('resolution')
        force = options.get('force')

        if video_id:
            try:
                video = Video.objects.get(id=video_id)
                self.create_hls_for_video(video, resolution, force)
            except Video.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Video mit ID {video_id} nicht gefunden!')
                )
        else:
            videos = Video.objects.filter(video_file__isnull=False)
            self.stdout.write(f'Erstelle HLS-Segmente für {videos.count()} Videos...')
            
            for video in videos:
                self.create_hls_for_video(video, resolution, force)

    def create_hls_for_video(self, video, resolution, force):
        """Erstellt HLS-Segmente für ein spezifisches Video"""
        if not video.video_file:
            self.stdout.write(
                self.style.WARNING(f'Video "{video.title}" hat keine Video-Datei, überspringe...')
            )
            return

        self.stdout.write(f'Verarbeite Video "{video.title}" (ID: {video.id})...')

        if resolution == 'all':
            resolutions = ['480p', '720p', '1080p']
        else:
            resolutions = [resolution]

        success_count = 0
        error_count = 0

        for res in resolutions:
            try:
                result = create_hls_stream(video.video_file.path, video.id, res)
                if result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(f'   {res}: HLS-Segmente erfolgreich erstellt')
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   {res}: {result["error"]}')
                    )
                    error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   {res}: Exception - {str(e)}')
                )
                error_count += 1

        if error_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f' Video "{video.title}": Alle {success_count} HLS-Segmente erfolgreich erstellt!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Video "{video.title}": {success_count} erfolgreich, {error_count} fehlgeschlagen')
            )
