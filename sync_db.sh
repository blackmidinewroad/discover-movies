#!/bin/sh

set -euo pipefail

start_time=$(date +%s)

echo "Starting: update_collections daily_export"
python manage.py update_collections daily_export --batch_size 1000
echo

echo "Starting: update_companies daily_export"
python manage.py update_companies daily_export --batch_size 1000
echo

echo "Starting: update_people daily_export"
python manage.py update_people daily_export --batch_size 1000
echo

for i in $(seq 1 4); do
    echo "Starting: update_people update_changed days $i"
    python manage.py update_people update_changed --batch_size 1000 --days $i
    echo
done

echo "Starting: update_movies daily_export"
python manage.py update_movies daily_export --batch_size 1000
echo

for i in $(seq 1 4); do
    echo "Starting: update_movies update_changed days $i"
    python manage.py update_movies update_changed --batch_size 1000 --days $i
    echo
done

echo "Starting: update_removed collection"
python manage.py update_removed collection
echo

echo "Starting: update_removed company"
python manage.py update_removed company
echo

echo "Starting: update_removed movie"
python manage.py update_removed movie
echo

echo "Starting: update_removed person"
python manage.py update_removed person
echo

echo "Starting: update_people roles_count"
python manage.py update_people roles_count
echo

echo "Starting: update_companies movie_count"
python manage.py update_companies movie_count
echo

echo "Starting: update_collections movies_released"
python manage.py update_collections movies_released
echo

echo "Starting: update_popularity movie"
python manage.py update_popularity movie --limit 10000
echo

echo "Starting: update_popularity person"
python manage.py update_popularity person --limit 10000
echo

echo "Starting: update_collections avg_popularity"
python manage.py update_collections avg_popularity
echo

end_time=$(date +%s)
duration=$(( end_time - start_time ))

printf "Total Runtime: %02d:%02d:%02d\n" $((duration/3600)) $(( (duration%3600)/60 )) $((duration%60))
