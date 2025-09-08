$startTime = Get-Date

Write-Host "Loading countries"
python manage.py update_countries
Write-Host ""

Write-Host "Loading languages"
python manage.py update_languages
Write-Host ""

Write-Host "Loading genres"
python manage.py update_genres
Write-Host ""

Write-Host "Loading 50 most popular movies"
python manage.py update_movies daily_export --batch_size 50 --sort_by_popularity --limit 50
Write-Host ""

$endTime = Get-Date
$duration = $endTime - $startTime
$rounded = [TimeSpan]::FromSeconds([Math]::Round($duration.TotalSeconds))
Write-Host "Total Runtime: $($rounded.ToString())"