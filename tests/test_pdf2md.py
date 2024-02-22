import logging
from pathlib import Path
from llmfoo.pdf2md import process_pdf


def test_pdf_to_markdown_conversions():
    pdf_dir = Path(__file__).parent / "data" / "pdfs"
    output_dir = Path(__file__).parent / "data" / "output"

    skip_files = ["instruction-manual-fisher-es-eas-easy-e-valves-cl125-through-cl600-en-124780.pdf"]

    for pdf_file in pdf_dir.glob("*.pdf"):
        if pdf_file.name not in skip_files:
            logging.info(f"Processing {pdf_file.name}...")
            try:
                process_pdf(pdf_file, output_dir)
            except Exception as e:
                logging.error(f"Failed to process {pdf_file.name}: {e}")


def test_pdf_to_markdown_conversion_huge():
    pdf_file = "instruction-manual-fisher-es-eas-easy-e-valves-cl125-through-cl600-en-124780.pdf"
    pdf_path = Path(__file__).parent / "data" / "pdfs" / pdf_file
    output_dir = Path(__file__).parent / "data" / "output"

    # Run the conversion process
    filename = process_pdf(pdf_path, output_dir)

    # Validate the output
    assert filename.exists(), "Markdown file was not created."

    with open(filename, "r", encoding="utf-8") as output_file:
        output_md = output_file.read()

    assert output_md == "something", "The output Markdown does not match the expected Markdown."
