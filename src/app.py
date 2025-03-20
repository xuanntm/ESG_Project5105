from flask import Flask, request, jsonify, send_from_directory
import os, json
import fitz  # PyMuPDF
from dotenv import load_dotenv
import urllib.parse
from service.extract_service import extract_sentences, extract_content_from_pdf, extract_content_from_pdf_by_ocr, ESG_TEXT_FOLDER
from service.nlp_service import nlp
from service.openAI_service import openai_client, extract_esg_values_openai
import PyPDF2

load_dotenv()


app = Flask(__name__)

UPLOAD_FOLDER = os.environ.get("01_INPUT_PDF_FOLDER")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

CONFIG_FOLDER = 'src/config/'
config_file_path = CONFIG_FOLDER + 'esg_metric_dictionary.json'

# Load the JSON data into a dictionary
with open(config_file_path, 'r') as file:
    esg_metrics = json.load(file)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    company = request.form.get('company')  # Get from FormData
    reportYear = request.form.get('reportYear')  # Get from FormData

    if file and allowed_file(file.filename):
        file_folder = os.path.join(app.config['UPLOAD_FOLDER'], company, reportYear)
        os.makedirs(file_folder, exist_ok=True)
        file_path = os.path.join(file_folder, file.filename)
        file.save(file_path)
        return jsonify({'file_location': file_path}), 201

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/extract-text', methods=['POST'])
def extract_text():
    data = request.json
    file_location = data.get('file_location')
    header_height_percent = data.get('header_height_percent', 0.05)
    footer_height_percent = data.get('footer_height_percent', 0.05)

    # Decode the file_location if necessary
    decoded_file_location = urllib.parse.unquote(file_location)
    print(f'decoded_file_location:{decoded_file_location}')

    if not os.path.exists(decoded_file_location):
        return jsonify({'error': 'File not found'}), 404

    if not allowed_file(decoded_file_location):
        return jsonify({'error': 'Invalid file type'}), 400

    # Extract text from PDF
    text = ""
    try:
        # pdf_document = fitz.open(decoded_file_location)
        # for page in pdf_document:
        #     text += page.get_text()
        # pdf_document.close()
        text = extract_content_from_pdf_by_ocr(decoded_file_location, header_height_percent, footer_height_percent)
        # print(f'text:{text[0:100]}')

        report_pages, report_sentences = extract_sentences(text)
        # print(f'report_pages:{report_pages[0][0:100]}')
        # print(f'report_sentences:{report_sentences}')
        
        return jsonify({'extracted_text': report_sentences}), 200

        # return jsonify({'extracted_text': text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    company = request.form.get('company')  # Get from FormData
    reportYear = request.form.get('reportYear')  # Get from FormData

    if file and allowed_file(file.filename):
        file_folder = os.path.join(app.config['UPLOAD_FOLDER'], company, reportYear)
        os.makedirs(file_folder, exist_ok=True)
        file_path = os.path.join(file_folder, file.filename)
        file.save(file_path)


    file_location = file_path
    header_height_percent = float(request.form.get('header_height_percent', 0.05))
    footer_height_percent = float(request.form.get('footer_height_percent', 0.05))

    # Decode the file_location if necessary
    decoded_file_location = urllib.parse.unquote(file_location)
    print(f'decoded_file_location:{decoded_file_location}')

    if not os.path.exists(decoded_file_location):
        return jsonify({'error': 'File not found'}), 404

    if not allowed_file(decoded_file_location):
        return jsonify({'error': 'Invalid file type'}), 400

    # Extract text from PDF
    text = ""
    try:
        # pdf_document = fitz.open(decoded_file_location)
        # for page in pdf_document:
        #     text += page.get_text()
        # pdf_document.close()
        text = extract_content_from_pdf_by_ocr(decoded_file_location, header_height_percent, footer_height_percent)
        

        report_pages, report_sentences = extract_sentences(text)
        # print(f'report_pages:{report_pages[0][0:100]}')
        # print(f'report_sentences:{report_sentences}')

        # Save extracted text to a new folder
        filename_no_ext = os.path.splitext(file.filename)[0]
        output_filepath = os.path.join(ESG_TEXT_FOLDER, filename_no_ext + '.txt')
        with open(output_filepath, 'w') as f:
            for report_sentence in report_sentences:
                f.write(report_sentence + " ")
        
        return jsonify({'message': 'File processed and text saved successfully!', 'output_filepath': output_filepath}), 200

        # return jsonify({'extracted_text': text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




@app.route('/extract-esg-sentences', methods=['POST'])
def extract_esg_sentences():
    data = request.json
    text = data.get('extracted_text')
    esg_indicators = data.get('esg_indicators', [])

    if not text:
        return jsonify({'error': 'No text to analyze.'}), 400

    relevant_sentences = []
    doc = nlp(text)  # Process the text with spaCy

    for sent in doc.sents:
        for indicator in esg_indicators:
            if indicator.lower() in sent.text.lower():
                relevant_sentences.append(sent.text)
                break  # Stop checking after finding one match

    return jsonify({'relevant_sentences': relevant_sentences}), 200


# Add this function in your Flask app
@app.route('/process-esg-data', methods=['POST'])
def process_esg_data():
    data = request.json
    sentences = data.get('sentences', [])

    if not sentences:
        return jsonify({'error': 'No sentences provided.'}), 400

    try:
        # Combine the sentences into a single prompt for ChatGPT
        # prompt = f"Please analyze the following sentences and extract the relevant ESG metric values:\n\n"
        prompt = f"The following are ESG metric keys with their explanations:\n"
        for key, explanation in esg_metrics.items():
            prompt += f"- {key}: {explanation}\n"

        prompt += "\nPlease analyze the following sentences and extract the relevant values for these ESG metrics:\n\n"
        prompt += "\n".join(sentences)

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # or the model you have access to
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        print(response.choices[0].message.content)
        if response.choices and response.choices[0].message:
            extracted_value = response.choices[0].message.content
            return jsonify({'metric_values': extracted_value.strip()}), 200
        else:
            return jsonify({'error': 'No response from ChatGPT.'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/load-text-file')
def load_text_file():
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return 'File not found', 404
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
        return file_content
    except Exception as e:
        return f'Error reading file: {e}', 500


@app.route('/process-esg-data-by-path')
def process_esg_data_v2():
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return 'File not found', 404
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
        esg_metrict_values = extract_esg_values_openai(file_content)
        return esg_metrict_values, 200
    except Exception as e:
        return f'Error reading file: {e}', 500



if __name__ == '__main__':
    app.run(debug=True)