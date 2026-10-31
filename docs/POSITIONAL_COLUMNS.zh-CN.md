# PDF 里对齐的列，为什么在文本里跑偏了？

同一张表跨页时，即使两页文字的 PDF 物理 x 坐标相同，`pdftotext -layout` 输出的字符位置也可能不同。如果直接沿用第一页的字符切分位置，后续页就可能读错列。本案例参考了 [anthropics/skills #1078](https://github.com/anthropics/skills/issues/1078) 提出的问题；核对时已有[文档修改申请](https://github.com/anthropics/skills/pull/1567)等待审核。

[原创合成 PDF](../fixtures/positional-two-page.pdf) 的两页都将 `Cedar`、`12.5`、`64.00` 分别放在 x = 50、260、430 点；第一页页眉短，第二页页眉较长。数据完全虚构，表格没有边框。

在 macOS arm64 和 Poppler `pdftotext` 26.05.0 上，`-layout` 输出中 `12.5` 和 `64.00` 的零起始字符位置，第一页是 **14 / 21**，第二页变成 **47 / 74**；pdfplumber 0.11.9 读出的物理 x 坐标在两页相同。如果在提取前只选择表格区域、排除页眉，两页的字符位置在此样本中都为 **10 / 17**。已经输出的文本再删除页眉，无法改变已生成的字符位置。

这只是一份受控样本，不代表所有 PDF、Poppler 版本或基于坐标的解析器都会如此。PDF 坐标本身也可能变化：需要核对实际原件中的关键行和列。本案例独立于原有 3 份转换器实测样本，旧版 v0.1.0 ZIP 不包含它。

## 复现

需要 Poppler 的 `pdftotext` 和 Python 3.10+；在仓库根目录运行：

```sh
pdftotext -layout fixtures/positional-two-page.pdf - | python3 -c 'import sys; p=sys.stdin.read().split("\f"); print([[(s.index("12.5"),s.index("64.00")) for s in page.splitlines() if "Cedar" in s] for page in p if page.strip()])'
pdftotext -r 72 -layout -x 0 -y 60 -W 612 -H 500 fixtures/positional-two-page.pdf - | python3 -c 'import sys; p=sys.stdin.read().split("\f"); print([[(s.index("12.5"),s.index("64.00")) for s in page.splitlines() if "Cedar" in s] for page in p if page.strip()])'
```

如需查看 PDF 物理坐标，在虚拟环境安装 `pdfplumber==0.11.9`，然后运行：

```sh
python3 -c 'import pdfplumber; p=pdfplumber.open("fixtures/positional-two-page.pdf"); print([[(w["text"],w["x0"]) for w in page.extract_words() if w["text"] in ("Cedar","12.5","64.00")] for page in p.pages]); p.close()'
```

重建 PDF 可安装 `reportlab==4.4.9`，再运行 `python3 scripts/generate_positional.py --out /tmp/positional-two-page.pdf`，输出路径必须不存在。仓库中 PDF 的 SHA-256 是 `0938b3d14f6acbaeb0ecb40395fe6ce843d338f57117c60c1b591b9062b1b50d`。

PDF Table Traps 本身不会解析 PDF 文本或推断这些列的位置。将文件转换为支持的 Markdown 或 JSON 表格后，才可以用现有检查器把选定单元格与原件中核实的值进行比较。
