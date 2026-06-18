#!/usr/bin/env node

const fs = require('fs');

const INPUT_DIR = 'input';
const OUTPUT_DIR = 'output';


const inputFile = process.argv[2] || (() => {
  const found = fs.readdirSync(INPUT_DIR).find(f => f.startsWith('search-') && f.endsWith('.csv'));
  return found ? `${INPUT_DIR}/${found}` : null;
})();
if (!inputFile) {
  console.error('No input file found. Pass a CSV filename as argument.');
  process.exit(1);
}

function decodeParam(str) {
  try {
    return decodeURIComponent(str.replace(/\+/g, ' ')).trim();
  } catch {
    return str.replace(/\+/g, ' ').trim();
  }
}

function parseSearchUrl(urlStr) {
  const qIndex = urlStr.indexOf('?');
  if (qIndex === -1) return {};
  const params = {};
  for (const part of urlStr.slice(qIndex + 1).split('&')) {
    const eqIndex = part.indexOf('=');
    if (eqIndex === -1) continue;
    const key = decodeURIComponent(part.slice(0, eqIndex));
    params[key] = decodeParam(part.slice(eqIndex + 1));
  }
  return params;
}

function readRows(filepath) {
  const rows = [];
  for (const line of fs.readFileSync(filepath, 'utf-8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('Page path')) continue;
    const lastComma = trimmed.lastIndexOf(',');
    if (lastComma === -1) continue;
    const url = trimmed.slice(0, lastComma).trim();
    const views = parseInt(trimmed.slice(lastComma + 1));
    if (!url.startsWith('/search') || isNaN(views)) continue;
    rows.push({ url, views });
  }
  return rows;
}

function toCsvCell(val) {
  const str = String(val ?? '');
  return str.includes(',') || str.includes('"') || str.includes('\n')
    ? '"' + str.replace(/"/g, '""') + '"'
    : str;
}

function writeCsv(filename, headers, rows) {
  const filepath = `${OUTPUT_DIR}/${filename}`;
  const lines = [headers.join(','), ...rows.map(r => r.map(toCsvCell).join(','))];
  fs.writeFileSync(filepath, lines.join('\n') + '\n', 'utf-8');
  console.log(`  ${filepath} (${rows.length} rows)`);
}

function aggregate(entries) {
  const map = new Map();
  for (const { value, views } of entries) {
    map.set(value, (map.get(value) || 0) + views);
  }
  return [...map.entries()].sort((a, b) => b[1] - a[1]);
}

// ---- Parse ----
const rows = readRows(inputFile);
console.log(`Parsed ${rows.length} URL patterns from ${inputFile}\n`);

const queries = [], publishers = [], topics = [], formats = [], sorts = [], combos = [], filterTypes = [];

for (const { url, views } of rows) {
  const p = parseSearchUrl(url);
  const q         = p['q'];
  const publisher = p['filters[publisher]'];
  const topic     = p['filters[topic]'];
  const format    = p['filters[format]'];
  const sort      = p['sort'];

  if (q)         queries.push({ value: q, views });
  else           queries.push({ value: '(no query)', views });
  if (publisher) publishers.push({ value: publisher, views });
  else           publishers.push({ value: '(no publisher)', views });
  if (topic)     topics.push({ value: topic, views });
  else           topics.push({ value: '(no topic)', views });
  if (format)    formats.push({ value: format, views });
  else           formats.push({ value: '(no format)', views });
  if (sort)      sorts.push({ value: sort, views });
  else           sorts.push({ value: '(no sort)', views });

  const comboParts = [...(q ? ['[query]'] : []), ...[[publisher, 'publisher'], [topic, 'topic'], [format, 'format']]
    .filter(([v]) => v).map(([v, label]) => `${label}: ${v}`)];
  if (comboParts.length > 1) combos.push({ value: comboParts.join(' | '), views });

  const typeLabel = [q && 'query', publisher && 'publisher', topic && 'topic', format && 'format', sort && 'sort']
    .filter(Boolean).join(' + ') || '(no filters)';
  filterTypes.push({ value: typeLabel, views });
}

// ---- Build reports ----
const totalViews   = rows.reduce((s, r) => s + r.views, 0);
const withQuery    = rows.filter(r => { const p = parseSearchUrl(r.url); return p['q']; });
const withFilter   = rows.filter(r => { const p = parseSearchUrl(r.url); return p['filters[publisher]'] || p['filters[topic]'] || p['filters[format]']; });
const withSort     = rows.filter(r => parseSearchUrl(r.url)['sort']);

const reports = [
  { file: 'search_queries.csv',      sheet: 'Search queries',      headers: ['Query', 'Views'],                rows: aggregate(queries) },
  { file: 'publisher_filters.csv',   sheet: 'Publishers',          headers: ['Publisher', 'Views'],            rows: aggregate(publishers) },
  { file: 'topic_filters.csv',       sheet: 'Topics',              headers: ['Topic', 'Views'],                rows: aggregate(topics) },
  { file: 'format_filters.csv',      sheet: 'Formats',             headers: ['Format', 'Views'],               rows: aggregate(formats) },
  { file: 'sort_options.csv',        sheet: 'Sort options',        headers: ['Sort option', 'Views'],          rows: aggregate(sorts) },
  { file: 'filter_combinations.csv', sheet: 'Filter combinations', headers: ['Filters used together', 'Views'], rows: aggregate(combos) },
  { file: 'filter_types_used.csv',   sheet: 'Filter types used',   headers: ['Filter types used', 'Views'],   rows: aggregate(filterTypes) },
  { file: 'summary_statistics.csv',  sheet: 'Summary',             headers: ['Metric', 'Value'],              rows: [
    ['Total search page views',                totalViews],
    ['Unique URL patterns',                    rows.length],
    ['URL patterns with a search query',       withQuery.length],
    ['URL patterns using at least one filter', withFilter.length],
    ['URL patterns using a sort option',       withSort.length],
    ['Unique search queries',                  aggregate(queries).length],
    ['Unique publishers filtered',             aggregate(publishers).length],
    ['Unique topics filtered',                 aggregate(topics).length],
    ['Unique formats filtered',                aggregate(formats).length],
  ]},
];

// ---- Write CSVs ----
console.log('Writing CSVs:');
for (const { file, headers, rows: data } of reports) writeCsv(file, headers, data);

// ---- Write Excel ----
const ExcelJS = require('exceljs');
const workbook = new ExcelJS.Workbook();
for (const { sheet, headers, rows: data } of reports) {
  const ws = workbook.addWorksheet(sheet);
  ws.addRow(headers);
  ws.getRow(1).font = { bold: true };
  ws.addRows(data);
}
const xlsxFile = `${OUTPUT_DIR}/${inputFile.replace(/^.*\//, '').replace(/\.csv$/, '.xlsx').replace(/^search-/, 'search-analytics-')}`;
workbook.xlsx.writeFile(xlsxFile).then(() => {
  console.log(`\nWriting Excel:\n  ${xlsxFile}`);
  console.log('\nDone.');
});
