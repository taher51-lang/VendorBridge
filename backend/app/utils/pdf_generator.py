"""
VendorBridge ERP – PDF Generator
==================================
Uses WeasyPrint to render HTML templates into PDF documents.
Primarily used for invoice PDF generation.
"""

import os


def generate_invoice_pdf(invoice_data: dict, output_dir: str = None) -> str:
    """
    Render an invoice as a PDF file.

    Args:
        invoice_data: Dict containing all invoice fields, items, and
                      company/vendor info needed for the template.
        output_dir: Directory to save the PDF. Defaults to
                    app.config['PDF_OUTPUT_DIR'].

    Returns:
        The absolute file path of the generated PDF.

    Implementation:
        1. Build output_dir from config if not provided.
        2. Create the output directory if it doesn't exist.
        3. Generate a unique filename: INV-{invoice_number}.pdf
        4. Render the HTML template (use Jinja2 render_template or
           render_template_string) with invoice_data context.
        5. Call weasyprint.HTML(string=html).write_pdf(output_path)
        6. Return output_path.
    """
    # TODO: Implement PDF generation
    # from weasyprint import HTML
    # html = render_template('invoice_template.html', **invoice_data)
    # HTML(string=html).write_pdf(output_path)
    pass


def generate_po_pdf(po_data: dict, output_dir: str = None) -> str:
    """
    Render a purchase order as a PDF file.

    Args:
        po_data: Dict containing PO fields, vendor info, and quotation items.
        output_dir: Directory to save the PDF.

    Returns:
        The absolute file path of the generated PDF.
    """
    # TODO: Same pattern as invoice PDF
    pass
