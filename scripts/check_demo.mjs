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
    const types = { '.html': 'text/html', '.png': 'image/png', '.pdf': 'application/pdf', '.json': 'application/json' };
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
  assert.deepEqual(external, []); assert.deepEqual(errors, []);
  const result = { status: 'pass', panels: 6, downloaded_pdf_sha256: sha(await readFile(pdf)), external_http_requests: external.length, page_errors: errors.length, mobile_overflow: false, output, screenshotFolder };
  await writeFile(path.join(output, 'result.json'), JSON.stringify(result, null, 2) + '\n');
  process.stdout.write(JSON.stringify(result) + '\n');
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
