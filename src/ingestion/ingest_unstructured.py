###----------------------------- Imports ---------------------------------------------
from pypdf import PdfReader
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders.parsers import PyMuPDFParser, TesseractBlobParser
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders import FileSystemBlobLoader

###---------------------------- Extraction Modules ---------------------------------------

def read_pdf_docs(pdf_dir: str):

    loader = GenericLoader(
        blob_loader=FileSystemBlobLoader(
            path=pdf_dir,
            glob="*.pdf",
        ),
        blob_parser=PyMuPDFParser(
            mode='page',
            images_inner_format='html-img',
            images_parser=TesseractBlobParser(),
            extract_images=True,
            extract_tables='markdown',
        ),
    )
    
    return loader.load()

def load_images(reader: PdfReader, image_dir: str):

    image_filepath = image_dir
    for i, page in enumerate(reader.pages):

        image_filepath = image_filepath + '_'  + str(i)
        for count, image_file_object in enumerate(page.images):

            image_filepath = image_filepath + str(count) + image_file_object.name
            with open(image_filepath, "wb") as fp:
                
                fp.write(image_file_object.data)

def extract_content(pages):

    doc_content = []
    for page in pages:
        doc_content.append(page.page_content)

    return doc_content


def extract_metadata(pages: list):

    metdata_list = []

    for page in pages:

        # cleaned_metdata_page = clean_metadata(page)
        metdata_list.append(page)

    return metdata_list

def extract(pdf_dir: str, image_dir: str):

    pages = read_pdf_docs(pdf_dir)

    docs_content = extract_content(pages)
    metadata_list =  extract_metadata(pages)

    pypdf_reader = PdfReader(pdf_dir)
    load_images(pypdf_reader, image_dir)

    return {'content' : docs_content, 'metadata' : metadata_list}


###---------------------------------- Transformation Modules --------------------------------

def clean_metadata(metadata, redundant_keys: set):
    
    if redundant_keys <= metadata.keys():
        for key in redundant_keys:
            del metadata[key]

    return metadata


def add_author(doc):

    doc.metadata['author'] = str(' '.join(doc.metadata['source'].split('_')[-2:])).split('.')[0]

    return doc

def if_toc(full_text):

    if not (full_text.startswith('Table of Contents') or full_text.startswith('Contents') or full_text.startswith('CONTENTS')):
        return None

    lines = full_text.split('\n')[1:8]
    toc_line_heuristic = r'(?mi)^((?:[0-9.]+|[IVXLCDM]+\b))?\s*(.+?)\s*(?:(?:\s*\.\s*){2,}\s*|(?:\s*\n\s*\.+\s*(?:\n\s*)?)|\s*\n\s*)([a-z0-9]+)$'

    match_count = 0
    for line in lines:
        if re.search(toc_line_heuristic, line, re.IGNORECASE):
            match_count += 1
    
    if match_count >= 2:
        return full_text
    else:
        return None

def extract_toc(doc):

    lines = [line.strip().replace("'", "") for line in doc.page_content.strip().splitlines()]
    full_text = "\n".join(lines)

    toc_text = if_toc(full_text)
    toc_list = []
    if toc_text:

        regex_pattern = r"(?mi)^((?:[0-9.]+|[IVXLCDM]+\b))?\s*(.+?)\s*(?:(?:\s*\.\s*){2,}\s*|(?:\s*\n\s*\.+\s*(?:\n\s*)?)|\s*\n\s*)([a-z0-9]+)$"
        matches = re.finditer(regex_pattern, toc_text, re.MULTILINE)

        for match in matches:
            section_id = match.group(1).strip() if match.group(1) else None
            title = match.group(2).strip()
            title = re.sub(r'(\.\s*){2,}', '', title)
            page_str = match.group(3).strip()
            page = int(page_str) if page_str.isdigit() else page_str
            

            
            entry = {"id": section_id, "title": title, "page": page}
            toc_list.append(entry)

    return toc_list



def normalize_text(page: str):

    page = page.strip()

    page = re.sub(r'\n+', "", page)

    page = re.sub(r'\s+', '', page)


def clean_docs(doc_dict: dict):
    

    
    
    return





