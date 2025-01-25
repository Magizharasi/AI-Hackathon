from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import re
import spacy
import PyPDF2
import docx
import pdfkit
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import webbrowser

app = Flask(__name__)

# Folder configurations
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_text_from_file(file_path):
    """Extract text from PDF, DOCX, or TXT files."""
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.pdf':
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ' '.join([page.extract_text() for page in reader.pages])
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
    """Extract skills from text using a predefined list and regex."""
    skill_list = [
        'Python', 'Java', 'JavaScript', 'SQL', 'C++', 'React', 'Angular',
        'Node.js', 'Machine Learning', 'Data Analysis', 'Docker', 'Kubernetes',
        'AWS', 'Azure', 'Google Cloud', 'Git', 'REST API', 'GraphQL',
        'TensorFlow', 'Pandas', 'NumPy', 'Scikit-learn', 'Excel'
    ]
    text_lower = text.lower()
    found_skills = set()
    for skill in skill_list:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
            found_skills.add(skill)
    return list(found_skills)

def generate_resume_pdf(resume_data, output_path):
    """Generate a PDF resume from the given data."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { text-align: center; margin-bottom: 20px; }
            .header h1 { margin: 0; }
            .section { margin-bottom: 20px; }
            .section h2 { border-bottom: 2px solid #333; padding-bottom: 5px; }
            ul { list-style-type: square; margin: 0; padding: 0; }
            ul li { margin: 5px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{{ name }}</h1>
            <p>{{ title }}</p>
            <p>Email: {{ contact.email }} | Phone: {{ contact.phone }}</p>
        </div>
        <div class="section">
            <h2>Professional Summary</h2>
            <p>{{ professional_summary }}</p>
        </div>
        <div class="section">
            <h2>Matched Skills</h2>
            <ul>
                {% for skill in matched_skills %}
                <li>{{ skill }}</li>
                {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """
    env = Environment(loader=FileSystemLoader('.'))
    template = env.from_string(html_template)
    html_content = template.render(resume_data)
    config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
    pdfkit.from_string(html_content, output_path, configuration=config)

def generate_skill_pie_chart(matching_skills, jd_skills, output_path):
    """Generate a pie chart for skill match analysis."""
    labels = ['Matched Skills', 'Remaining JD Skills']
    sizes = [len(matching_skills), len(jd_skills) - len(matching_skills)]
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
        # Save uploaded files
        resume_file = request.files['resume']
        jd_file = request.files['job_description']
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(resume_file.filename))
        jd_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(jd_file.filename))
        resume_file.save(resume_path)
        jd_file.save(jd_path)

        # Extract text and skills
        resume_text = extract_text_from_file(resume_path)
        jd_text = extract_text_from_file(jd_path)
        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills(jd_text)

        # Find matching and unique skills
        matching_skills = list(set(resume_skills) & set(jd_skills))
        percentage_match = round((len(matching_skills) / len(jd_skills)) * 100, 2) if jd_skills else 0

        # Generate pie chart
        pie_chart_path = os.path.join(app.config['OUTPUT_FOLDER'], 'skill_pie_chart.png')
        generate_skill_pie_chart(matching_skills, jd_skills, pie_chart_path)

        # Generate PDF resume
        pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], 'resume.pdf')
        updated_resume_data = {
            "name": "John Doe",
            "title": "Software Developer",
            "contact": {"email": "johndoe@example.com", "phone": "123-456-7890"},
            "professional_summary": (
                "A highly motivated software developer with expertise in designing, "
                "developing, and maintaining complex applications."
            ),
            "matched_skills": matching_skills
        }
        generate_resume_pdf(updated_resume_data, pdf_path)

        # Return analysis results
        return jsonify({
            'matching_skills': matching_skills,
            'percentage_match': percentage_match,
            'pie_chart_path': '/output/skill_pie_chart.png',
            'pdf_path': '/output/resume.pdf'
        })

    except Exception as e:
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
