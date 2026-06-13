# 题练通

题练通是一个本地单机版刷题软件，数据全部保存在本机 SQLite 数据库中，不需要登录、注册、会员、云端同步或后端服务器。

## 功能

- 下载空白 Excel 题库模板和示例题库
- 导入 Excel 题库，检查表头、题型、答案、选项和重复题
- 导入前预览、编辑、删除题目
- 保存题库、查看题库列表和题库详情
- 顺序刷题、随机刷题、错题练习、背题模式
- 自动保存做题记录，错题自动进入错题本
- 收藏题目、学习记录统计、基础设置

## 技术栈

Python 3.11+、PySide6、SQLite、openpyxl、SQLAlchemy、pytest、PyInstaller。

## 安装与启动

```bash
pip install -r requirements.txt
python main.py
```

首次启动会自动创建 `data/question_app.db`，并在 `resources/templates/` 下生成空白模板和示例题库。

## 题库模板规则

Excel 必须包含工作表 `题库数据`，表头为：

```text
题型、题目、A选项、B选项、C选项、D选项、E选项、F选项、正确答案、解析、章节、难度
```

支持题型：单选题、单选、多选题、多选、判断题、判断、填空题、填空。

答案规则：单选填 `A`；多选填 `ABD` 或 `A,B,D`；判断题支持 `正确/错误/对/错/√/×/True/False/1/0`；填空题多个答案用 `|` 分隔。

## 数据保存位置

默认数据库文件：`data/question_app.db`。删除题库时会同时删除对应题目、做题记录、错题记录和收藏记录。

## 打包

Windows 下执行：

```bat
build.bat
```

输出：`dist\题练通\题练通.exe`。请分发整个 `dist\题练通` 文件夹。

详细说明见 `WINDOWS_BUILD.md`。

## 常见问题

- 缺少工作表：确认工作表名称是 `题库数据`。
- 表头缺失：使用软件内下载的标准模板，不要修改第一行表头。
- Excel 无法读取：确认文件是 `.xlsx`，并关闭正在占用该文件的 Excel。
- 模板保存失败：确认目标文件夹可写，且同名文件没有被占用。
- 数据库创建失败：确认项目目录下 `data/` 可写。
- Ubuntu 启动提示 `Could not load the Qt platform plugin "xcb"`：安装 Qt 运行库 `sudo apt install libxcb-cursor0`，部分系统包名为 `xcb-cursor0`。

## 测试

```bash
pytest
```
