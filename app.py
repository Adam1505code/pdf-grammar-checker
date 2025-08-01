from flask import Flask, render_template, request
import fitz  # PyMuPDF
import language_tool_python
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

tool = language_tool_python.LanguageTool('en-US')

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files['pdf']
        if file and file.filename.endswith(".pdf"):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            text = extract_text(filepath)
            matches = tool.check(text)
            issues = [{
                "message": m.message,
                "context": m.context,
                "suggestions": m.replacements
            } for m in matches]
            return render_template("index.html", text=text, issues=issues)
    return render_template("index.html", text=None, issues=None)

if __name__ == "__main__":
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
