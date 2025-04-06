import json
import base64
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
from PIL import Image

class NotebookReportPDF(FPDF):
    def __init__(self, student_name="", assignment_name=""):
        super().__init__()
        self.student_name = student_name
        self.assignment_name = assignment_name
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, f"Jupyter Notebook Assignment Report", ln=True, align="C")
        self.set_font("Arial", "", 12)
        self.cell(0, 10, f"Student: {student_name}", ln=True)
        self.cell(0, 10, f"Assignment: {assignment_name}", ln=True)
        self.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        self.ln(10)
    
    def add_cell_marker(self, cell_type, cell_number):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(220, 220, 220)
        self.cell(0, 10, f"Cell {cell_number} ({cell_type})", ln=True, fill=True)
        self.ln(5)
    
    def add_code(self, code):
        self.set_font("Courier", "", 10)
        self.set_fill_color(240, 240, 240)
        self.multi_cell(0, 5, code, fill=True)
        self.ln(5)
    
    def add_markdown(self, text):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 5, text)
        self.ln(5)
    
    def add_output(self, output_text):
        self.set_font("Courier", "", 10)
        self.multi_cell(0, 5, output_text)
        self.ln(5)
    
    def add_image(self, img_data):
        try:
            # Handle base64 image data
            image = BytesIO(base64.b64decode(img_data))
            pil_img = Image.open(image)
            
            # Calculate dimensions to fit page width while maintaining aspect ratio
            page_width = self.w - 2 * self.l_margin
            img_width = min(page_width, pil_img.width)
            img_height = (pil_img.height * img_width) / pil_img.width
            
            # Save the image to a temporary file
            temp_img = BytesIO()
            pil_img.save(temp_img, format='PNG')
            temp_img.seek(0)
            
            # Add the image to the PDF
            x = self.l_margin + (page_width - img_width) / 2
            self.image(temp_img, x=x, w=img_width)
            self.ln(5)
        except Exception as e:
            self.set_text_color(255, 0, 0)
            self.multi_cell(0, 5, f"Error displaying image: {str(e)}")
            self.set_text_color(0, 0, 0)
            self.ln(5)

def process_notebook(notebook_file, student_name, assignment_name):
    # Load the notebook
    if isinstance(notebook_file, str):
        with open(notebook_file, 'r', encoding='utf-8') as f:
            notebook_content = json.load(f)
    else:
        notebook_content = json.load(notebook_file)
    
    # Create PDF
    pdf = NotebookReportPDF(student_name, assignment_name)
    
    # Process each cell
    for i, cell in enumerate(notebook_content.get('cells', [])):
        cell_type = cell.get('cell_type', 'unknown')
        cell_number = i + 1
        
        # Add cell marker
        pdf.add_cell_marker(cell_type, cell_number)
        
        # Process based on cell type
        if cell_type == 'code':
            # Add code content
            source = ''.join(cell.get('source', []))
            pdf.add_code(source)
            
            # Process outputs
            outputs = cell.get('outputs', [])
            for output in outputs:
                output_type = output.get('output_type', '')
                
                # Text output
                if output_type == 'stream':
                    pdf.add_output(f"{output.get('name', 'output')}: {''.join(output.get('text', []))}")
                
                # Display data (often contains images)
                elif output_type == 'display_data' or output_type == 'execute_result':
                    data = output.get('data', {})
                    
                    # Handle text/plain output
                    if 'text/plain' in data:
                        text_content = ''.join(data['text/plain'])
                        pdf.add_output(text_content)
                    
                    # Handle images
                    if 'image/png' in data:
                        pdf.add_image(data['image/png'])
                        
                    # Handle HTML (simplified as text)
                    elif 'text/html' in data:
                        html_content = ''.join(data['text/html'])
                        pdf.add_output(f"HTML Output: {html_content[:200]}...")
                        
                # Error output
                elif output_type == 'error':
                    error_name = output.get('ename', 'Error')
                    error_value = output.get('evalue', '')
                    traceback = '\n'.join(output.get('traceback', []))
                    pdf.set_text_color(255, 0, 0)
                    pdf.add_output(f"{error_name}: {error_value}\n{traceback}")
                    pdf.set_text_color(0, 0, 0)
        
        elif cell_type == 'markdown':
            # Process markdown content
            markdown_text = ''.join(cell.get('source', []))
            pdf.add_markdown(markdown_text)
    
    return pdf