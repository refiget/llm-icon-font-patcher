# Patch SVG Icon to Font

把任意 SVG 图标 patch 到 TrueType / OpenType 字体的指定码位上，常用于在编程字体（如 Nerd Font）里添加自定义图标。

## 依赖

- **FontForge**（提供 Python 绑定 `fontforge`）

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

当前目录已经包含了一个示例字体和 SVG：

```bash
python3 patch_svg_to_font.py \
  --font FiraCodeNerdFont-Regular.ttf \
  --svg deepseek.svg \
  --codepoint 0xE900 \
  --output FiraCodeNerdFont-Regular-Patched-deepseek.ttf
```

安装生成字体后，在支持 PUA 的编辑器/终端里输入 `\uE900` 即可看到 DeepSeek 图标。

## 命令行用法

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

### 示例：复用到其他字体

```bash
# 把同一个 SVG patch 到 JetBrains Mono 字体
python3 patch_svg_to_font.py \
  --font "/path/to/JetBrainsMono-Regular.ttf" \
  --svg deepseek.svg \
  --codepoint 0xE900 \
  --output JetBrainsMono-DeepSeek.ttf

# 如果目标字体是比例字体（非等宽），去掉强制等宽
python3 patch_svg_to_font.py \
  --font "/path/to/SomeProportionalFont.ttf" \
  --svg deepseek.svg \
  --codepoint U+E900 \
  --output SomeProportionalFont-Patched.ttf \
  --proportional
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--font` | 原始字体路径 |
| `--svg` | SVG 图标路径（建议 `viewBox` 为正方形，如 `0 0 24 24`） |
| `--codepoint` | 目标 Unicode 码位，**强烈建议选 PUA 空位**（见下表） |
| `--output` | 输出字体文件名 |
| `--proportional` | 默认会强制 glyph 宽度等于字体标准字宽（等宽）。加此参数则按图标实际宽度自适应。 |

### Codepoint 选择建议

为了避免覆盖已有字符，请优先使用 **PUA（Private Use Area）** 空位：

| 区域 | 范围 | 说明 |
|------|------|------|
| PUA-BMP | `U+E000` ~ `U+F8FF` | 最常用，兼容性好 |
| PUA-A | `U+F0000` ~ `U+FFFFD` | 平面 15 |
| PUA-B | `U+100000` ~ `U+10FFFD` | 平面 16 |

**如何查找当前字体的空位？**

```bash
fc-query -f '%{charset}\n' YourFont.ttf
```

如果输出里没有某个区间（例如 `e900` 没有出现），那它就是空的。

## 脚本做了什么？

1. **读取字体指标**：自动获取 `em` (UPM)、`capHeight`、标准字宽等，保证参数不硬编码。
2. **导入 SVG**：通过 FontForge 把 SVG path 转成字体 glyph 轮廓。
3. **智能缩放**：按 `capHeight × 0.95` 缩放图标，使其与字母大小视觉协调。
4. **位置修正**：水平左对齐 `0`，垂直下沉约 `2.5% em`，和 Nerd Font 图标风格保持一致。
5. **等宽对齐**：默认把 glyph advance width 设成字体标准字宽（空格/`A` 的宽度）。
6. **重命名字体**：自动修改字体内部名称，防止和系统已安装字体冲突。
7. **生成字体**：输出 `.ttf` / `.otf`。

## 在 macOS Font Book 中预览

```bash
open FiraCodeNerdFont-Regular-Patched-deepseek.ttf
```

在 Linux 上可以用字体查看器或 `fc-scan` 预览；Windows 上可以双击安装后用系统字体预览器查看。

Font Book 打开后：

1. 点击「安装字体」。
2. 在左侧栏选中该字体。
3. 菜单栏选择 **显示 > 显示全部字符**（或按 `Cmd + 2`）。
4. 滚动到「专用字符 / Private Use Area」区域，找到你 patch 的码位（如 `U+E900`）即可看到图标。

> 你也可以把字符 ``（U+E900）直接复制粘贴到 Font Book 的预览输入框里快速查看。

## 注意事项

- SVG 的 `viewBox` 最好为正方形（如 `0 0 24 24`），非正方形图标缩放后可能会拉伸。
- 如果 SVG 使用了复杂遮罩、渐变、文字或外部样式，FontForge 可能无法正确解析。建议简化为纯 `path`。
- 脚本会修改字体名称表，如果你需要保留原始名称，请在脚本里注释掉「Rename font」段落。

## 批量处理

如果你想把 `./icons` 里的所有 SVG 一次性 patch 到 `./font` 里的所有 `.ttf` 字体，可以直接运行：

```bash
python3 main.py
```

默认会：

1. 读取 `./font` 下所有 `.ttf`
2. 按文件名排序读取 `./icons` 下所有 `.svg`
3. 从 `U+E900` 开始顺序分配 codepoint
4. 把每个字体的所有图标 patch 完后输出到 `./out/`

如果要改目录或起始码位：

```bash
python3 main.py \
  --font-dir font \
  --icon-dir icons \
  --out-dir out \
  --start-codepoint 0xE900
```
