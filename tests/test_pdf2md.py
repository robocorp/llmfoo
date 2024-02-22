from pathlib import Path
from llmfoo.pdf2md import process_pdf  # Adjust the import path according to your project structure


def test_pdf_to_markdown_conversion():
    pdf_file = "instruction-manual-fisher-es-eas-easy-e-valves-cl125-through-cl600-en-124780.pdf"
    pdf_path = Path(__file__).parent / "data" / "pdfs" / pdf_file
    output_dir = Path(__file__).parent / "data" / "output"

    # Run the conversion process
    filename = process_pdf(pdf_path, output_dir)

    # Validate the output
    output_md_path = output_dir / (pdf_file.replace(".pdf", ".md"))
    assert output_md_path.exists(), "Markdown file was not created."

    with open(output_md_path, "r", encoding="utf-8") as output_file:
        output_md = output_file.read()

    assert output_md == "something", "The output Markdown does not match the expected Markdown."