# Harvest API converter

A script to take the output from Datapress API and convert it to DCAT so we can harvest it.

This is a manual process for now:

1. Run
```
python3 datapress_to_dcat.py https://data.london.gov.uk/api/v3/datasets/export.json output/london-dcat.json
python3 datapress_to_dcat.py https://datamillnorth.org/api/v3/datasets/export.json output/data-mill-north-dcat.json
python3 datapress_to_dcat.py https://dataworks.calderdale.gov.uk/api/v3/datasets/export.json output/calderdale-dcat.json
```

2. Commit the files and push to github
3. Run the harvesters
