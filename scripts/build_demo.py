"""Build an offline report viewer from measured outputs; does not run converters."""
import argparse
import json
from pathlib import Path
import shutil

from table_traps.core import evaluate, parse_input
from table_traps.report import bi, document, esc, section

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', type=Path, required=True, help='Direct source-PDF excerpt renders, named ruled.png etc.')
    parser.add_argument('--output', type=Path, default=ROOT/'docs')
    args = parser.parse_args()
    output = args.output
    for folder in ['assets', 'fixtures', 'reports']:
        (output/folder).mkdir(parents=True, exist_ok=True)
    cases = [('ruled', 'Ruled table', '有边框表格'), ('borderless', 'Wrapped row', '跨行名称'), ('prose', 'Prose control', '正文对照')]
    body = ['<div class="intro"><p>' + bi('All the numbers survived. Did they keep the right headers?', '数字都保留了，还对应着正确的列名吗？') + '</p></div>',
            '<div class="toolbar"><nav aria-label="Sample">']
    for i, (name, en, zh) in enumerate(cases):
        body.append(f'<button type="button" data-case="{name}" aria-pressed="{str(i == 0).lower()}">{bi(en, zh)}</button>')
    body += ['</nav><nav aria-label="Engine"><button type="button" data-engine="markitdown" aria-pressed="true">MarkItDown 0.1.8</button>',
             '<button type="button" data-engine="pdfplumber" aria-pressed="false">pdfplumber 0.11.10</button></nav></div>',
             '<div class="notice"><p>' + bi('Measured synthetic outputs, captured 20 Oct 2026. This page views saved results; it does not run a parser or upload your files. Checks cover only the supplied expectations.', '2026 年 10 月 20 日实测合成样本。本页仅查看已保存的结果，不运行转换器，也不上传文件。检查只覆盖明确提供的预期值。') + '</p></div><main>']
    for name, _, _ in cases:
        shutil.copy2(args.images/f'{name}.png', output/'assets'/f'{name}.png')
        shutil.copy2(ROOT/'fixtures'/f'{name}.pdf', output/'fixtures'/f'{name}.pdf')
        rules = json.loads((ROOT/'cases'/f'{name}.json').read_text())
        for engine, extension, fmt in [('markitdown', 'md', 'markdown'), ('pdfplumber', 'json', 'tables-json')]:
            filename = f'{name}.{engine}.{extension}'
            raw = (ROOT/'measured'/filename).read_text()
            parsed = parse_input(raw, fmt)
            report = evaluate(parsed, rules, filename)
            (output/'reports'/f'{name}.{engine}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            hidden = '' if (name, engine) == ('ruled', 'markitdown') else ' hidden'
            body.append(f'<section class="report" data-panel-case="{name}" data-panel-engine="{engine}"{hidden}>')
            body.append(section(report, parsed, raw, f'assets/{name}.png', f'fixtures/{name}.pdf'))
            body.append(f'<p><a href="reports/{name}.{engine}.json" download>{bi("Download check results (JSON)", "下载检查结果（JSON）")}</a></p></section>')
    body += ['</main><section class="handoff" aria-labelledby="use-the-kit"><h2 id="use-the-kit">',
             bi('Use these checks before your next parser upgrade.', '下次升级转换器前，用这些样本先检查一遍。'),
             '</h2><p>' + bi('Get the source and fixtures to run a local check. For your own output, supply values you have checked against the original document.', '获取源码与样本，在本机运行检查。检查自己的输出时，请先对照原件确认预期值。') + '</p>',
             '<nav aria-label="Use PDF Table Traps">',
             '<a class="primary" href="https://github.com/LydiaTools/pdf-table-traps#try-a-known-failure">' + bi('Source & quick start', '源码与快速上手') + '</a>',
             '<a href="https://github.com/LydiaTools/pdf-table-traps/releases/tag/v0.1.0">' + bi('Download v0.1.0 kit', '下载 v0.1.0 测试集') + '</a>',
             '<a href="https://github.com/LydiaTools/pdf-table-traps#check-your-own-output">' + bi('Write your own rule', '为自己的文件编写规则') + '</a>',
             '</nav></section>']
    script = """let currentCase='ruled',currentEngine='markitdown';function select(){document.querySelectorAll('[data-panel-case]').forEach(p=>p.hidden=!(p.dataset.panelCase===currentCase&&p.dataset.panelEngine===currentEngine));document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===currentCase)));document.querySelectorAll('[data-engine]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.engine===currentEngine)));}document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{currentCase=b.dataset.case;select();}));document.querySelectorAll('[data-engine]').forEach(b=>b.addEventListener('click',()=>{currentEngine=b.dataset.engine;select();}));"""
    html = document(''.join(body), 'PDF Table Traps | Do values keep their headers?')
    public_style = '.handoff{max-width:1376px;margin:0 auto 28px;padding:24px 32px;background:#eaf0e9;border-block:1px solid #becbbf}.handoff h2{font-size:21px;line-height:1.3;margin:0 0 10px;max-width:55ch}.handoff p{max-width:78ch;margin:0 0 18px}.handoff nav{align-items:center;gap:18px}.handoff .primary{display:inline-block;background:#173d34;color:white;padding:10px 16px;border-radius:5px;text-decoration:none}@media(max-width:800px){.handoff{margin-inline:20px;padding:20px}.handoff nav{align-items:flex-start;flex-direction:column;gap:14px}}'
    html = html.replace('</style>', public_style + '</style>')
    html = html.replace('</body>', '<script>' + script + '</script></body>')
    (output/'index.html').write_text(html, encoding='utf-8')
    print(json.dumps({'site': str(output), 'cases': 3, 'reports': 6}))


if __name__ == '__main__':
    main()
