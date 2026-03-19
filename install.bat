@echo off
REM Prometheus Research Skill 安装脚本 (Windows)

echo 🚀 安装 Prometheus Research Skill...

set SKILL_DIR=%USERPROFILE%\.claude\skills\prometheus-research

REM 创建目录
if not exist "%SKILL_DIR%" mkdir "%SKILL_DIR%"

REM 复制文件
echo 📁 复制文件...
xcopy /E /I /Y "%~dp0*" "%SKILL_DIR%\"

REM 安装 Python 依赖
if exist "%SKILL_DIR%\scripts\requirements.txt" (
    echo 📦 安装 Python 依赖...
    pip install -r "%SKILL_DIR%\scripts\requirements.txt"
)

echo.
echo ✅ 安装完成!
echo.
echo 使用方法：
echo   在 Claude Code 中说：
echo     启动研究 [研究主题]
echo     继续研究
echo.
echo 安装位置: %SKILL_DIR%
pause
