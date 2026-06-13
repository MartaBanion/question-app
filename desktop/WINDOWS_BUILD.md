# Windows 打包说明

本项目可以在 Windows 上打包为 `题练通.exe`。建议使用 Python 3.11 或更高版本。

## 1. 准备环境

安装 Python 时请勾选：

```text
Add Python to PATH
```

## 2. 打包

在 Windows 终端进入项目目录：

```bat
cd question-app
build.bat
```

脚本会自动完成：

- 创建 `.venv-win` 虚拟环境
- 安装 `requirements.txt` 依赖
- 调用 PyInstaller 打包
- 把 `resources/templates`、`resources/icons`、`resources/styles` 一起打进程序

## 3. 输出位置

```text
dist\题练通\题练通.exe
```

请分发整个目录：

```text
dist\题练通\
```

不要只复制单独的 exe。

## 4. 数据保存位置

Windows 打包版会把数据库保存到：

```text
%APPDATA%\题练通\data\question_app.db
```

这样即使程序目录在桌面、下载目录或只读位置，学习记录、错题和收藏也能持久保存。

## 5. 常见问题

如果提示 `python 不是内部或外部命令`：重新安装 Python，并勾选 `Add Python to PATH`。

如果依赖下载慢：可以先换国内 pip 源，例如：

```bat
.venv-win\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果杀毒软件拦截：这是 PyInstaller 程序常见误报，可将 `dist\题练通` 加入信任，或在本机自行打包。
