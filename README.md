# ESG_Project5105

brew install python@3.12

python3.12 -m venv .virt1
source .virt1/bin/activate


pip install -r requirements.txt

pip list
pip freeze > requirements_2025_03_08.txt


Step1: PDF -> raw Text
Step 2: raw text -> cleaned text
Step 3: cleaned text -> Pre NLP process


# Open API Key
OPENAI_API_KEY=sk-proj-...
# Config foler
01_INPUT_PDF_FOLDER=.../ESG5105/01_INPUT
02_RAW_TEXT_FOLDER=.../ESG5105/02_RAW_TEXT
03_ESG_TEXT_FOLDER=.../ESG5105/03_ESG_TEXT
04_ESG_EXTRACTED_FOLDER=.../ESG5105/04_ESG_EXTRACTED_TEXT


> python src/app.py  
> access website at http://localhost:5000/
