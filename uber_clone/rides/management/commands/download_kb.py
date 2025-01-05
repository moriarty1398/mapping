from django.core.management.base import BaseCommand
from rides.views import download_knowledge_base

class Command(BaseCommand):
    help = 'Download knowledge base data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Downloading knowledge base...')
        download_knowledge_base()
        self.stdout.write(self.style.SUCCESS('Successfully downloaded knowledge base')) 