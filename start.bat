@echo off
echo Starting Doyle Chrysler Controller Tool...
cd /d "%~dp0"
pip install -r requirements.txt --quiet
python fake_data_generator.py
streamlit run app.py --server.port 8501
pause
