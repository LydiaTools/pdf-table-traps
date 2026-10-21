const SAMPLE_MARKDOWN = `Garden materials estimate
Case A: ruled table, one header row, three material rows
| Material         | Volume (m3) | Unit price ($) |        | Line total ($) |           |
| ---------------- | ----------- | -------------- | ------ | -------------- | --------- |
| Cedar mulch      |             | 12.5           | 64.00  |                | 800.00    |
| Screened compost |             | 3.25           | 88.00  |                | 286.00    |
| River gravel     |             | 1.8            | 145.00 |                | 261.00    |
| Materials total  |             |                |        |                | $1,347.00 |
Keep each price attached to its material. The total alone is not a table check.
Synthetic test fixture by LydiaTools. Fictional values; not a supplier quote. 1 / 1`;

const form = document.querySelector('#check-form');
const markdown = document.querySelector('#markdown');
const result = document.querySelector('#result');
const languageButton = document.querySelector('#language');
const tablePreview = document.querySelector('#table-preview');
const encoder = new TextEncoder();

const copy = {
  en: {
    passBadge: 'Matches', failBadge: 'Mismatch', unknownBadge: 'Needs review',
    passTitle: 'The value is under the expected header.',
    failTitle: 'The cell value does not match.',
    unknownTitle: 'This check needs review.',
    passReason: 'The row, column and value match the expectation.',
    failReason: 'The row and header were found, but the value is different.',
    reasons: {
      size: 'Text is over the 2 MiB limit.',
      tableNumber: 'Enter a table number from 1 to 100.',
      missingTable: 'No supported Markdown table was found at that number.',
      unsupported: 'This table contains HTML or image content that needs review.',
      missingHeader: 'The row key or target header is missing or ambiguous.',
      missingRow: 'The row value is missing or appears more than once.',
      ragged: 'The selected row has a different number of cells than the header.',
      empty: 'Paste a Markdown pipe table to check.'
    },
    table: 'Table', emptyPreview: 'No table to show.'
  },
  zh: {
    passBadge: '匹配', failBadge: '不符', unknownBadge: '需核查',
    passTitle: '该值位于指定列。',
    failTitle: '单元格值不符。',
    unknownTitle: '这项检查需要人工核对。',
    passReason: '目标行、列和值均与预期一致。',
    failReason: '已找到目标行和列，但单元格值不同。',
    reasons: {
      size: '文本超过 2 MiB 限制。',
      tableNumber: '表格序号应在 1 到 100 之间。',
      missingTable: '该序号下没有找到支持的 Markdown 表格。',
      unsupported: '该表格包含 HTML 或图片内容，需要人工核对。',
      missingHeader: '行标识列或目标列缺失、重复或不明确。',
      missingRow: '行标识值未找到或出现多次。',
      ragged: '目标行的单元格数量与表头不一致。',
      empty: '请粘贴 Markdown 管道表格。'
    },
    table: '表格', emptyPreview: '没有可显示的表格。'
  }
};

function currentLanguage() {
  return document.documentElement.dataset.lang === 'zh' ? 'zh' : 'en';
}

function normalized(value) {
  return String(value ?? '').normalize('NFC').replace(/\s+/gu, ' ').trim();
}

function parseCells(line) {
  let source = line.trim();
  if (source.startsWith('|')) source = source.slice(1);
  let slashCount = 0;
  for (let i = source.length - 1; i >= 0 && source[i] === '\\'; i -= 1) slashCount += 1;
  if (source.endsWith('|') && slashCount % 2 === 0) source = source.slice(0, -1);

  const cells = [];
  let cell = '';
  let codeFence = 0;
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];
    if (char === '\\' && source[i + 1] === '|') {
      cell += '|';
      i += 1;
      continue;
    }
    if (char === '`') {
      let run = 1;
      while (source[i + run] === '`') run += 1;
      if (codeFence === 0) codeFence = run;
      else if (codeFence === run) codeFence = 0;
      cell += source.slice(i, i + run);
      i += run - 1;
      continue;
    }
    if (char === '|' && codeFence === 0) {
      cells.push(cell.trim());
      cell = '';
      continue;
    }
    cell += char;
  }
  cells.push(cell.trim());
  return cells;
}

