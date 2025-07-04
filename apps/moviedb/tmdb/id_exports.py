import requests

url = 'http://files.tmdb.org/p/exports/production_company_ids_04_07_2025.json.gz'

response = requests.get(url)

with open("production_company_ids_04_07_2025.json.gz", "wb") as f:
    f.write(response.content)

print(response)