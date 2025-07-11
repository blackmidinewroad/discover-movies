from django.core.management.base import BaseCommand

from apps.moviedb.integrations.tmdb.api import asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport
from apps.moviedb.models import Country, ProductionCompany


class Command(BaseCommand):
    help = 'Update production company table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Date of the export file in "MM_DD_YYYY" format.',
        )

        parser.add_argument(
            '--batch_size',
            type=int,
            default=100,
            help='Number of companies to fetch per batch. Defaults to 100.',
        )

        parser.add_argument(
            '--specific_ids',
            type=int,
            default=None,
            nargs='*',
            help='Update specific companies.',
        )

        parser.add_argument(
            '--create',
            action='store_true',
            default=False,
            help='Only create new companies.',
        )

    def handle(self, *args, **options):
        published_date = options['date']
        batch_size = options['batch_size']
        specific_ids = options['specific_ids']
        only_create = options['create']

        company_ids = specific_ids or IDExport().fetch_ids('company', published_date=published_date)

        if only_create:
            existing_ids = set(ProductionCompany.objects.only('tmdb_id').values_list('tmdb_id', flat=True))
            company_ids = [id for id in company_ids if id not in existing_ids]

        companies, missing_ids = asyncTMDB().fetch_companies_by_id(company_ids, batch_size=batch_size)
        countries = {c.code for c in Country.objects.all()}
        company_objs = []
        new_slugs = set()

        for company_data in companies:
            origin_country_code = company_data['origin_country']
            if origin_country_code and origin_country_code not in countries:
                Country.objects.create(code=origin_country_code, name='unknown')
                countries.add(origin_country_code)

            company = ProductionCompany(
                tmdb_id=company_data['id'],
                name=company_data['name'],
                logo_path=company_data['logo_path'] or '',
                origin_country_id=origin_country_code or None,
            )
            company.set_slug(company.name, new_slugs)
            company_objs.append(company)
            new_slugs.add(company.slug)

        ProductionCompany.objects.bulk_create(
            company_objs,
            update_conflicts=True,
            update_fields=('name', 'slug', 'logo_path', 'origin_country'),
            unique_fields=('tmdb_id',),
        )

        self.stdout.write(self.style.SUCCESS(f'Companies processed: {len(companies)}'))
        if missing_ids:
            self.stdout.write(self.style.WARNING(f"Couldn't update/create: {len(missing_ids)} (IDs: {', '.join(map(str, missing_ids))})"))
