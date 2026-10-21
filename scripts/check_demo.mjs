import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, mkdir, mkdtemp, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
await mkdir(path.join(root, 'artifacts'), { recursive: true });
const output = await mkdtemp(path.join(root, 'artifacts', 'browser-'));
const screenshotFolder = process.env.TABLE_TRAPS_SCREENSHOT_DIR || output;
await mkdir(screenshotFolder, { recursive: true });
const standalone = path.join(output, 'standalone.html');
const cli = spawnSync(process.env.TABLE_TRAPS_PYTHON || 'python3', ['-m', 'table_traps', 'check', '--input', 'measured/ruled.markitdown.md', '--rules', 'cases/ruled.json', '--html', standalone], { cwd: root, encoding: 'utf8' });
assert.equal(cli.status, 1, cli.stderr);
const server = createServer(async (req, res) => {
  try {
    assert.equal(req.method, 'GET');
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const filename = pathname === '/_standalone.html' ? standalone : path.resolve(root, 'docs', '.' + (pathname === '/' ? '/index.html' : pathname));
    assert.ok(filename === standalone || filename.startsWith(path.join(root, 'docs') + path.sep));
    const data = await readFile(filename);
    const types = { '.html': 'text/html', '.png': 'image/png', '.pdf': 'application/pdf', '.json': 'application/json', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8' };
    res.writeHead(200, { 'content-type': types[path.extname(filename)] || 'text/plain' }); res.end(data);
  } catch { res.writeHead(404); res.end('Not found'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL === 'chromium' ? undefined : process.env.BROWSER_CHANNEL || 'chrome', headless: true });
const external = [], errors = [];
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1050 }, deviceScaleFactor: 1 });
  context.on('request', req => { if (!req.url().startsWith(base + '/')) external.push(req.url()); });
  const page = await context.newPage();
  page.on('pageerror', err => errors.push(err.message));
  await page.goto(base);
  const panel = () => page.locator('.report:not([hidden])');
  assert.equal(await panel().count(), 1);
  assert.equal(await panel().locator('.check').first().locator('.value strong').nth(0).innerText(), '64.00');
  assert.equal(await panel().locator('.check').first().locator('.value strong').nth(1).innerText(), '12.5');
  assert.equal(await panel().locator('td.flag').count(), 3);
  for (const sample of ['ruled', 'borderless', 'prose']) {
    for (const engine of ['markitdown', 'pdfplumber']) {
      await page.locator(`[data-case="${sample}"]`).click();
      await page.locator(`[data-engine="${engine}"]`).click();
      const expected = JSON.parse(await readFile(path.join(root, 'docs', 'reports', `${sample}.${engine}.json`), 'utf8'));
      assert.ok(await panel().locator('.headline .status').evaluate((el, status) => el.classList.contains(status), expected.status));
      assert.equal(await panel().locator('.check').count(), expected.findings.length);
    }
  }
  await page.locator('[data-case="ruled"]').click();
  await page.locator('[data-engine="markitdown"]').click();
  const downloadPromise = page.waitForEvent('download');
  await panel().locator('.source a[download]').click();
  const download = await downloadPromise;
  const pdf = path.join(output, 'downloaded.pdf'); await download.saveAs(pdf);
  const sha = data => createHash('sha256').update(data).digest('hex');
  assert.equal(sha(await readFile(pdf)), sha(await readFile(path.join(root, 'fixtures', 'ruled.pdf'))));
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(screenshotFolder, 'report-en.png'), fullPage: true });
  await page.locator('#language').click();
  assert.equal(await page.locator('html').getAttribute('lang'), 'zh-CN');
  await page.screenshot({ path: path.join(screenshotFolder, 'report-zh.png'), fullPage: true });
  const mobile = await context.newPage();
  await mobile.setViewportSize({ width: 390, height: 844 });
  await mobile.goto(base); await mobile.locator('#language').click();
  await mobile.evaluate(() => document.fonts.ready);
  assert.equal(await mobile.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  assert.equal(await mobile.locator('header').count(), 1);
  await mobile.screenshot({ path: path.join(screenshotFolder, 'mobile-top.png') });
  await mobile.locator('.report:not([hidden]) .check').first().scrollIntoViewIfNeeded();
  await mobile.screenshot({ path: path.join(screenshotFolder, 'mobile-check.png') });
  await page.goto(base + '/_standalone.html');
  assert.equal(await page.locator('.value strong').nth(0).innerText(), '64.00');
  await page.locator('#language').click();
  assert.equal(await page.locator('html').getAttribute('lang'), 'zh-CN');

  const playground = await context.newPage();
  await playground.setViewportSize({ width: 1440, height: 1000 });
  playground.on('pageerror', err => errors.push(err.message));
  await playground.goto(base + '/try.html');
  const finding = playground.locator('#result');
  assert.equal(await finding.getAttribute('data-state'), 'fail');
  assert.equal(await playground.locator('#expected-display').innerText(), '64.00');
  assert.equal(await playground.locator('#observed-display').innerText(), '12.5');
  assert.equal(await playground.locator('td.selected-cell').innerText(), '12.5');
  assert.deepEqual(await playground.locator('.comparison span[data-en]').evaluateAll(items => items.map(el => getComputedStyle(el).display !== 'none')), [true, true]);
  assert.deepEqual(await playground.locator('.comparison span[data-zh]').evaluateAll(items => items.map(el => getComputedStyle(el).display !== 'none')), [false, false]);
  await playground.screenshot({ path: path.join(screenshotFolder, 'playground-en.png'), fullPage: true });
  await playground.locator('#language').click();
  assert.equal(await playground.locator('html').getAttribute('lang'), 'zh-CN');
  assert.equal(await playground.locator('#result-heading').innerText(), '单元格值不符。');
  assert.deepEqual(await playground.locator('.comparison span[data-zh]').evaluateAll(items => items.map(el => getComputedStyle(el).display !== 'none')), [true, true]);
  assert.deepEqual(await playground.locator('.comparison span[data-en]').evaluateAll(items => items.map(el => getComputedStyle(el).display !== 'none')), [false, false]);
  await playground.screenshot({ path: path.join(screenshotFolder, 'playground-zh.png'), fullPage: true });
  await playground.locator('#language').click();

  await playground.locator('#row-key').fill('Item');
  await playground.locator('#row-value').fill('Cedar');
  await playground.locator('#column-name').fill('Unit price');
  await playground.locator('#expected-value').fill('64.00');
  await playground.locator('#markdown').fill('| Item | Unit price |\n| --- | --- |\n| Pine | 18.00 |\n| Cedar | 64.00 |');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'pass', 'row order must not affect a keyed check');

  await playground.locator('#row-key').fill('row_key');
  await playground.locator('#row-value').fill('user_id_42');
  await playground.locator('#column-name').fill('score_value');
  await playground.locator('#expected-value').fill('40_000');
  await playground.locator('#markdown').fill('| row_key | score_value |\n| --- | --- |\n| user_id_42 | 40_000 |');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'pass', 'underscores inside identifiers and values must stay literal');

  await playground.locator('#row-key').fill('Material');
  await playground.locator('#row-value').fill('Cedar mulch');
  await playground.locator('#column-name').fill('Unit price');
  await playground.locator('#expected-value').fill('64.00');
  await playground.locator('#markdown').fill('| Material | Unit price |\n| --- | --- |\n| **Cedar mulch** | **64.00** |');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'pass', 'space-delimited emphasis must preserve the cell value');

  await playground.locator('#markdown').fill('| Material | Unit price |\n| --- |\n| Cedar | 64.00 |');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'unknown', 'a delimiter row with a different column count must fail closed');

  await playground.locator('#markdown').fill('| Material | Unit price |\n| --- | --- |\n| Cedar mulch | 64 |');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'fail', 'numeric formatting differences must remain visible');

  await playground.locator('#row-value').fill('Cedar | bark');
  await playground.locator('#markdown').fill('| Material | Unit price |\n| --- | --- |\n| `Cedar | bark` | 64.00 |');
  await playground.locator('#row-key').fill('Material');
  await playground.locator('#column-name').fill('Unit price');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'pass', 'a pipe inside an inline code span must stay in its cell');

  await playground.locator('#markdown').fill('```md\n| Material | Unit price |\n| --- | --- |\n| Cedar | 64.00 |\n```');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'unknown', 'tables inside code fences are not parsed');

  await playground.locator('#markdown').fill('| Material | Unit price |\n| --- | --- |\n| <img src=x onerror=alert(1)> | 64.00 |');
  await playground.locator('#check-form button[type="submit"]').click();
  assert.equal(await finding.getAttribute('data-state'), 'unknown', 'HTML cells must fail closed');
  assert.equal(await playground.locator('#table-preview img').count(), 0, 'user-supplied text must never become HTML');
  await playground.setViewportSize({ width: 390, height: 844 });
  await playground.goto(base + '/try.html');
  assert.equal(await playground.locator('#result').getAttribute('data-state'), 'fail');
  const playgroundMobileOverflow = await playground.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  assert.equal(playgroundMobileOverflow, false, 'the playground must fit a 390px viewport');
  await playground.screenshot({ path: path.join(screenshotFolder, 'playground-mobile.png'), fullPage: true });

  assert.deepEqual(external, []); assert.deepEqual(errors, []);
  const result = { status: 'pass', panels: 6, playground_cases: 9, downloaded_pdf_sha256: sha(await readFile(pdf)), external_http_requests: external.length, page_errors: errors.length, mobile_overflow: playgroundMobileOverflow, output, screenshotFolder };
  await writeFile(path.join(output, 'result.json'), JSON.stringify(result, null, 2) + '\n');
  process.stdout.write(JSON.stringify(result) + '\n');
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
