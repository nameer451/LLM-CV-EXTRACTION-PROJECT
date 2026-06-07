@echo off
REM TALASH Milestone 2 - Quick Start Guide for Windows
REM Run this script to set up and start the system

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  TALASH - Milestone 2: Quick Start (Windows)          ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check Python version
echo 📦 Checking Python version...
python --version
echo.

REM Create virtual environment
echo 🔧 Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo.   ✓ Virtual environment created
) else (
    echo.   ✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo 🚀 Activating virtual environment...
call venv\Scripts\activate.bat
echo.   ✓ Virtual environment activated
echo.

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt
echo.   ✓ Dependencies installed
echo.

REM Generate sample data
echo 📊 Generating sample candidate data...
python sample_cv_generator.py
echo.   ✓ Sample data generated (sample_cv_data.json)
echo.

REM Display API endpoints
echo 🌐 Starting TALASH Backend Server...
echo.
echo ─────────────────────────────────────────────────────────
echo Available API Endpoints:
echo ─────────────────────────────────────────────────────────
echo GET  /api/candidates                 - List all candidates
echo GET  /api/candidate/^<id^>             - Get candidate details
echo GET  /api/analyze/^<id^>               - Run analysis
echo POST /api/upload                     - Upload CV
echo GET  /api/dashboard-stats            - Dashboard statistics
echo GET  /api/reports-data               - Reports metrics
echo GET  /api/missing-info-email/^<id^>    - Draft email
echo GET  /health                         - Health check
echo.
echo Web Application:
echo ─────────────────────────────────────────────────────────
echo URL: http://localhost:5000
echo Login: Use login.html
echo.
echo Frontend Pages:
echo   • Dashboard (KPI cards, analysis queue)
echo   • Candidates (ledger with search)
echo   • Analysis (4-tab detailed results)
echo   • Reports (4 interactive charts)
echo   • Profile (candidate detail)
echo   • Settings (configuration)
echo ─────────────────────────────────────────────────────────
echo.
echo Starting Flask server on port 5000...
echo.
python app.py
