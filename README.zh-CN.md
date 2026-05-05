# Patch SVG Icon to Font

> English version: [README.md](README.md)

把 SVG 图标 patch 到 TrueType / OpenType 字体的指定码位上，常用于给编程字体（如 Nerd Fonts）添加自定义图标。

## 展示

在打补丁后的编程字体中使用 LLM 服务商图标，覆盖完整的终端工作流。

### 图标总览

全部 26 个 patched 图标一览。

| 暗色主题 | 亮色主题 |
|:---:|:---:|
| <img src="assets/demo_dark.png" width="640"> | <img src="assets/demo_light.png" width="640"> |

### 使用场景

**Tmux 状态栏** —— 在状态栏中直接用图标实时追踪各模型的 API 花费。

| 暗色主题 | 亮色主题 |
|:---:|:---:|
| <img src="assets/tmux_bar_dark.png" width="320"> | <img src="assets/tmux_bar_light.png" width="320"> |

**模型选择器** —— 在交互式 TUI 中使用图标快速切换服务商。

| 暗色主题 | 亮色主题 |
|:---:|:---:|
| <img src="assets/api_choser_dark.png" width="320"> | <img src="assets/api_choser_light.png" width="320"> |

**API 花费看板** —— 完整的终端看板，带图标支持，兼容暗色和亮色主题。

| 暗色主题 | 亮色主题 |
|:---:|:---:|
| <img src="assets/api_tracker_dark.png" width="320"> | <img src="assets/api_tracker_light.png" width="320"> |

## 依赖

- FontForge，且需要 Python 绑定 `fontforge`

安装方式因平台而异：

```bash
# macOS
brew install fontforge

# Ubuntu / Debian
sudo apt-get install fontforge python3-fontforge

# Fedora
sudo dnf install fontforge python3-fontforge
```

验证安装：

```bash
python3 -c "import fontforge; print(fontforge.version())"
```

## 快速开始

```bash
git clone git@github.com:refiget/llm-icon-font-patcher.git
cd llm-icon-font-patcher/
mkdir icons/
mkdir font/
```

把你的 SVG 图标放进 `icons/`，把 `.ttf` 字体文件放进 `font/`。你可以从 [`lobe-icons/packages/static-svg/`](https://github.com/lobehub/lobe-icons) 下载图标 SVG。

最小目录结构如下：

```text
.
├── font/
├── icons/
├── main.py
└── patch_svg_to_font.py
```

运行批处理脚本：

```bash
python3 main.py
```

处理完成后，生成的字体文件会输出到 `out/` 目录。

## 映射规则

`./icons` 目录下的 SVG 会先按文件名排序，然后依次映射到 Unicode Private Use Area（PUA）：

- 起始码位：`U+E900`，可通过 `--start-codepoint` 修改
- 第 1 个图标 -> `U+E900`
- 第 2 个图标 -> `U+E901`
- 以此类推

当前这组 `icons/` 共 26 个图标，覆盖范围为：

- `U+E900` ~ `U+E919`

安装生成字体后，在支持 PUA 的编辑器或终端里输入 `\uE900`，即可看到 `icons/` 中第一个图标。

## 命令行说明

### `patch_svg_to_font.py`

```text
usage: patch_svg_to_font.py [-h] --font FONT --svg SVG --codepoint CODEPOINT --output OUTPUT [--proportional]

options:
  -h, --help            show this help message and exit
  -f FONT, --font FONT  Input font file (.ttf/.otf)
  -s SVG, --svg SVG     Input SVG icon file
  -c CODEPOINT, --codepoint CODEPOINT
                        Target Unicode codepoint (e.g. 0xE900, U+E900, or E900)
  -o OUTPUT, --output OUTPUT
                        Output font file path
  -p, --proportional    Use proportional width instead of forcing monospace width
```

示例：

```bash
python3 patch_svg_to_font.py \
  --font "/path/to/JetBrainsMono-Regular.ttf" \
  --svg deepseek.svg \
  --codepoint 0xE900 \
  --output JetBrainsMono-DeepSeek.ttf
```

如果目标字体是比例字体，可以加上 `--proportional`：

```bash
python3 patch_svg_to_font.py \
  --font "/path/to/SomeProportionalFont.ttf" \
  --svg deepseek.svg \
  --codepoint U+E900 \
  --output SomeProportionalFont-Patched.ttf \
  --proportional
```

### `main.py`

```bash
python3 main.py \
  --font-dir font \
  --icon-dir icons \
  --out-dir out \
  --start-codepoint 0xE900
```

参数说明：

- `--font-dir`：源字体目录
- `--icon-dir`：SVG 图标目录
- `--out-dir`：生成字体的输出目录
- `--start-codepoint`：起始 PUA 码位，默认 `0xE900`
- `--proportional`：使用比例宽度，不强制等宽

## 脚本做了什么

1. 读取字体指标，例如 `em`、`capHeight` 和标准字宽，避免硬编码这些值。
2. 使用 FontForge 将 SVG 轮廓导入到字体 glyph 中。
3. 按 `capHeight × 0.95` 缩放图标，让它在视觉上和大写字母更协调。
4. 将 glyph 左对齐到 `0`，并略微下移基线。
5. 默认把 advance width 设为字体的标准字宽。
6. 重命名字体元数据，避免和系统里已安装的字体冲突。
7. 生成最终的 `.ttf` / `.otf` 文件。

## macOS 预览

```bash
open FiraCodeNerdFont-Regular-Patched-deepseek.ttf
```

Font Book 预览步骤：

1. 安装字体。
2. 在左侧栏选中该字体。
3. 选择 `View > Show All Characters`，或按 `Cmd + 2`。
4. 滚动到 Private Use Area，找到你 patch 的码位，例如 `U+E900`。

你也可以把字符 ``（`U+E900`）直接粘贴到 Font Book 的预览框里快速查看。

在 Linux 上，可以使用字体查看器或 `fc-scan` 预览；在 Windows 上，可以双击字体文件安装后使用系统字体预览器查看。

## 注意事项

- SVG 的 `viewBox` 最好是正方形，例如 `0 0 24 24`。非正方形图标在缩放后可能出现拉伸。
- 如果 SVG 使用了复杂遮罩、渐变、文字或外部样式，FontForge 可能无法正确解析。建议尽量使用简化的 `path`。
- 脚本会修改字体名称表。如果你需要保留原始字体名称，可以注释掉脚本里的重命名部分。

## 免责声明

本项目仅为字体 patch 工具，供个人使用和开发参考，不隶属于、也不代表任何示例中出现的字体厂商、图标提供方或商标所有者。

文中出现的商标、Logo、图标名称和品牌名称，其权利均归各自所有者所有。如果你使用了第三方字体文件或 SVG 资源，请自行确认你拥有相应的使用和分发权利。

## 仓库结构

```text
.
├── README.md
├── README.zh-CN.md
├── main.py
├── patch_svg_to_font.py
├── assets/
├── font/
└── icons/
```
