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

def highlight_errors(text, matches):
    """
    Highlight errors in text with red and show corrections in blue
    """
    # Sort matches by offset in reverse order to avoid offset issues when replacing
    sorted_matches = sorted(matches, key=lambda x: x.offset, reverse=True)
    
    # Convert text to list for easier manipulation
    text_list = list(text)
    
    for match in sorted_matches:
        error_start = match.offset
        error_end = match.offset + match.errorLength
        
        # Create highlighted error text
        error_text = f'<span class="error">{text[error_start:error_end]}</span>'
        
        # Create correction text if available
        if match.replacements:
            correction_text = f'<span class="correction">{match.replacements[0]}</span>'
            replacement_text = f'{error_text} <span class="suggestion">→ {correction_text}</span>'
        else:
            replacement_text = error_text
        
        # Replace the error text with the highlighted version
        text_list[error_start:error_end] = replacement_text
    
    return ''.join(text_list)

@app.route("/", methods=["GET", "POST"])
def index():
    text = None
    issues = None
    highlighted_text = None
    
    if request.method == "POST":
        # Check if PDF was uploaded
        if 'pdf' in request.files:
            file = request.files['pdf']
            if file and file.filename.endswith(".pdf"):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                text = extract_text(filepath)
        
        # Check if text was pasted
        elif 'text_input' in request.form:
            text = request.form['text_input']
            # Limit to 3500 words if needed
            if len(text.split()) > 3500:
                words = text.split()[:3500]
                text = ' '.join(words)
        
        # Process text if available
        if text:
            matches = tool.check(text)
            issues = [{
                "message": m.message,
                "context": m.context,
                "suggestions": m.replacements
            } for m in matches]
            
            # Create highlighted version of the text
            highlighted_text = highlight_errors(text, matches)
    
    return render_template("index.html", text=text, issues=issues, highlighted_text=highlighted_text)

if __name__ == "__main__":
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
