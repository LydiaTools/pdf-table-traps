# 检查 pdf-inspector 转换后的关键值

[English](PDF_INSPECTOR.md) · [原始测量文件](../measured/pdf-inspector-1.25.2/) · [主要上手说明](../README.zh-CN.md)

这是一份接入示例。[Firecrawl 的 pdf-inspector](https://github.com/firecrawl/pdf-inspector) 已经能在本地解析 PDF、检测表格；我们用独立检查器核对事先指定的值是否仍属于指定行和列。

本次使用 **pdf-inspector 1.25.2** 的默认 `process_pdf(path)`，读取相同的三份原创 PDF；没有提供 OCR 运行库、凭据或远程服务。已保存的结果来自 macOS arm64 / Python 3.12，CI 另在 Ubuntu 实跑，具体以各次运行记录为准。

| 样本 | 指定检查结果 | 观察到的情况 |
| --- | --- | --- |
| 有框表格 | 4 项匹配 | 指定的行、列、值保持对应。 |
| 无框且名称跨行 | 1 项匹配、3 项不匹配 | 单价列中是数量 `12.5`、`3.25`、`1.8`，而非 `64.00`、`88.00`、`145.00`；单价数字仍出现在其他位置。 |
| 纯正文 | 1 项匹配 | 按预期没有检测到支持的表格，不代表正文全部正确。 |

成功和失败的原始输出都保留。这三例不能推导通用准确率、OCR 效果或调参后的表现，也不能用于诊断其他用户文件的错误原因。

## 复现

从当前源码检出目录，在 Python 3.10+ 虚拟环境中运行：

```sh
python -m pip install --only-binary=:all: -r requirements-inspector.txt
python -m scripts.run_pdf_inspector --output artifacts/inspector-run --expect-observed
```

输出目录必须是新目录。已记录的结果全部复现时，runner 返回 `0`，其中包含预期会失败的无框样本；这不表示三个文件的转换结果都正确。结果改变时停止供人工检查。示例固定转换器版本；安装命令只接受适用平台的二进制 wheel，不进行源码编译或 OCR 模型下载。

单独查看检查器如何阻止错误结果进入流水线：

```sh
python -m table_traps check --input measured/pdf-inspector-1.25.2/borderless.pdf-inspector.md --rules cases/borderless.json
```

预期退出码为 **1**，三处关键值不匹配。换为 `ruled.pdf-inspector.md` 和 `cases/ruled.json`，正确对照返回 **0**。检查自己的文件时，要依据自己的原件编写预期值，不能照用园艺样本数据。

现有六面板网页和 v0.1.0 发行包仍为最初两条提取路径的固定快照；本接入示例在当前源码分支提供。不代表 pdf-inspector 官方背书。