function isDelimiter(line) {
  const cells = parseCells(line);
  return cells.length > 0 && cells.every(cell => /^:?-+:?$/.test(cell));
}

function cleanCell(cell) {
  return cell
    .replace(/(`+)(.*?)\1/g, '$2')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/(^|[\s([{])\*\*([^*\n]+)\*\*(?=$|[\s)\]}.,!?;:])/g, '$1$2')
    .replace(/(^|[\s([{])__([^_\n]+)__(?=$|[\s)\]}.,!?;:])/g, '$1$2')
    .replace(/(^|[\s([{])\*([^*\n]+)\*(?=$|[\s)\]}.,!?;:])/g, '$1$2')
    .replace(/(^|[\s([{])_([^_\n]+)_(?=$|[\s)\]}.,!?;:])/g, '$1$2')
    .replace(/\\([\\`*_{}\[\]()#+\-.!|>])/g, '$1')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .trim();
}

function parseMarkdown(text) {
  const lines = text.replace(/\r\n?/g, '\n').split('\n');
  const usable = [];
  let fence = null;
  for (const line of lines) {
    const marker = line.match(/^\s{0,3}(`{3,}|~{3,})/);
    if (fence) {
      if (marker && marker[1][0] === fence.char && marker[1].length >= fence.length) fence = null;
      usable.push('');
    } else if (marker) {
      fence = { char: marker[1][0], length: marker[1].length };
      usable.push('');
    } else {
      usable.push(line);
    }
  }

  const tables = [];
  for (let i = 0; i < usable.length - 1;) {
    if (!usable[i].includes('|') || !isDelimiter(usable[i + 1])) {
      i += 1;
      continue;
    }
    const rawHeaders = parseCells(usable[i]);
    const headers = rawHeaders.map(cleanCell);
    const rows = [];
    const rawRows = [usable[i], usable[i + 1]];
    let limitExceeded = rawHeaders.length !== parseCells(usable[i + 1]).length
      || headers.length > 100 || headers.some(cell => cell.length > 20000);
    i += 2;
    while (i < usable.length && usable[i].trim() && usable[i].includes('|')) {
      const row = parseCells(usable[i]).map(cleanCell);
      if (row.length > 100 || row.some(cell => cell.length > 20000) || rows.length >= 1000) limitExceeded = true;
      if (rows.length < 1000) rows.push(row);
      rawRows.push(usable[i]);
      i += 1;
    }
    const unsupported = rawRows.some(line => /<\/?[a-z][^>]*>/i.test(line) || /!\[[^\]]*\]\(/.test(line));
    tables.push({ headers, rows, unsupported: unsupported || limitExceeded });
    if (tables.length >= 100) break;
  }
  return tables;
}

function evaluate(tables, input) {
  const strings = copy[currentLanguage()];
  if (!input.markdown.trim()) return { status: 'unknown', reason: strings.reasons.empty };
  if (encoder.encode(input.markdown).length > 2 * 1024 * 1024) return { status: 'unknown', reason: strings.reasons.size };
  if (!Number.isInteger(input.table) || input.table < 1 || input.table > 100) return { status: 'unknown', reason: strings.reasons.tableNumber };
  const table = tables[input.table - 1];
  if (!table) return { status: 'unknown', reason: strings.reasons.missingTable };
  if (table.unsupported) return { status: 'unknown', reason: strings.reasons.unsupported, table };

  const rowKeyMatches = table.headers.map((header, index) => normalized(header) === normalized(input.rowKey) ? index : -1).filter(index => index >= 0);
  const columnMatches = table.headers.map((header, index) => normalized(header) === normalized(input.column) ? index : -1).filter(index => index >= 0);
  if (rowKeyMatches.length !== 1 || columnMatches.length !== 1) return { status: 'unknown', reason: strings.reasons.missingHeader, table };
  const rowKeyIndex = rowKeyMatches[0];
  const columnIndex = columnMatches[0];
  const rows = table.rows.map((row, index) => ({ row, index })).filter(item => normalized(item.row[rowKeyIndex]) === normalized(input.rowValue));
  if (rows.length !== 1) return { status: 'unknown', reason: strings.reasons.missingRow, table };
  const selected = rows[0];
  if (selected.row.length !== table.headers.length || columnIndex >= selected.row.length) return { status: 'unknown', reason: strings.reasons.ragged, table };
  const actual = selected.row[columnIndex] ?? '';
  return {
    status: normalized(actual) === normalized(input.expected) ? 'pass' : 'fail',
    reason: normalized(actual) === normalized(input.expected) ? strings.passReason : strings.failReason,
    table, rowIndex: selected.index, columnIndex, actual
  };
}

function addCell(row, tag, text, className = '') {
  const cell = document.createElement(tag);
  if (className) cell.className = className;
  cell.textContent = text || '\u00a0';
  row.append(cell);
}

function renderTable(table, finding) {
  tablePreview.replaceChildren();
  if (!table) {
    const message = document.createElement('p');
    message.className = 'empty-table';
    message.textContent = copy[currentLanguage()].emptyPreview;
    tablePreview.append(message);
    return;
  }
  const visibleRows = table.rows.slice(0, 16);
  const tableElement = document.createElement('table');
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  table.headers.slice(0, 16).forEach((header, index) => addCell(headRow, 'th', header, index === finding?.columnIndex ? 'selected-column' : ''));
  head.append(headRow);
  tableElement.append(head);
  const body = document.createElement('tbody');
  visibleRows.forEach((cells, rowIndex) => {
    const row = document.createElement('tr');
    cells.slice(0, 16).forEach((value, columnIndex) => {
      const selected = finding && rowIndex === finding.rowIndex && columnIndex === finding.columnIndex;
      addCell(row, 'td', value, selected ? 'selected-cell' : '');
    });
    body.append(row);
  });
  tableElement.append(body);
  tablePreview.append(tableElement);
}

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function runCheck() {
  const language = currentLanguage();
  const strings = copy[language];
  const input = {
    markdown: markdown.value,
    table: Number(document.querySelector('#table-number').value),
    rowKey: document.querySelector('#row-key').value,
    rowValue: document.querySelector('#row-value').value,
    column: document.querySelector('#column-name').value,
    expected: document.querySelector('#expected-value').value
  };
  const finding = evaluate(parseMarkdown(input.markdown), input);
  result.dataset.state = finding.status;
  setText('#status-badge', strings[`${finding.status}Badge`]);
  setText('#result-heading', finding.status === 'pass' ? strings.passTitle : finding.status === 'fail' ? strings.failTitle : strings.unknownTitle);
  setText('#result-reason', finding.reason);
  setText('#expected-display', input.expected || '\u2014');
  setText('#observed-display', finding.actual ?? '\u2014');
  setText('#table-label', strings.table + (Number.isInteger(input.table) && input.table > 0 ? ` ${input.table}` : ''));
  renderTable(finding.table, finding);
}

markdown.value = SAMPLE_MARKDOWN;
form.addEventListener('submit', event => {
  event.preventDefault();
  runCheck();
});
document.querySelector('#load-sample').addEventListener('click', () => {
  document.querySelector('#table-number').value = '1';
  document.querySelector('#row-key').value = 'Material';
  document.querySelector('#row-value').value = 'Cedar mulch';
  document.querySelector('#column-name').value = 'Unit price ($)';
  document.querySelector('#expected-value').value = '64.00';
  markdown.value = SAMPLE_MARKDOWN;
  runCheck();
});
languageButton.addEventListener('click', () => {
  const language = currentLanguage() === 'en' ? 'zh' : 'en';
  document.documentElement.dataset.lang = language;
  document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
  languageButton.textContent = language === 'en' ? '中文' : 'English';
  runCheck();
});
runCheck();
