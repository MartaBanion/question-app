@echo off
chcp 65001 >nul
setlocal

set APP_NAME=题练通
set PYTHON_EXE=python
set VENV_DIR=.venv-win

echo ========================================
echo  正在打包 %APP_NAME%
echo ========================================

where %PYTHON_EXE% >nul 2>nul
if errorlevel 1 (
  echo 未找到 python。请先安装 Python 3.11+，并勾选 Add Python to PATH。
  pause
  exit /b 1
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo 创建虚拟环境...
  %PYTHON_EXE% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo 创建虚拟环境失败。
    pause
    exit /b 1
  )
)

echo 安装依赖...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo 依赖安装失败。
  pause
  exit /b 1
)

echo 清理旧打包文件...
if exist build rmdir /s /q build
if exist "dist\%APP_NAME%" rmdir /s /q "dist\%APP_NAME%"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"

echo 开始 PyInstaller 打包...
"%VENV_DIR%\Scripts\python.exe" -m PyInstaller --noconfirm --windowed --name "%APP_NAME%" ^
  --add-data "resources\templates;resources\templates" ^
  --add-data "resources\icons;resources\icons" ^
  --add-data "resources\styles;resources\styles" ^
  main.py
if errorlevel 1 (
  echo 打包失败，请查看上方错误信息。
  pause
  exit /b 1
)

if not exist "dist\%APP_NAME%\data" mkdir "dist\%APP_NAME%\data"

echo.
echo 打包完成：dist\%APP_NAME%\%APP_NAME%.exe
echo 数据保存位置：%%APPDATA%%\%APP_NAME%\data\question_app.db
echo 请分发整个 dist\%APP_NAME% 文件夹，不要只复制 exe。
echo.
pause
