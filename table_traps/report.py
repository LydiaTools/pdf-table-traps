import html


def esc(value):
    return html.escape(str(value), quote=True)


STYLE = """
:root{color-scheme:light;--ink:#173d34;--soft:#eaf0e9;--paper:#fafcf8;--line:#becbbf;--fail:#a52f37;--pass:#246546;--unknown:#846013}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 'Avenir Next','Segoe UI',sans-serif}a{color:inherit;text-underline-offset:3px}button,select{font:inherit;color:inherit}button{background:white;border:1px solid var(--line);padding:8px 14px;cursor:pointer;border-radius:5px}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #31695b;outline-offset:3px}button[aria-pressed=true]{background:var(--ink);color:white;border-color:var(--ink)}header{max-width:1440px;margin:auto;padding:24px 32px 16px;display:flex;justify-content:space-between;gap:16px;align-items:center}h1{font-size:25px;letter-spacing:-.6px;margin:0}header p{margin:3px 0 0;color:#50665c}nav{display:flex;gap:8px;flex-wrap:wrap}.intro{max-width:1440px;padding:0 32px 22px;margin:auto;font-size:19px;max-inline-size:1440px}.intro p{max-width:76ch;margin:0}.toolbar{max-width:1440px;margin:auto;padding:0 32px 18px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}.notice{background:var(--soft);border-block:1px solid var(--line);padding:12px 32px;font-size:13px}.notice p{max-width:1380px;margin:auto}.report{max-width:1440px;margin:auto;padding:24px 32px}.headline{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:18px}.headline h2{font-size:19px;margin:0}.headline p{font-size:13px;color:#50665c;margin:4px 0 0}.status{border:1px solid currentColor;padding:3px 10px;border-radius:4px;font-size:13px;font-weight:700;white-space:nowrap}.fail{color:var(--fail)}.pass{color:var(--pass)}.unknown{color:var(--unknown)}.review{display:grid;grid-template-columns:minmax(280px,.9fr) minmax(0,1.15fr);gap:28px;align-items:start}.source{border:1px solid var(--line);background:white}.source .caption{padding:10px 14px;border-bottom:1px solid var(--line);font-size:13px;display:flex;justify-content:space-between;gap:16px}.source img{display:block;width:100%;height:auto;max-height:760px;object-fit:contain;object-position:top}.checks{min-width:0}.check{padding:13px 0;border-bottom:1px solid var(--line)}.check:first-child{border-top:2px solid var(--ink)}.check-title{display:flex;align-items:baseline;justify-content:space-between;gap:12px}.check h3{font-size:14px;font-weight:700;margin:0;overflow-wrap:anywhere}.values{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}.value{padding:9px 12px;background:white;border:1px solid var(--line);min-width:0}.value span{font-size:12px;display:block;color:#50665c}.value strong{font-size:19px;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}.reason{margin:5px 0 0;font-size:12px;color:#50665c}.extracted{margin-top:24px}.extracted h3{font-size:14px;margin:0 0 8px}.table-scroll{overflow:auto;border:1px solid var(--line);background:white}table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;border-bottom:1px solid #d9e1d7;border-right:1px solid #d9e1d7;padding:8px 10px;white-space:pre-wrap;min-width:70px}th{background:var(--soft);font-weight:700}td.flag{background:#f9e2df;color:#7e242c;font-weight:700;outline:2px solid #b25050;outline-offset:-2px}.table-label{font-size:12px;margin:12px 0 5px;color:#50665c}details{margin-top:16px}summary{cursor:pointer;font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3ec;padding:12px;font:12px/1.6 'SFMono-Regular',Consolas,monospace}.scope{font-size:12px;color:#50665c;margin-top:18px;max-width:90ch}footer{max-width:1440px;margin:0 auto;padding:16px 32px 28px;border-top:1px solid var(--line);font-size:13px}[hidden]{display:none!important}html[data-lang=zh] [data-en],html[data-lang=en] [data-zh]{display:none}
@media(max-width:800px){header{align-items:flex-start;padding:20px}header nav{justify-content:flex-end}.intro,.toolbar{padding-left:20px;padding-right:20px}.intro{font-size:17px}.report{padding:20px}.review{grid-template-columns:1fr;gap:20px}.source img{max-height:580px}.notice{padding:12px 20px}.headline{align-items:flex-start}h1{font-size:22px}footer{padding:20px}}
"""


def bi(en, zh):
    return f'<span data-en>{esc(en)}</span><span data-zh>{esc(zh)}</span>'


