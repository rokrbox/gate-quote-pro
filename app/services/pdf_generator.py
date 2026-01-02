"""PDF quote generation service for Gate Quote Pro."""
import os
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from ..models.quote import Quote
from ..models.database import get_db


class PDFGenerator:
    """Generate professional PDF quotes."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=6,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='CompanyInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_CENTER,
            spaceAfter=2
        ))

        self.styles.add(ParagraphStyle(
            name='QuoteTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#2d3748'),
            spaceBefore=20,
            spaceAfter=20,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1a365d'),
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='CustomerInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=2
        ))

        self.styles.add(ParagraphStyle(
            name='Terms',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#718096'),
            spaceBefore=20
        ))

        self.styles.add(ParagraphStyle(
            name='Total',
            parent=self.styles['Normal'],
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a365d'),
            alignment=TA_RIGHT
        ))

    def generate(self, quote: Quote, output_path: str = None) -> str:
        """Generate PDF quote and return the file path."""
        db = get_db()
        settings = db.get_all_settings()

        # Determine output path
        if output_path is None:
            downloads = Path.home() / "Downloads"
            downloads.mkdir(exist_ok=True)
            filename = f"Quote_{quote.quote_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
            output_path = str(downloads / filename)

        # Create PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        story = []

        # Company Header
        story.append(Paragraph(settings.get('company_name', 'Your Gate Company'), self.styles['CompanyName']))

        if settings.get('company_address'):
            story.append(Paragraph(settings['company_address'], self.styles['CompanyInfo']))

        contact_parts = []
        if settings.get('company_phone'):
            contact_parts.append(settings['company_phone'])
        if settings.get('company_email'):
            contact_parts.append(settings['company_email'])
        if contact_parts:
            story.append(Paragraph(' | '.join(contact_parts), self.styles['CompanyInfo']))

        if settings.get('company_license'):
            story.append(Paragraph(f"License: {settings['company_license']}", self.styles['CompanyInfo']))

        # Quote Title
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"QUOTE #{quote.quote_number}", self.styles['QuoteTitle']))

        # Quote Date and Status
        date_str = datetime.now().strftime('%B %d, %Y')
        story.append(Paragraph(f"Date: {date_str}", self.styles['CustomerInfo']))
        story.append(Paragraph(f"Status: {quote.status.upper()}", self.styles['CustomerInfo']))

        # Customer Information
        if quote.customer:
            story.append(Spacer(1, 15))
            story.append(Paragraph("CUSTOMER", self.styles['SectionHeader']))
            story.append(Paragraph(quote.customer.name, self.styles['CustomerInfo']))
            if quote.customer.address:
                story.append(Paragraph(quote.customer.address, self.styles['CustomerInfo']))
            if quote.customer.city or quote.customer.state:
                city_state = f"{quote.customer.city}, {quote.customer.state} {quote.customer.zip_code}".strip()
                story.append(Paragraph(city_state, self.styles['CustomerInfo']))
            if quote.customer.phone:
                story.append(Paragraph(f"Phone: {quote.customer.phone}", self.styles['CustomerInfo']))
            if quote.customer.email:
                story.append(Paragraph(f"Email: {quote.customer.email}", self.styles['CustomerInfo']))

        # Project Specifications
        story.append(Spacer(1, 15))
        story.append(Paragraph("PROJECT SPECIFICATIONS", self.styles['SectionHeader']))

        specs_data = [
            ['Gate Type:', self._format_value(quote.gate_type), 'Material:', self._format_value(quote.material)],
            ['Width:', f"{quote.width} ft", 'Height:', f"{quote.height} ft"],
            ['Style:', self._format_value(quote.gate_style), 'Automation:', self._format_value(quote.automation)],
            ['Access Control:', self._format_value(quote.access_control), 'Ground Type:', self._format_value(quote.ground_type)],
        ]

        specs_table = Table(specs_data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch])
        specs_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(specs_table)

        # Materials/Line Items
        if quote.items:
            story.append(Spacer(1, 15))
            story.append(Paragraph("MATERIALS & EQUIPMENT", self.styles['SectionHeader']))

            items_data = [['Description', 'Qty', 'Unit', 'Unit Price', 'Total']]
            for item in quote.items:
                items_data.append([
                    item.description,
                    f"{item.quantity:.1f}",
                    item.unit,
                    f"${item.unit_cost:.2f}",
                    f"${item.total_cost:.2f}"
                ])

            items_table = Table(items_data, colWidths=[3 * inch, 0.6 * inch, 0.6 * inch, 1 * inch, 1 * inch])
            items_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(items_table)

        # Labor
        story.append(Spacer(1, 15))
        story.append(Paragraph("LABOR", self.styles['SectionHeader']))

        labor_cost = quote.labor_hours * quote.labor_rate
        labor_data = [
            ['Description', 'Hours', 'Rate', 'Total'],
            ['Professional Installation', f"{quote.labor_hours:.2f}", f"${quote.labor_rate:.2f}/hr", f"${labor_cost:.2f}"]
        ]

        labor_table = Table(labor_data, colWidths=[3.6 * inch, 1 * inch, 1.2 * inch, 1 * inch])
        labor_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(labor_table)

        # Totals
        story.append(Spacer(1, 20))

        materials_with_markup = quote.materials_cost * (1 + quote.markup_percent / 100)

        totals_data = [
            ['Materials (with markup):', f"${materials_with_markup:.2f}"],
            ['Labor:', f"${labor_cost:.2f}"],
            ['Subtotal:', f"${quote.subtotal:.2f}"],
        ]

        if quote.tax_rate > 0:
            totals_data.append(['Tax ({:.1f}%):'.format(quote.tax_rate), f"${quote.tax_amount:.2f}"])

        totals_data.append(['TOTAL:', f"${quote.total:.2f}"])

        totals_table = Table(totals_data, colWidths=[5 * inch, 1.5 * inch])
        totals_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a365d')),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a365d')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(totals_table)

        # Notes
        if quote.notes:
            story.append(Spacer(1, 15))
            story.append(Paragraph("NOTES", self.styles['SectionHeader']))
            story.append(Paragraph(quote.notes, self.styles['CustomerInfo']))

        # Terms and Conditions
        terms = settings.get('quote_terms', 'Quote valid for 30 days. 50% deposit required to begin work.')
        story.append(Spacer(1, 25))
        story.append(Paragraph("TERMS & CONDITIONS", self.styles['SectionHeader']))
        story.append(Paragraph(terms, self.styles['Terms']))

        # Build PDF
        doc.build(story)

        return output_path

    def _format_value(self, value: str) -> str:
        """Format a value for display (capitalize, replace underscores)."""
        if not value:
            return "N/A"
        return value.replace('_', ' ').title()


# Global generator instance
_generator = None


def get_pdf_generator() -> PDFGenerator:
    """Get the global PDF generator instance."""
    global _generator
    if _generator is None:
        _generator = PDFGenerator()
    return _generator
