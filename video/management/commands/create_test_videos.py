from django.core.management.base import BaseCommand
from video.models import Video

class Command(BaseCommand):
    help = 'Erstellt Test-Videos für die Videoflix-Anwendung'

    def handle(self, *args, **options):
        # Test-Videos erstellen
        videos_data = [
            {
                'title': 'The Matrix',
                'description': 'Ein Computerprogrammierer entdeckt, dass die Realität, wie er sie kennt, eine Simulation ist.',
                'category': 'sci-fi',
                'thumbnail_url': 'https://example.com/thumbnails/matrix.jpg',
                'duration': 8160,  # 136 Minuten in Sekunden
            },
            {
                'title': 'Inception',
                'description': 'Ein Dieb, der Informationen aus dem Unterbewusstsein seiner Ziele stiehlt.',
                'category': 'sci-fi',
                'thumbnail_url': 'https://example.com/thumbnails/inception.jpg',
                'duration': 8880,  # 148 Minuten in Sekunden
            },
            {
                'title': 'The Dark Knight',
                'description': 'Batman kämpft gegen den Joker in Gotham City.',
                'category': 'action',
                'thumbnail_url': 'https://example.com/thumbnails/dark-knight.jpg',
                'duration': 9120,  # 152 Minuten in Sekunden
            },
            {
                'title': 'Pulp Fiction',
                'description': 'Verschiedene Geschichten von Gangstern in Los Angeles.',
                'category': 'crime',
                'thumbnail_url': 'https://example.com/thumbnails/pulp-fiction.jpg',
                'duration': 9240,  # 154 Minuten in Sekunden
            },
            {
                'title': 'Forrest Gump',
                'description': 'Die Geschichte eines Mannes mit niedrigem IQ, der wichtige Momente der amerikanischen Geschichte erlebt.',
                'category': 'drama',
                'thumbnail_url': 'https://example.com/thumbnails/forrest-gump.jpg',
                'duration': 8520,  # 142 Minuten in Sekunden
            },
        ]

        created_count = 0
        for video_data in videos_data:
            video, created = Video.objects.get_or_create(
                title=video_data['title'],
                defaults=video_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Video "{video.title}" erstellt')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Video "{video.title}" existiert bereits')
                )

        self.stdout.write(
            self.style.SUCCESS(f'{created_count} neue Videos erstellt')
        )
