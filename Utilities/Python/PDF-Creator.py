from fpdf import FPDF
from fpdf.enums import XPos, YPos
from typing import Dict, List, Optional, Any

class CustomPDF(FPDF):
    """
    Generic PDF class for creating structured documents with cover page, sections, and tables.
    Extend or modify as needed for your document structure.
    """
    def header(self):
        if self.page_no() == 1:
            return  # No header on cover page
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(40, 40, 40)
        # Edit the document title below or pass as an argument if needed
        self.cell(0, 10, 'Document Title', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return  # No footer on cover page
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def cover_page(self, title: str, subtitle: str = ""):
        self.add_page()
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(30, 30, 80)
        self.cell(0, 60, '', new_x=XPos.LMARGIN, new_y=YPos.NEXT)  # Spacer
        self.cell(0, 20, title, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if subtitle:
            self.set_font('Helvetica', '', 14)
            self.set_text_color(60, 60, 60)
            self.cell(0, 10, subtitle, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(20)

    def section_title(self, title: str):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(0, 70, 140)
        self.ln(8)
        self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)

    def section_body(self, body: str):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 8, body)
        self.ln(2)

    def add_table(self, table_data: List[Dict[str, str]], col_widths: List[int], col_names: List[str]):
        """
        Add a table to the PDF.
        table_data: List of dicts, each dict is a row with column names as keys.
        col_widths: List of column widths (ints).
        col_names: List of column names (headers, must match dict keys).
        """
        self.set_font('Helvetica', 'B', 11)
        self.set_fill_color(220, 230, 241)
        row_height = 10
        # Header
        for i, col_name in enumerate(col_names):
            self.cell(col_widths[i], row_height, col_name, border=1, fill=True, align='C')
        self.ln(row_height)
        self.set_font('Helvetica', '', 10)
        # Rows
        for row in table_data:
            for i, col_name in enumerate(col_names):
                self.multi_cell(col_widths[i], row_height, row.get(col_name, ''), border=1, align='L', max_line_height=self.font_size)
                self.set_xy(self.get_x() + col_widths[i], self.get_y() - row_height)
            self.ln(row_height)

def generate_pdf_document(
    output_path: str,
    title: str,
    subtitle: str,
    sections: List[Dict[str, str]],
    tables: Optional[List[Optional[Dict[str, Any]]]] = None
) -> None:
    """
    Generate a generic PDF document.
    sections: List of dicts with 'title' and 'body' keys.
    tables: List of dicts with 'data', 'col_widths', and 'col_names' keys (optional).
    """
    pdf = CustomPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.cover_page(title=title, subtitle=subtitle)
    pdf.add_page()
    for i, section in enumerate(sections):
        pdf.section_title(section['title'])
        pdf.section_body(section['body'])
        # Optionally add a table after a section
        if tables and i < len(tables):
            table = tables[i]
            if (
                table and isinstance(table, dict)
                and 'data' in table and 'col_widths' in table and 'col_names' in table
            ):
                # Cast to correct types for linter
                data = table['data'] if isinstance(table['data'], list) else []
                col_widths = table['col_widths'] if isinstance(table['col_widths'], list) else []
                col_names = table['col_names'] if isinstance(table['col_names'], list) else []
                pdf.add_table(
                    table_data=data,
                    col_widths=col_widths,
                    col_names=col_names
                )
    pdf.output(output_path)
    print(f"PDF created successfully at {output_path}")

# Example usage for any document type
if __name__ == "__main__":
    # Example: Replace with your own document structure and data
    sections = [
        {
            'title': 'Introduction',
            'body': 'This is a generic PDF document. You can add any sections you want.\nJust update the sections list with your own titles and content.'
        },
        {
            'title': 'Details',
            'body': 'You can add more sections as needed. Each section can have a title and body text.'
        },
        {
            'title': 'Summary',
            'body': 'This is the summary section. Add your conclusions or final notes here.'
        }
    ]
    # Example table (optional)
    tables = [
        None,  # No table for first section
        {
            'data': [
                {'Item': 'Apple', 'Quantity': '3', 'Price': '$2'},
                {'Item': 'Banana', 'Quantity': '5', 'Price': '$1'},
            ],
            'col_widths': [40, 40, 40],
            'col_names': ['Item', 'Quantity', 'Price']
        },
        None  # No table for third section
    ]
    # Only add tables where needed (None for sections without tables)
    generate_pdf_document(
        output_path="example_document.pdf",
        title="Generic PDF Document",
        subtitle="A Template for Any Structured PDF",
        sections=sections,
        tables=tables
    ) 