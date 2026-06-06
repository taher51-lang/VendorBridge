"""
VendorBridge ERP – PDF Generator
==================================
Uses WeasyPrint to render Jinja2 HTML templates into PDF documents.
Used for Invoice and Purchase Order PDF generation.

Workflow:
    invoice_data (dict)
        → flask.render_template('invoice_template.html', **invoice_data)
        → weasyprint.HTML(string=html).write_pdf(output_path)
        → returns absolute file path of saved PDF
"""

import os

from flask import render_template, current_app


def generate_invoice_pdf(invoice_data: dict, output_dir: str = None) -> str:
    """
    Render an invoice as a PDF file using WeasyPrint.

    Args:
        invoice_data: Dict containing all invoice fields, items, and
                      vendor info needed for invoice_template.html.
        output_dir:   Directory to save the PDF. Defaults to
                      app.config['PDF_OUTPUT_DIR'] ('generated_pdfs').

    Returns:
        The absolute file path of the generated PDF.

    Raises:
        Exception: Propagates WeasyPrint or filesystem errors to caller.
    """
    from weasyprint import HTML

    if output_dir is None:
        output_dir = current_app.config.get("PDF_OUTPUT_DIR", "generated_pdfs")

    os.makedirs(output_dir, exist_ok=True)

    invoice_number = invoice_data.get("invoice_number", "INV-UNKNOWN")
    # Sanitise filename – strip characters not allowed in file names
    safe_name = invoice_number.replace("/", "-").replace("\\", "-")
    output_path = os.path.join(output_dir, f"{safe_name}.pdf")

    # Render Jinja2 template to HTML string
    html_string = render_template("invoice_template.html", **invoice_data)

    # WeasyPrint converts HTML → PDF; base_url allows relative asset resolution
    HTML(string=html_string, base_url=current_app.root_path).write_pdf(output_path)

    return os.path.abspath(output_path)


def generate_po_pdf(po_data: dict, output_dir: str = None) -> str:
    """
    Render a purchase order as a PDF file using WeasyPrint.

    Args:
        po_data:    Dict containing PO fields, vendor info, and line items.
                    Used by po_template.html.
        output_dir: Directory to save the PDF. Defaults to
                    app.config['PDF_OUTPUT_DIR'].

    Returns:
        The absolute file path of the generated PDF.
    """
    from weasyprint import HTML

    if output_dir is None:
        output_dir = current_app.config.get("PDF_OUTPUT_DIR", "generated_pdfs")

    os.makedirs(output_dir, exist_ok=True)

    po_number = po_data.get("po_number", "PO-UNKNOWN")
    safe_name = po_number.replace("/", "-").replace("\\", "-")
    output_path = os.path.join(output_dir, f"{safe_name}.pdf")

    html_string = render_template("po_template.html", **po_data)

    HTML(string=html_string, base_url=current_app.root_path).write_pdf(output_path)

    return os.path.abspath(output_path)
