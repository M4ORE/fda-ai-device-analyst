@echo off
echo ========================================
echo FDA AI Device Classification
echo ========================================
echo.
echo This will classify all devices using LLM
echo Estimated time: 40-60 minutes for 1200+ devices
echo.
pause

venv\Scripts\python.exe src\classify.py --batch-size 20

echo.
echo ========================================
echo Classification complete!
echo ========================================
pause
