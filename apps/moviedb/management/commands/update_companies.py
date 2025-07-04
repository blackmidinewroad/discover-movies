from django.core.management.base import BaseCommand

from apps.moviedb.models import Country, ProductionCompany
from apps.moviedb.tmdb.api import TMDB
from apps.moviedb.tmdb.id_exports import IDExport


class Command(BaseCommand):
    help = 'Update production company table'

    def handle(self, *args, **kwargs):
        id_export = IDExport()
        tmdb = TMDB()
        company_ids = id_export.fetch_ids('company')
        for id in company_ids:
            company = tmdb.fetch_company_by_id(id)
            country = Country.objects.get(code=company['origin_country']) if company['origin_country'] else None
            _, created = ProductionCompany.objects.update_or_create(
                tmdb_id=id,
                defaults={
                    'name': company['name'],
                    'logo_path': company['logo_path'] if company['logo_path'] else '',
                    'origin_country': country,
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} company: {company['name']}'))
