# data.gov.uk Link Quality

This directory contains one-off scripts and report CSV files relating to efforts
to improve the quality of dataset links on data.gov.uk.  Over time, CKAN (which
acts as a backend for data.gov.uk directory) has accumulated thousands of links
to data.  A large fraction of those links have become broken.

## Scripts

There are two main scripts in this directory;
- `analyse.py` - takes a broken link report and analyses it for counts/proportions
    of different statuses/breakages.
- `retry.py` - takes a broken link report and retries failed requests.  Writes
    a new broken link report.

To run scripts locally, run the following;
```
uv sync
uv run analyse.py -h
uv run report.py -h
```

## Reports

The directory also holds CSV files relating to link checking activity.
`reports/check-links-output/` contains outputs from our check links scripts in
https://github.com/alphagov/ckanext-datagovuk
`reports/retry/` contains outputs from our retry scripts in this directory.

**Note:** Some of these reports are zipped due to github file upload limits.
