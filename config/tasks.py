import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger('moviedb')


@shared_task
def daily_db_update():
    logger.info('Starting: update_genres')
    call_command('update_genres')

    logger.info('Starting: update_countries')
    call_command('update_countries')

    logger.info('Starting: update_languages')
    call_command('update_languages')

    logger.info('Starting: update_collections daily_export')
    call_command('update_collections', 'daily_export', batch_size=1000)

    logger.info('Starting: update_companies daily_export')
    call_command('update_companies', 'daily_export', batch_size=1000)

    logger.info('Starting: update_people daily_export')
    call_command('update_people', 'daily_export', batch_size=1000)

    for i in range(1, 5):
        logger.info('Starting: update_people update_changed days %s', i)
        call_command('update_people', 'update_changed', batch_size=1000, days=i)

    logger.info('Starting: update_movies daily_export')
    call_command('update_movies', 'daily_export', batch_size=1000)

    for i in range(1, 5):
        logger.info('Starting: update_movies update_changed days %s', i)
        call_command('update_movies', 'update_changed', batch_size=1000, days=i)

    logger.info('Starting: update_removed collection')
    call_command('update_removed', 'collection')

    logger.info('Starting: update_removed company')
    call_command('update_removed', 'company')

    logger.info('Starting: update_removed movie')
    call_command('update_removed', 'movie')

    logger.info('Starting: update_removed person')
    call_command('update_removed', 'person')

    logger.info('Starting: update_people roles_count')
    call_command('update_people', 'roles_count')

    logger.info('Starting: update_companies movie_count')
    call_command('update_companies', 'movie_count')

    logger.info('Starting: update_collections movies_released')
    call_command('update_collections', 'movies_released')

    logger.info('Starting: update_popularity movie')
    call_command('update_popularity', 'movie', limit=10000)

    logger.info('Starting: update_popularity person')
    call_command('update_popularity', 'person', limit=10000)

    logger.info('Starting: update_collections avg_popularity')
    call_command('update_collections', 'avg_popularity')
