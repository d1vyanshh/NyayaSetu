@echo off
setlocal
cd /d "%~dp0"

echo Installing PrecedentForecaster dependencies...
where python >nul 2>nul
if %errorlevel%==0 (
  set PYTHON_CMD=python
) else (
  set PYTHON_CMD=py
)

%PYTHON_CMD% -m pip install -r requirements.txt

echo.
echo Pull these Ollama models if you have not already:
echo   ollama pull phi3:mini
echo   ollama pull nomic-embed-text
echo.

echo Building indexes from ..\case_corpus ...
%PYTHON_CMD% index_cases.py --reset

echo Launching Streamlit UI...
streamlit run app.py
