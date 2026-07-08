# Link deletion process for check links output generated 15/06/2026

Source spreadsheet:
(check_links_report_20260615T1628_sorted.csv)[https://github.com/alphagov/datagovuk-scripts/blob/main/reports/check-links-output/15-06-2026/check_links_report_20260615T1628_sorted.csv]

Spreadsheets emailed to users:
(check_links_report_20260615T1628_sorted part 1.xlsx)[https://github.com/alphagov/datagovuk-scripts/blob/main/reports/check-links-output/15-06-2026/check_links_report_20260615T1628_sorted part 1.xlsx]
(check_links_report_20260615T1628_sorted part 2.xlsx)[https://github.com/alphagov/datagovuk-scripts/blob/main/reports/check-links-output/15-06-2026/check_links_report_20260615T1628_sorted part 2.xlsx]

## Retries

```
uv run scripts/retry.py reports/check-links-output/15-06-2026/check_links_report_20260615T1628_sorted.csv reports/retry/15-06-2026/sorted_20260615T1628_retry_20260623T0925.csv
```

First retry result:
(sorted_20260615T1628_retry_20260623T0925.csv)[https://github.com/alphagov/datagovuk-scripts/blob/main/reports/retry/15-06-2026/sorted_20260615T1628_retry_20260623T0925.csv]

```
uv run scripts/retry.py reports/retries/15-06-2026/sorted_20260615T1628_retry_20260623T0925.csv reports/retry/15-06-2026/retry_20260623T0925_retry_20260624T0953.csv
```

Second retry result:
(retry_20260623T0925_retry_20260624T0953.csv)[https://github.com/alphagov/datagovuk-scripts/blob/main/reports/retry/15-06-2026/reports/retry/15-06-2026/retry_20260623T0925_retry_20260624T0953.csv]

```
uv run scripts/retry.py reports/retry/15-06-2026/retry_20260623T0925_retry_20260624T0953.csv reports/retry/15-06-2026/retry_20260624T0953_retry_20260625T0907.csv
```

Third retry result:
(retry_20260624T0953_retry_20260625T0907.csv)[https://github.com/alphagov/datagovuk-scripts/blob/main/reports/retry/15-06-2026/reports/retry/15-06-2026/retry_20260624T0953_retry_20260625T0907.csv]

```
uv run scripts/retry.py reports/retry/15-06-2026/retry_20260624T0953_retry_20260625T0907.csv reports/retry/15-06-2026/retry_20260625T0907_retry_20260707T0942.csv
```

Fourth retry result:
(retry_20260625T0907_retry_20260707T0942.csv)[https://github.com/alphagov/datagovuk-scripts/blob/main/reports/retry/15-06-2026/reports/retry/15-06-2026/retry_20260625T0907_retry_20260707T0942.csv]

## Filtering

```
uv run scripts/filter.py reports/retry/15-06-2026/retry_20260625T0907_retry_20260707T0942.csv reports/filtered/15-06-2026/broken_links_to_delete_20260707T1611.csv --exclude org-name=department-for-transport,plymouth-city-council,national-highways,oxford-city-council,leicester-city-council,rural-payments-agency,environment-agency,nhs-blood-and-transplant,marine-environmental-data-information-network,nottingham-city-council,runnymede-borough-council,natural-resources-wales,office-of-rail-and-road,dartmoor-national-park-authority,natural-england,newcastle-city-council,bridgend-county-borough-council,wirral-metropolitan-borough-council,healthcare-quality-improvement-partnership,animal-and-plant-health-agency,department-for-environment-food-and-rural-affairs,london-borough-of-hounslow,marine-management-organisation,royal-borough-of-kensington-and-chelsea --exclude-substring resource-url=open-geography-portalx-ons.hub.arcgis.com
```