def section(report, parsed, raw="", source_image=None, pdf_link=None):
    labels = {"pass": ("Matches", "检查匹配"), "fail": ("Mismatch", "检查不符"), "unknown": ("Needs review", "需要核查")}
    count = report["counts"]
    count_label = bi(f'{count["fail"]} mismatches / {count["unknown"]} unknown / {count["pass"]} matches',
                     f'{count["fail"]} 项不符 / {count["unknown"]} 项需核查 / {count["pass"]} 项匹配')
    out = [f'<div class="headline"><div><h2>{esc(report["suite"])}</h2><p>{esc(report["source_name"])}<br>{count_label}</p></div>',
           f'<div class="status {report["status"]}">{bi(*labels[report["status"]])}</div></div>', '<div class="review"' + (' style="display:block"' if not source_image else '') + '>']
    if source_image:
        out += ['<div class="source"><div class="caption">' + bi("Synthetic PDF excerpt", "合成 PDF 原件局部"),
                f'<a href="{esc(pdf_link)}" download>{bi("Download PDF", "下载 PDF")}</a>' if pdf_link else '',
                f'</div><img src="{esc(source_image)}" alt="Original synthetic {esc(report["suite"])} PDF page"></div>']
    out.append('<div class="checks">')
    flags = set()
    ordered = sorted(report["findings"], key=lambda item: ({"fail": 0, "unknown": 1, "pass": 2}[item["status"]], item["kind"] == "table_count"))
    for index, finding in enumerate(ordered):
        if index == 1:
            out.append('<details class="other-checks"><summary>' + bi(f'Inspect the other {len(ordered)-1} checks', f'查看其余 {len(ordered)-1} 项检查') + '</summary>')
        selector = finding["selector"]
        title = "Table count" if finding["kind"] == "table_count" else f'{selector["row"]} / {selector["column"]}'
        if finding["status"] == "fail" and "location" in finding:
            loc = finding["location"]; flags.add((loc["table"], loc["row"], loc["column"]))
        actual = finding["actual"] if finding["actual"] is not None else "—"
        reasons = {
            'cell_match': ('Value matches this row and header.', '值与指定行、列的预期一致。'),
            'cell_mismatch': ('Value under this header differs from the expectation.', '该列下的值与预期不同。'),
            'table_count_match': ('Supported table count matches.', '支持的表格数量与预期一致。'),
            'table_count_mismatch': ('Supported table count differs from the expectation.', '支持的表格数量与预期不同。'),
            'table_missing': ('The selected table was not found.', '未找到指定表格。'),
            'header_missing_or_ambiguous': ('The header is missing or is not unique.', '列名缺失或不唯一。'),
            'row_missing_or_ambiguous': ('The row label is missing or is not unique.', '行名称缺失或不唯一。'),
            'ragged_row': ('This row has a different number of cells.', '该行的单元格数量不一致。'),
            'unsupported_structure': ('Unsupported or empty structure needs review.', '结构不支持或为空，需要核查。'),
        }
        out += [f'<div class="check"><div class="check-title"><h3>{esc(title)}</h3><span class="{finding["status"]}">{bi(*labels[finding["status"]])}</span></div>',
                '<div class="values"><div class="value">' + bi("Expected", "预期值") + f'<strong>{esc(finding["expected"])}</strong></div>',
                '<div class="value">' + bi("Observed", "观察值") + f'<strong>{esc(actual)}</strong></div></div>',
                '<p class="reason">' + bi(*reasons[finding["reason"]]) + '</p></div>']
    if len(ordered) > 1:
        out.append('</details>')
    out.append('<div class="extracted"><h3>' + bi("Parsed output tables", "解析后的输出表格") + '</h3>')
    if not parsed["tables"]:
        out.append('<p>' + bi("No supported Markdown/JSON table found.", "未发现支持的 Markdown / JSON 表格。") + '</p>')
    for tidx, table in enumerate(parsed["tables"], 1):
        out.append(f'<p class="table-label">{bi("Table", "表格")} {tidx}</p><div class="table-scroll"><table>')
        for ridx, row in enumerate(table):
            tag = 'th' if ridx == 0 else 'td'
            out.append('<tr>')
            for cidx, value in enumerate(row):
                flag = ' class="flag"' if (tidx, ridx, cidx) in flags else ''
                out.append(f'<{tag}{flag}>{esc(value) if value else "&nbsp;"}</{tag}>')
            out.append('</tr>')
        out.append('</table></div>')
    out += ['</div>', '<details><summary>' + bi("Read the unmodified converter output", "查看未经修改的转换输出") + '</summary>',
            f'<pre>{esc(raw)}</pre></details>', '<p class="scope">' + bi(report["scope"], "仅检查使用者提供的预期值；采用 NFC 和空白规范化。不代表全文正确、独立来源验证、OCR 或认证。") + '</p>', '</div></div>']
    return ''.join(out)


LANGUAGE_SCRIPT = """document.getElementById('language').addEventListener('click',()=>{const lang=document.documentElement.dataset.lang==='en'?'zh':'en';document.documentElement.dataset.lang=lang;document.documentElement.lang=lang==='zh'?'zh-CN':'en';document.getElementById('language').textContent=lang==='en'?'中文':'English';});"""


def document(body, title="PDF Table Traps report"):
    return '<!doctype html><html lang="en" data-lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data: \'self\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>' + esc(title) + '</title><style>' + STYLE + '</style></head><body><header><div><h1>PDF Table Traps</h1><p>' + bi("Check the relationship, not just the numbers.", "不只核对数字，还要核对数字的位置。") + '</p></div><nav><button id="language" type="button">中文</button><a href="https://github.com/LydiaTools/pdf-table-traps">GitHub</a></nav></header>' + body + '<footer>' + bi("Original synthetic cases. Small regression kit, not a representative accuracy benchmark.", "原创合成样本。小型回归测试集，不代表总体准确率。") + '</footer><script>' + LANGUAGE_SCRIPT + '</script></body></html>'


def render_report(report, parsed, raw):
    return document('<main class="report">' + section(report, parsed, raw) + '</main>')
