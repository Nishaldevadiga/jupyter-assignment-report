from flask import Flask, request, render_template, send_file
from io import BytesIO
import traceback

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
            
            try:
                # Process notebook to generate LaTeX
                latex_content = process_notebook(notebook_file, student_name, assignment_name)
                
                # Save to BytesIO
                latex_output = BytesIO()
                latex_output.write(latex_content.encode('utf-8'))
                latex_output.seek(0)  # Reset pointer to beginning
                
                # Return the LaTeX file
                return send_file(
                    latex_output,
                    as_attachment=True,
                    download_name=f"{student_name}_{assignment_name}_report.tex",
                    mimetype='application/x-tex'
                )
            except Exception as e:
                error_details = traceback.format_exc()
                return render_template('upload.html', error=f'Error processing notebook: {str(e)}\n{error_details}')
        
        return render_template('upload.html', error='Invalid file format. Please upload .ipynb files only')
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)