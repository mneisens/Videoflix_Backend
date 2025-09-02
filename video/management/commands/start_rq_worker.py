"""
Management command to start RQ workers
"""
from django.core.management.base import BaseCommand
from django_rq import get_worker, get_queue
import time
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start RQ workers for background task processing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queues',
            nargs='+',
            default=['default'],
            help='Queues to process (default: default)'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=1,
            help='Number of workers to start (default: 1)'
        )
        parser.add_argument(
            '--burst',
            action='store_true',
            help='Run in burst mode (exit when no jobs)'
        )

    def handle(self, *args, **options):
        queues = options['queues']
        num_workers = options['workers']
        burst_mode = options['burst']

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting {num_workers} RQ worker(s) for queues: {", ".join(queues)}'
            )
        )

        try:
            queue_instances = [get_queue(queue_name) for queue_name in queues]

            workers = []
            for i in range(num_workers):
                worker = get_worker(*queue_instances)
                workers.append(worker)
                self.stdout.write(f'Worker {i+1} created for queues: {", ".join(queues)}')

            if burst_mode:
                self.stdout.write('Running workers in burst mode...')
                for worker in workers:
                    worker.work(burst=True)
            else:
                self.stdout.write('Starting workers (press Ctrl+C to stop)...')
                for worker in workers:
                    worker.work()

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nStopping workers...')
            )
            for worker in workers:
                worker.shutdown()
            self.stdout.write(
                self.style.SUCCESS('Workers stopped successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting workers: {str(e)}')
            )
            logger.error(f'Error starting RQ workers: {str(e)}')
