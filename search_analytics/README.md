# Search analytics

Processes data.gov.uk search page analytics exports into per-dimension CSV reports and a single Excel workbook.

## Setup

```
npm install
```

## Usage

1. Drop a GA CSV export into `input/` (filename must start with `search-`)
2. Run the script:

```
npm start
```

Output files are written to `output/`:

- `search_queries.csv` — search terms by views
- `publisher_filters.csv` — publisher filter usage
- `topic_filters.csv` — topic filter usage
- `format_filters.csv` — format filter usage
- `sort_options.csv` — sort option usage
- `filter_combinations.csv` — filter combinations used together
- `filter_types_used.csv` — which filter types were combined
- `summary_statistics.csv` — headline totals
- `search-analytics-*.xlsx` — all of the above in one workbook

You can also pass a specific input file as an argument:

```
npm start -- input/search-2026-04-17.csv
```

## Tests

```
npm test
```

Verifies that the view totals in each output CSV sum to the grand total in the input file.
