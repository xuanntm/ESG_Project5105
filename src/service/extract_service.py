import os, io, re, string, fitz
import PyPDF2, pdfplumber

# PDF text extraction
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter

from pdfminer.high_level import extract_text

from .nlp_service import nlp
import subprocess
import cv2

from PIL import Image
import pytesseract
import uuid
from dotenv import load_dotenv
load_dotenv()

IMAGE_FOLDER=os.environ.get("05_IMAGE_FOLDER")




def remove_header_footer(image_path, header_height_percent=0.05, footer_height_percent=0.05):
    print(f'remove_header_footer: {image_path}')
    img = cv2.imread(image_path)
    height, width = img.shape[:2]
    header_height = int(height * header_height_percent)
    footer_height = int(height * footer_height_percent)

    cropped_img = img[header_height:height - footer_height, 0:width]
    cv2.imwrite(image_path, cropped_img)

def convert_pdf_to_images(pdf_path, output_dir):
    process_id = uuid.uuid4().hex
    output_dir = output_dir + '/' + process_id
    print(f'convert_pdf_to_images:{pdf_path}-{output_dir}')
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run(['gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pngalpha', '-r300', '-sOutputFile=' + os.path.join(output_dir, 'page%d.png'), pdf_path])
    return output_dir


def extract_pdf_by_ocr(folder_location, header_height_percent, footer_height_percent, verbose=False):
    output_dir = convert_pdf_to_images(folder_location, IMAGE_FOLDER)
    print(f'output_dir:{output_dir}')
    all_text = ""
    content = []
    for filename in sorted(os.listdir(output_dir)):
        print(f'process filename:{filename}')
        if filename.endswith('.png'):
            img_path = os.path.join(output_dir, filename)
            remove_header_footer(img_path, header_height_percent, footer_height_percent) # Remove header and footer from the image
            img = Image.open(img_path)
            text = pytesseract.image_to_string(img)
            # print(f'text from OCR:{text}')
            # all_text += text + "\n\n"  # Add a separator between pages
            content.append(text)
    all_text = '##PAGE_BREAK##'.join(content)
    return all_text


def extract_content_from_pdf_by_ocr(pdf_file_path, header_height_percent, footer_height_percent):
    print('=== START === extract_content_from_pdf')
    """
    A simple user define function that, given a url, download PDF text content
    Parse PDF and return plain text version
    """
    headers={"User-Agent":"Mozilla/5.0"}

    try:
        # with open(pdf_file_path, 'rb') as file:
        #     pdf_bytes = file.read()
        # # access pdf content
        # text = extract_pdf(io.BytesIO(pdf_bytes), True)
        # folder_path = '/'.join(pdf_file_path.split('/')[0:-1])
        text = extract_pdf_by_ocr(pdf_file_path, header_height_percent, footer_height_percent, True)

        # return concatenated content
        print(f'text:{text}')
        return text

    except:
        return ""

def extract_content_from_pdf(pdf_file_path):
    print('=== START === extract_content_from_pdf')
    """
    A simple user define function that, given a url, download PDF text content
    Parse PDF and return plain text version
    """
    headers={"User-Agent":"Mozilla/5.0"}

    try:
        # with open(pdf_file_path, 'rb') as file:
        #     pdf_bytes = file.read()
        # # access pdf content
        # text = extract_pdf(io.BytesIO(pdf_bytes), True)

        text = extract_pdf(pdf_file_path, True)
        print(f'text extracted:{text}')
        # return concatenated content
        return text

    except:
        return ""

def extract_pdf_byte(file, verbose=False):
    print('=== START === extract_pdf')
    if verbose:
        print('Processing {}'.format(file))

    try:
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        codec = 'utf-8'
        laparams = LAParams()

        converter = TextConverter(resource_manager, fake_file_handle, codec=codec, laparams=laparams)
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
        
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()

        content = []

        index = 0

        for page in PDFPage.get_pages(file,
                                      pagenos, 
                                      maxpages=maxpages,
                                      password=password,
                                      caching=True,
                                      check_extractable=False):

            page_interpreter.process_page(page)
            index = index + 1
            print(f'_index {index}: {fake_file_handle.getvalue()}')

            content.append(fake_file_handle.getvalue())

            fake_file_handle.truncate(0)
            fake_file_handle.seek(0)
            # fake_file_handle.seek(0, os.SEEK_SET)        

        text = '##PAGE_BREAK##'.join(content)

        # close open handles
        converter.close()
        fake_file_handle.close()
        
        return text

    except Exception as e:
        print(e)

        # close open handles
        converter.close()
        fake_file_handle.close()

        return ""



