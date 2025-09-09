from celery import shared_task
from django.core.management import call_command


@shared_task
def daily_db_update():
    call_command('update_collections', 'daily_export', batch_size=1000)
    call_command('update_companies', 'daily_export', batch_size=1000)
    call_command('update_people', 'daily_export', batch_size=1000)

    for i in range(1, 5):
        call_command('update_people', 'update_changed', batch_size=1000, days=i)

    call_command('update_movies', 'daily_export', batch_size=1000)

    for i in range(1, 5):
        call_command('update_movies', 'update_changed', batch_size=1000, days=i)

    call_command('update_removed', 'collection')
    call_command('update_removed', 'company')
    call_command('update_removed', 'movie')
    call_command('update_removed', 'person')

    call_command('update_people', 'roles_count')
    call_command('update_companies', 'movie_count')
    call_command('update_collections', 'movies_released')

    call_command('update_popularity', 'movie', limit=10000)
    call_command('update_popularity', 'person', limit=10000)

    call_command('update_collections', 'avg_popularity')
