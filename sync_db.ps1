$startTime = Get-Date

Write-Host "Starting: update_collections daily_export"
python manage.py update_collections daily_export --batch_size 1000
Write-Host ""

Write-Host "Starting: update_companies daily_export"
python manage.py update_companies daily_export --batch_size 1000
Write-Host ""

Write-Host "Starting: update_people daily_export"
python manage.py update_people daily_export --batch_size 1000
Write-Host ""

for ($i = 1; $i -le 4; $i++) {
    Write-Host "Starting: update_people update_changed days $i"
    python manage.py update_people update_changed --batch_size 1000 --days $i
    Write-Host ""
}

Write-Host "Starting: update_movies daily_export"
python manage.py update_movies daily_export --batch_size 1000
Write-Host ""

for ($i = 1; $i -le 4; $i++) {
    Write-Host "Starting: update_movies update_changed days $i"
    python manage.py update_movies update_changed --batch_size 1000 --days $i
    Write-Host ""
}

Write-Host "Starting: update_removed collection"
python manage.py update_removed collection
Write-Host ""

Write-Host "Starting: update_removed company"
python manage.py update_removed company
Write-Host ""

Write-Host "Starting: update_removed movie"
python manage.py update_removed movie
Write-Host ""

Write-Host "Starting: update_removed person"
python manage.py update_removed person
Write-Host ""

Write-Host "Starting: update_people roles_count"
python manage.py update_people roles_count
Write-Host ""

Write-Host "Starting: update_companies movie_count"
python manage.py update_companies movie_count
Write-Host ""

Write-Host "Starting: update_collections movies_released"
python manage.py update_collections movies_released
Write-Host ""

Write-Host "Starting: update_popularity movie"
python manage.py update_popularity movie --limit 100000
Write-Host ""

Write-Host "Starting: update_popularity person"
python manage.py update_popularity person --limit 100000
Write-Host ""

Write-Host "Starting: update_collections avg_popularity"
python manage.py update_collections avg_popularity
Write-Host ""

$endTime = Get-Date
$duration = $endTime - $startTime
$rounded = [TimeSpan]::FromSeconds([Math]::Round($duration.TotalSeconds))
Write-Host "Total Runtime: $($rounded.ToString())"