from django.core.management.base import BaseCommand

from apps.moviedb.models import Country, ProductionCompany
from apps.moviedb.tmdb.api import TMDB
from apps.moviedb.tmdb.id_exports import IDExport


class Command(BaseCommand):
    help = 'Update production company table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "DD_MM_YYYY" format.',
        )

    def handle(self, *args, **kwargs):
        id_export = IDExport()
        tmdb = TMDB()
        
        published_date = kwargs['date']
        company_ids = id_export.fetch_ids('company', published_date=published_date)

        for id in company_ids[20870:]:
            company = tmdb.fetch_company_by_id(id)

            country = created_country = None
            if company['origin_country']:
                country, created_country = Country.objects.get_or_create(code=company['origin_country'], defaults={'name': 'unknown'})

            _, created_company = ProductionCompany.objects.update_or_create(
                tmdb_id=id,
                defaults={
                    'name': company['name'],
                    'logo_path': company['logo_path'] or '',
                    'origin_country': country,
                },
            )

            if created_country:
                self.stdout.write(self.style.NOTICE(f'Created new country: {company['origin_country']}'))

            # action = 'Created' if created_company else 'Updated'
            # self.stdout.write(self.style.SUCCESS(f'{action} company: {company['name']}'))
