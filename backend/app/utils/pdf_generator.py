"""
VendorBridge ERP – PDF Generator
==================================
Uses WeasyPrint to render HTML templates into PDF documents.
Primarily used for invoice PDF generation.
"""

import os
import logging

logger = logging.getLogger(__name__)


def _get_output_dir() -> str:
    """Get PDF output directory from config or default."""
    output_dir = os.environ.get("PDF_OUTPUT_DIR", "generated_pdfs")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _render_invoice_html(data: dict) -> str:
    """Build a professional HTML invoice from data dict."""
    items_rows = ""
    for i, item in enumerate(data.get("items", []), 1):
        items_rows += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{i}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{item['item_name']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:center;">{item.get('hsn_code', '')}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;">{item['quantity']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;">₹{item['unit_price']}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;">{item['tax_rate']}%</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:600;">₹{item['line_total']}</td>
        </tr>
        """

    # Build GST section
    gst_section = ""
    cgst = data.get("cgst_amount", "0.00")
    sgst = data.get("sgst_amount", "0.00")
    igst = data.get("igst_amount", "0.00")

    if float(igst) > 0:
        gst_section = f"""
        <tr><td style="padding:6px 12px;text-align:right;">IGST:</td>
            <td style="padding:6px 12px;text-align:right;">₹{igst}</td></tr>
        """
    else:
        gst_section = f"""
        <tr><td style="padding:6px 12px;text-align:right;">CGST:</td>
            <td style="padding:6px 12px;text-align:right;">₹{cgst}</td></tr>
        <tr><td style="padding:6px 12px;text-align:right;">SGST:</td>
            <td style="padding:6px 12px;text-align:right;">₹{sgst}</td></tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: #1f2937;
                margin: 0;
                padding: 40px;
                font-size: 13px;
                line-height: 1.5;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 30px;
                border-bottom: 3px solid #3b82f6;
                padding-bottom: 20px;
            }}
            .company-name {{
                font-size: 24px;
                font-weight: 700;
                color: #1e40af;
                margin: 0;
            }}
            .invoice-title {{
                font-size: 28px;
                font-weight: 700;
                color: #3b82f6;
                text-align: right;
            }}
            .meta-grid {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
            }}
            .meta-box {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                width: 48%;
            }}
            .meta-box h4 {{
                margin: 0 0 8px 0;
                color: #64748b;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .meta-box p {{
                margin: 2px 0;
                font-size: 13px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            thead th {{
                background: #1e40af;
                color: white;
                padding: 10px 12px;
                text-align: left;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
            thead th:last-child, thead th:nth-child(4),
            thead th:nth-child(5), thead th:nth-child(6) {{
                text-align: right;
            }}
            .totals-table {{
                width: 300px;
                margin-left: auto;
            }}
            .totals-table td {{
                padding: 6px 12px;
            }}
            .grand-total td {{
                font-size: 16px;
                font-weight: 700;
                border-top: 2px solid #1e40af;
                color: #1e40af;
                padding-top: 10px;
            }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                color: #94a3b8;
                font-size: 11px;
                border-top: 1px solid #e2e8f0;
                padding-top: 15px;
            }}
            .notes {{
                background: #fffbeb;
                border: 1px solid #fde68a;
                border-radius: 6px;
                padding: 12px;
                margin-top: 20px;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <p class="company-name">⬡ VendorBridge</p>
                <p style="color:#64748b;margin:4px 0;">Procurement Management System</p>
            </div>
            <div style="text-align:right;">
                <p class="invoice-title">TAX INVOICE</p>
                <p style="margin:4px 0;"><strong>{data['invoice_number']}</strong></p>
            </div>
        </div>

        <div class="meta-grid">
            <div class="meta-box">
                <h4>Invoice Details</h4>
                <p><strong>Invoice #:</strong> {data['invoice_number']}</p>
                <p><strong>Date:</strong> {data['invoice_date']}</p>
                <p><strong>Due Date:</strong> {data['due_date']}</p>
                <p><strong>PO Ref:</strong> {data['po_number']}</p>
            </div>
            <div class="meta-box">
                <h4>Vendor</h4>
                <p><strong>{data['vendor_name']}</strong></p>
                <p>{data.get('vendor_address', '')}</p>
                <p>{data.get('vendor_city', '')}, {data.get('vendor_state', '')}</p>
                <p><strong>GSTIN:</strong> {data.get('vendor_gst', '')}</p>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Item</th>
                    <th style="text-align:center;">HSN</th>
                    <th style="text-align:right;">Qty</th>
                    <th style="text-align:right;">Unit Price</th>
                    <th style="text-align:right;">Tax Rate</th>
                    <th style="text-align:right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
            </tbody>
        </table>

        <table class="totals-table">
            <tr>
                <td style="text-align:right;">Subtotal:</td>
                <td style="text-align:right;">₹{data['subtotal']}</td>
            </tr>
            {gst_section}
            <tr class="grand-total">
                <td style="text-align:right;">TOTAL:</td>
                <td style="text-align:right;">₹{data['total_amount']}</td>
            </tr>
        </table>

        {"<div class='notes'><strong>Notes:</strong> " + data['notes'] + "</div>" if data.get('notes') else ""}

        <div class="footer">
            <p>Generated by VendorBridge ERP • This is a computer-generated invoice</p>
        </div>
    </body>
    </html>
    """
    return html


def generate_invoice_pdf(invoice_data: dict, output_dir: str = None) -> str:
    """
    Render an invoice as a PDF file.

    Args:
        invoice_data: Dict containing all invoice fields, items, and
                      company/vendor info needed for the template.
        output_dir: Directory to save the PDF. Defaults to
                    PDF_OUTPUT_DIR env var.

    Returns:
        The absolute file path of the generated PDF.
    """
    if output_dir is None:
        output_dir = _get_output_dir()
    else:
        os.makedirs(output_dir, exist_ok=True)

    filename = f"INV-{invoice_data['invoice_number']}.pdf"
    output_path = os.path.join(output_dir, filename)

    html_content = _render_invoice_html(invoice_data)

    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)
        logger.info(f"Invoice PDF generated: {output_path}")
    except ImportError:
        # WeasyPrint not installed — save HTML as fallback
        fallback_path = output_path.replace(".pdf", ".html")
        with open(fallback_path, "w") as f:
            f.write(html_content)
        logger.warning(
            f"WeasyPrint not available. Saved HTML fallback: {fallback_path}"
        )
        output_path = fallback_path
    except Exception as e:
        logger.exception(f"PDF generation failed for {invoice_data['invoice_number']}")
        raise

    return os.path.abspath(output_path)


def generate_po_pdf(po_data: dict, output_dir: str = None) -> str:
    """
    Render a purchase order as a PDF file.
    """
    # Reuse invoice pattern but with PO-specific template
    if output_dir is None:
        output_dir = _get_output_dir()
    else:
        os.makedirs(output_dir, exist_ok=True)

    filename = f"PO-{po_data.get('po_number', 'UNKNOWN')}.pdf"
    output_path = os.path.join(output_dir, filename)

    # Minimal PO PDF — can be expanded later
    html_content = f"""
    <html><body>
    <h1>Purchase Order: {po_data.get('po_number', 'N/A')}</h1>
    <p>Vendor: {po_data.get('vendor_name', 'N/A')}</p>
    <p>Total: ₹{po_data.get('total_amount', '0.00')}</p>
    </body></html>
    """

    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)
    except ImportError:
        fallback_path = output_path.replace(".pdf", ".html")
        with open(fallback_path, "w") as f:
            f.write(html_content)
        output_path = fallback_path

    return os.path.abspath(output_path)
