#!/usr/bin/env node

const fs = require('fs');
const assert = require('assert');

const INPUT_DIR = 'input';
const OUTPUT_DIR = 'output';

const inputFile = process.argv[2] || (() => {
  const found = fs.readdirSync(INPUT_DIR).find(f => f.startsWith('search-') && f.endsWith('.csv'));
  return found ? `${INPUT_DIR}/${found}` : null;
})();
if (!inputFile) {
  console.error('No input CSV found.');
  process.exit(1);
}

function decodeParam(str) {
  try {
    return decodeURIComponent(str.replace(/\+/g, ' ')).trim();
  } catch {
    return str.replace(/\+/g, ' ').trim();
  }
}

function getGrandTotal(filepath) {
  for (const line of fs.readFileSync(filepath, 'utf-8').split('\n')) {
    if (line.includes('Grand total')) {
      const parts = line.split(',');
      for (const part of parts) {
        const n = parseInt(part.trim());
        if (!isNaN(n) && n > 0) return n;
      }
    }
  }
  return null;
}

function sumRows(filepath) {
  let total = 0;
  for (const line of fs.readFileSync(filepath, 'utf-8').split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('Page path')) continue;
    const lastComma = trimmed.lastIndexOf(',');
    if (lastComma === -1) continue;
    const url = trimmed.slice(0, lastComma).trim();
    const views = parseInt(trimmed.slice(lastComma + 1));
    if (!url.startsWith('/search') || isNaN(views)) continue;
    total += views;
  }
  return total;
}

const grandTotal = getGrandTotal(inputFile);
assert(grandTotal !== null, 'Could not find Grand total row in CSV');

const summedTotal = sumRows(inputFile);

assert.strictEqual(
  summedTotal,
  grandTotal,
  `Total views mismatch: summed rows give ${summedTotal} but CSV grand total is ${grandTotal}`
);

console.log(`PASS: total views = ${summedTotal} (matches CSV grand total)`);

function sumCsvViews(filepath) {
  let total = 0;
  for (const line of fs.readFileSync(filepath, 'utf-8').split('\n').slice(1)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const lastComma = trimmed.lastIndexOf(',');
    const n = parseInt(trimmed.slice(lastComma + 1));
    if (!isNaN(n)) total += n;
  }
  return total;
}

for (const file of [
  'search_queries.csv',
  'publisher_filters.csv',
  'topic_filters.csv',
  'format_filters.csv',
  'sort_options.csv',
  'filter_types_used.csv',
]) {
  const total = sumCsvViews(`${OUTPUT_DIR}/${file}`);
  assert.strictEqual(total, grandTotal, `${file} total views ${total} does not match grand total ${grandTotal}`);
  console.log(`PASS: ${file} total views = ${total} (matches CSV grand total)`);
}
