import json
import os
import logging
import subprocess
import pypdf
from pathlib import Path
from typing import List, TypedDict, Callable
import base64
import requests

from camelot.core import TableList
from dotenv import load_dotenv
import argparse
import camelot
from pypdf import PageObject

load_dotenv()


class PageData(TypedDict):
    content: str
    page_image: str
    page: int
    source: str


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clean_workdir(workdir: Path):
    if workdir.exists():
        for file in workdir.iterdir():
            if file.is_file():
                file.unlink()


def setup_workdir(workdir: Path):
    clean_workdir(workdir)
    workdir.mkdir(exist_ok=True)


def encode_image(image_path: str):
    logging.info(f"Attempting to encode image at: {image_path}")
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        logging.info(f"Image encoded successfully: {image_path}")
        return encoded
    except FileNotFoundError:
        logging.error(f"Image file not found: {image_path}")
        return ""


def get_page_description_from_openai(base64_image: str, page_content: str, tables_markdown: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No OPENAI_API_KEY in environment variables!")
    print(page_content)
    print("=" * 80)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    instruction = f"""
Convert the text content of this PDF document page into well-structured Markdown format.
Below is the PyPDF extracted text and potential Camelot extracted tables from the page, followed by screenshot
of the same page. For each figure in the screenshot of the page, provide a clear and detailed description in the text,
as the reader will not have access to the actual figure.
Apply Markdown formatting appropriately, using headers, lists, tables, bold and italic emphasis, and links.
At the beginning, add an HTML comment in Markdown to discuss how to best represent the visual elements from
the image of the page, such as tables and figures. Specifically, note details like the number of columns and
rows in a table and information defined in figures. Number of columns are calculated based on data rows.
Here is an example of how the result should look in Markdown format:

```markdown"
<!-- Page contains a table. The table has three columns, 1 header row and 2 data rows. -->
# Section Title
* List Item 1
* List Item 2
Table:
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |
```

Here is the text extracted from the page with PyPDF and then the screenshot of the same page:
```
{page_content}
```

Here are the markdown formatted tables from the page extracted with Camelot:
```
{tables_markdown}
```
""".strip()
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant in document page image to text processing."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": instruction,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"},
                    },
                ],
            }
        ],
        "max_tokens": 4096,
    }
    logging.info("Sending request to OpenAI API for page improvement.")
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        raise
    response_json = response.json()
    content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(content)
    if not content:
        raise Exception("Received empty content from OpenAI API.")
    logging.info(f"Received response from OpenAI API: {content[:120]}...")
    return content


def convert_pdf_page_to_png(pdf_path: Path, page_num: int, output_dir: Path) -> str:
    output_png_base = f"page_{page_num}"
    output_png_path = output_dir / f"{output_png_base}-{str(page_num).zfill(2)}.png"
    if output_png_path.exists():
        logging.info("Page png exists, using it.")
        return str(output_png_path)
    command = ["pdftocairo", "-png", "-f", str(page_num), "-l", str(page_num), str(pdf_path),
               str(output_dir / output_png_base)]

    logging.info(f"Running command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error converting PDF page to PNG: {e}")
        raise

    # Log the contents of the output directory
    logging.info(f"Contents of {output_dir}: {[f.name for f in output_dir.iterdir()]}")

    if not output_png_path.exists():
        logging.error(f"Expected PNG file not found: {output_png_path}")
        raise Exception(f"Expected PNG file not found: {output_png_path}")

    return str(output_png_path)


def extract_text_from_page(page) -> str:
    try:
        return page.extract_text() or ""
    except Exception as e:
        logging.error(f"Error extracting text from page: {e}")
        return ""


def _use_file_or_create(filename: str, creator: Callable) -> str:
    if not os.path.isfile(filename):
        content = creator()
        with open(filename, "w") as f:
            f.write(content)
        logging.info(f"File {filename} stored.")
    else:
        logging.info(f"File {filename} exists, using content from there.")
        with open(filename, "r") as f:
            content = f.read()
    return content


def process_pdf_page(page: PageObject, tables: TableList, page_num: int, pdf_path: Path, img_dir: Path) -> PageData:
    page_image_path = convert_pdf_page_to_png(pdf_path, page_num, img_dir)
    if not page_image_path:
        logging.error(f"Error no image! {page_num}")
        return {"content": "", "page_image": "", "page": page_num, "source": pdf_path.name}
    base64_image = encode_image(page_image_path)

    extract_file = str(img_dir / f"page_pypdf_extract_{page_num}.txt")
    tables_file = str(img_dir / f"page_tables_extract_{page_num}.txt")
    page_description_file = str(img_dir / f"page_description_{page_num}.txt")

    page_content = _use_file_or_create(extract_file, lambda: extract_text_from_page(page))
    tables_markdown = _use_file_or_create(tables_file, lambda: "\n\n".join(table.df.to_markdown() for table in tables))
    page_description = _use_file_or_create(page_description_file, lambda: get_page_description_from_openai(base64_image, page_content, tables_markdown))

    logging.info(f"Page data from page {page_num} ready")
    return {
        "content": page_description,
        "page_image": page_image_path,
        "page": page_num,
        "source": pdf_path.name
    }


def process_pdf(pdf_path: Path, output_dir: Path) -> List[PageData]:
    try:
        pdf_reader = pypdf.PdfReader(str(pdf_path))
    except Exception as e:
        logging.error(f"Error reading PDF {pdf_path.name}: {e}")
        return []

    img_dir = output_dir / f"{pdf_path.stem}_pages"
    img_dir.mkdir(exist_ok=True)

    return [process_pdf_page(page, camelot.read_pdf(str(pdf_path), pages=str(i)),  i, pdf_path, img_dir) for i, page in enumerate(pdf_reader.pages, start=1)]


def read_pdf_files(directory: Path, workdir: Path) -> List[PageData]:
    if not directory.exists() or not directory.is_dir():
        logging.error(f"Directory {directory} does not exist or is not a directory.")
        return []

    pdf_files = list(directory.glob("*.pdf"))
    if not pdf_files:
        logging.info(f"No PDF files found in {directory}")
        return []

    setup_workdir(workdir)

    results = []
    for pdf_file in pdf_files:
        results.extend(process_pdf(pdf_file, workdir))

    return results


def save_to_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Process PDF files and convert them to enhanced text using OpenAI's API.")
    parser.add_argument("pdf_directory", type=str, help="Directory containing PDF files to process")
    parser.add_argument("output_file", type=str, help="File path to save the processed data")
    parser.add_argument("--workdir", type=str, default="workdir2", help="Working directory for temporary files")
    return parser.parse_args()


def main():
    args = parse_arguments()
    pdf_directory = Path(args.pdf_directory)
    output_file = args.output_file
    workdir = Path(args.workdir)

    logging.info(f"Processing PDF files in directory: {pdf_directory}")
    pdf_data = read_pdf_files(pdf_directory, workdir)
    logging.info(f"Processed {len(pdf_data)} pages from PDF files.")
    save_to_json(pdf_data, output_file)
    logging.info(f"Saved processed data to {output_file}")


if __name__ == "__main__":
    main()