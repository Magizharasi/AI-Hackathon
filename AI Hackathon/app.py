from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import PyPDF2
import docx
import spacy
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import webbrowser

app = Flask(__name__)

# Folder configurations
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Predefined list of skills (can be expanded)
SKILL_LIST = [
    "Python", "Java", "JavaScript", "SQL", "C++", "React", "Angular",
    "Node.js", "Machine Learning", "Data Analysis", "Docker", "Kubernetes",
    "AWS", "Azure", "Google Cloud", "Git", "REST API", "GraphQL",
    "TensorFlow", "Pandas", "NumPy", "Scikit-learn", "Excel"
]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_text_from_file(file_path):
    """Extract text from PDF, DOCX, or TXT files."""
    file_extension = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if file_extension == '.pdf':
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ' '.join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    elif file_extension in ['.docx', '.doc']:
        doc = docx.Document(file_path)
        text = ' '.join([paragraph.text for paragraph in doc.paragraphs])
    
    elif file_extension == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    
    else:
        raise ValueError("Unsupported file type")
    
    return text

def extract_skills(text):
    """Extract skills using spaCy NLP processing."""
    doc = nlp(text)
    extracted_skills = {token.text for token in doc if token.text in SKILL_LIST}
    return list(extracted_skills)

def generate_skill_pie_chart(matching_skills, jd_skills, output_path):
    """Generate a pie chart for skill match analysis."""
    labels = ['Matched Skills', 'Remaining JD Skills']
    sizes = [len(matching_skills), max(len(jd_skills) - len(matching_skills), 1)]
    colors = ['#4CAF50', '#FF5733']
    explode = (0.1, 0)

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    plt.title('Skill Match Analysis')
    plt.savefig(output_path)
    plt.close()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        resume_file = request.files.get('resume')
        jd_file = request.files.get('job_description')

        if not resume_file or not jd_file:
            return jsonify({'error': 'Both resume and job description files are required'}), 400

        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(resume_file.filename))
        jd_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(jd_file.filename))
        resume_file.save(resume_path)
        jd_file.save(jd_path)

        resume_text = extract_text_from_file(resume_path)
        jd_text = extract_text_from_file(jd_path)
        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills(jd_text)

        matching_skills = list(set(resume_skills) & set(jd_skills))
        percentage_match = round((len(matching_skills) / max(len(jd_skills), 1)) * 100, 2)

        pie_chart_path = os.path.join(app.config['OUTPUT_FOLDER'], 'skill_pie_chart.png')
        generate_skill_pie_chart(matching_skills, jd_skills, pie_chart_path)

        result = {
            'matching_skills': matching_skills,
            'percentage_match': percentage_match,
            'pie_chart_path': f'/output/skill_pie_chart.png'
        }
        print("Analysis Result:", result)  # Debugging log
        return jsonify(result)

    except Exception as e:
        print("Error:", str(e))  # Debugging log
        return jsonify({'error': str(e)}), 500

@app.route('/output/<path:filename>')
def download_file(filename):
    """Serve the generated files."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == "__main__":
    port = 5000
    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)
    app.run(debug=True, port=port)
