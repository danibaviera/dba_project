@echo off
echo 🚀 Iniciando MonitorDB API (Versão Mínima)...
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo ✅ Ambiente virtual ativado
echo 🌐 Iniciando servidor em http://localhost:8000
echo 📖 Documentação em http://localhost:8000/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause