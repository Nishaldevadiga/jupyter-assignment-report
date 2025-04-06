from flask import Flask, request, render_template, send_file
from io import BytesIO
from report_generator import process_notebook

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'notebook' not in request.files:
            return render_template('upload.html', error='No file part')
        
        notebook_file = request.files['notebook']
        if notebook_file.filename == '':
            return render_template('upload.html', error='No selected file')
        
        if notebook_file and notebook_file.filename.endswith('.ipynb'):
            student_name = request.form.get('student_name', 'Unknown Student')
            assignment_name = request.form.get('assignment_name', 'Unknown Assignment')
            
            # Process notebook
            pdf = process_notebook(notebook_file, student_name, assignment_name)
            
            # Save to memory
            pdf_output = BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)
            
            # Return the PDF file
            return send_file(
                pdf_output,
                as_attachment=True,
                download_name=f"{student_name}_{assignment_name}_report.pdf",
                mimetype='application/pdf'
            )
        
        return render_template('upload.html', error='Invalid file format. Please upload .ipynb files only')
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)