def extract_pdf(file_location, verbose=False):
    print('=== START === extract_pdf')
    if verbose:
        print('Processing {}'.format(file_location))
    index = 0
    try:
        content = []
        # pdf_document = fitz.open(file_location)
        # for page in pdf_document:
        #     index = index + 1
        #     print(f'_index {index}: {page.get_text()}')
        #     content.append(page.get_text())
        
        # pdf_reader = PyPDF2.PdfReader(file_location)
        # print(f'_index start {index}')
        # for page in pdf_reader.pages:
        #     index = index + 1
        #     print(f'_index {index}: {page.extract_text()}')
        #     content.append(page.extract_text() or '')  # Handle None case

        # with pdfplumber.open(file_location) as pdf:
        #     for page in pdf.pages:
        #         # Extract text, ignoring tables
        #         if page.extract_tables():  # Check if there are tables
        #             continue  # Ignore this page if it has tables
        #         index = index + 1
        #         print(f'_index {index}: {page.extract_text()}')
        #         content.append(page.extract_text() or '')  # Handle None case

        text = extract_text(file_location)

        # text = '##PAGE_BREAK##'.join(content)
        
        return text

    except Exception as e:
        print(e)

        return ""

def remove_non_ascii(text):
    print('=== START === remove_non_ascii')
    printable = set(string.printable)
    return ''.join(filter(lambda x: x in printable, text))


# def extract_sentences(nlp, text):
def extract_sentences(text):
    print('=== START === extract_sentences')
    """
    Extracting ESG statements from raw text by removing junk, URLs, etc.
    We group consecutive lines into paragraphs and use spacy to parse sentences.
    """
    MIN_WORDS_PER_PAGE = 500
    
    pages = text.split('##PAGE_BREAK##')
#     print('Number of Pages: {}'.format(len(pages)))

    lines = []
    for page in pages:
        
        # remove non ASCII characters
        sub_text = remove_non_ascii(page)
        
        if len(sub_text.split(' ')) < MIN_WORDS_PER_PAGE:
#             print('Skipped Page: {}'.format(len(text.split(' '))))
            continue
        
        prev = ""
        for line in sub_text.split('\n\n'):
            # aggregate consecutive lines where text may be broken down
            # only if next line starts with a space or previous does not end with dot.
            if(line.startswith(' ') or not prev.endswith('.')):
                prev = prev + ' ' + line
            else:
                # new paragraph
                lines.append(prev)
                prev = line

        # don't forget left-over paragraph
        lines.append(prev)
        lines.append('##SAME_PAGE##')
        
    lines = '  '.join(lines).split('##SAME_PAGE##')
    
    # clean paragraphs from extra space, unwanted characters, urls, etc.
    # best effort clean up, consider a more versatile cleaner
    
    sentences = []
    pages_content = []

    for line in lines[:-1]:
        # removing header number
        line = re.sub(r'^\s?\d+(.*)$', r'\1', line)
        # removing trailing spaces
        line = line.strip()
        # words may be split between lines, ensure we link them back together
        line = re.sub(r'\s?-\s?', '-', line)
        # remove space prior to punctuation
        line = re.sub(r'\s?([,:;\.])', r'\1', line)
        # ESG contains a lot of figures that are not relevant to grammatical structure
        line = re.sub(r'\d{5,}', r' ', line)
        # remove emails
        line = re.sub(r'\S*@\S*\s?', '', line)
        # remove mentions of URLs
        line = re.sub(r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*', r' ', line)
        # remove multiple spaces
        line = re.sub(r'\s+', ' ', line)
        # join next line with space
        line = re.sub(r' \n', ' ', line)
        line = re.sub(r'.\n', '. ', line)
        line = re.sub(r'\x0c', ' ', line)
        
        pages_content.append(str(line).strip())

        # split paragraphs into well defined sentences using spacy
        for part in list(nlp(line).sents):
            sentences.append(str(part).strip())

#           sentences += nltk.sent_tokenize(line)
            
    # Only interested in full sentences and sentences with 10 to 100 words.
    sentences = [s for s in sentences if re.match('^[A-Z][^?!.]*[?.!]$', s) is not None]
    sentences = [s.replace('\n', ' ') for s in sentences]
    sentences = [s for s in sentences if (len(s.split(' ')) > 10) & (len(s.split(' ')) < 100)]

    return pages_content, sentences