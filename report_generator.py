import json
import base64
from datetime import datetime
import tempfile
import os
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import re

class NotebookReportLaTeX:
    def __init__(self, student_name="", assignment_name=""):
        self.student_name = student_name
        self.assignment_name = assignment_name
        self.content = []
        self.image_counter = 1
        self.images_dir = "images"
        
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        self.add_preamble()
        self.add_title()

    def add_preamble(self):
        preamble = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{hyperref}
\usepackage{geometry}

\geometry{margin=1in}

\lstset{
    backgroundcolor=\color{lightgray!30},
    basicstyle=\ttfamily\small,
    breaklines=true,
    captionpos=b,
    commentstyle=\color{green},
    frame=single,
    keywordstyle=\color{blue},
    showstringspaces=false,
    stringstyle=\color{purple},
}

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
}

\pagestyle{fancy}
\fancyhf{}
\rhead{Jupyter Notebook Report}
\lhead{Generated: \today}
\cfoot{\thepage}
"""
        self.content.append(preamble)

    def add_title(self):
        title_section = r"""
\begin{document}

\begin{center}
\Large\textbf{Jupyter Notebook Assignment Report}

\vspace{0.5cm}
\normalsize
Student: """ + self.student_name + r"""

Assignment: """ + self.assignment_name + r"""

Date: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + r"""
\end{center}

\vspace{1cm}
"""
        self.content.append(title_section)

    def add_cell_marker(self, cell_type, cell_number):
        marker = f"""
\\vspace{{0.5cm}}
\\noindent\\colorbox{{lightgray}}{{\\textbf{{Cell {cell_number} ({cell_type})}}}}
\\vspace{{0.3cm}}
"""
        self.content.append(marker)

    def _fix_code_special_chars(self, text):
        """Handle special characters in code listings"""
        if not isinstance(text, str):
            text = str(text)
        
        # Process the code to handle LaTeX special characters in code
        text = text.replace('\\', '\\\\')
        
        special_chars = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '^': '\\^{}',
            '~': '\\~{}'
        }
        
        for char, replacement in special_chars.items():
            if char != '\\':
                text = text.replace(char, replacement)
        
        return text

    def add_code(self, code):
        code = self._fix_code_special_chars(code)
        
        listing = f"""
\\begin{{lstlisting}}[language=Python]
{code}
\\end{{lstlisting}}
"""
        self.content.append(listing)

    def add_markdown(self, text):
        text = self._markdown_to_latex(text)
        
        markdown_section = f"""
\\begin{{quote}}
{text}
\\end{{quote}}
"""
        self.content.append(markdown_section)

    def add_raw(self, text, format_type=""):
        text = self._escape_latex(text)
        
        raw_section = f"""
\\begin{{quote}}
\\textit{{Format: {format_type}}}

\\begin{{verbatim}}
{text}
\\end{{verbatim}}
\\end{{quote}}
"""
        self.content.append(raw_section)

    def add_output(self, output_text):
        output_section = f"""
\\begin{{verbatim}}
{output_text}
\\end{{verbatim}}
"""
        self.content.append(output_section)

    def add_image(self, img_data):
        try:
            if not os.path.exists(self.images_dir):
                os.makedirs(self.images_dir)
                
            image_filename = f"image_{self.image_counter}.png"
            full_image_path = os.path.join(self.images_dir, image_filename)
            
            image_data = base64.b64decode(img_data)
            with open(full_image_path, 'wb') as f:
                f.write(image_data)
            
            image_section = f"""
\\begin{{figure}}[h]
\\centering
\\includegraphics[width=0.8\\textwidth]{{{self.images_dir}/{image_filename}}}
\\caption{{Output Image {self.image_counter}}}
\\end{{figure}}
"""
            self.content.append(image_section)
            self.image_counter += 1
            
        except Exception as e:
            error_msg = f"Error displaying image: {str(e)}"
            self.content.append(f"\\textcolor{{red}}{{{self._escape_latex(error_msg)}}}")

    def _escape_latex(self, text):
        if not isinstance(text, str):
            text = str(text)
            
        special_chars = {
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
            '^': '\\textasciicircum{}',
            '\\': '\\textbackslash{}'
        }
        
        for char, replacement in special_chars.items():
            text = text.replace(char, replacement)
            
        return text

    def _markdown_to_latex(self, text):
        text = self._escape_latex(text)
        
        text = re.sub(r'^# (.*?)$', r'\\section*{\1}', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'\\subsection*{\1}', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'\\subsubsection*{\1}', text, flags=re.MULTILINE)
        
        text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
        text = re.sub(r'\*(.*?)\*', r'\\textit{\1}', text)
        
        text = re.sub(r'^- (.*?)$', r'\\begin{itemize}\n\\item \1\n\\end{itemize}', text, flags=re.MULTILINE)
        
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\\href{\2}{\1}', text)
        
        return text

    def finalize(self):
        self.content.append("\n\\end{document}")
        return '\n'.join(self.content)

def process_notebook(notebook_file, student_name, assignment_name):
    if isinstance(notebook_file, str):
        with open(notebook_file, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    else:
        nb = nbformat.read(notebook_file, as_version=4)
    
    if isinstance(notebook_file, str):
        notebook_dir = os.path.dirname(os.path.abspath(notebook_file))
    else:
        notebook_dir = os.getcwd()
    
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    
    try:
        resources = {
            'metadata': {'path': notebook_dir},
        }
        
        executed_nb, _ = ep.preprocess(nb, resources)
        print(f"Successfully executed notebook with {len(executed_nb.cells)} cells")
        nb = executed_nb
    except Exception as e:
        print(f"Error executing notebook: {str(e)}")
        print("Continuing with non-executed notebook for LaTeX generation")

    latex_report = NotebookReportLaTeX(student_name, assignment_name)

    for i, cell in enumerate(nb.get('cells', [])):
        cell_type = cell.get('cell_type', 'unknown')
        cell_number = i + 1

        latex_report.add_cell_marker(cell_type, cell_number)

        if cell_type == 'code':
            source = ''.join(cell.get('source', []))
            latex_report.add_code(source)

            outputs = cell.get('outputs', [])
            for output in outputs:
                output_type = output.get('output_type', '')

                if output_type == 'stream':
                    latex_report.add_output(f"{output.get('name', 'output')}: {''.join(output.get('text', []))}")
                elif output_type in ('display_data', 'execute_result'):
                    data = output.get('data', {})
                    if 'text/plain' in data:
                        text_content = ''.join(data['text/plain']) if isinstance(data['text/plain'], list) else data['text/plain']
                        latex_report.add_output(text_content)
                    if 'image/png' in data:
                        latex_report.add_image(data['image/png'])
                elif output_type == 'error':
                    error_name = output.get('ename', 'Error')
                    error_value = output.get('evalue', '')
                    traceback = '\n'.join(output.get('traceback', []))
                    error_text = f"{error_name}: {error_value}\n{traceback}"
                    latex_report.add_output(error_text)

        elif cell_type == 'markdown':
            markdown_text = ''.join(cell.get('source', []))
            latex_report.add_markdown(markdown_text)
            
        elif cell_type == 'raw':
            raw_text = ''.join(cell.get('source', []))
            metadata = cell.get('metadata', {})
            format_type = metadata.get('format', '')
            if isinstance(format_type, list):
                format_type = ', '.join(format_type)
            latex_report.add_raw(raw_text, format_type)

    return latex_report.finalize()