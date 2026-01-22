import sqlite3
import os
import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "sms_ultimate_final_secret"
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper: Grading Logic
def get_grade(score):
    if score >= 90: return 'A+', 'text-success'
    elif score >= 75: return 'A', 'text-primary'
    elif score >= 60: return 'B', 'text-info'
    elif score >= 40: return 'C', 'text-warning'
    else: return 'F', 'text-danger'

def init_db():
    conn = sqlite3.connect("sms_final.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS students 
                   (sid TEXT PRIMARY KEY, name TEXT, sclass TEXT, maths INTEGER, 
                    science INTEGER, english INTEGER, total INTEGER, 
                    percentage REAL, cgpa REAL, photo TEXT, 
                    mobile TEXT, attendance INTEGER, email TEXT)""")
    conn.commit()
    conn.close()

# Combined UI Header with Dark Mode & Chart.js
UI_HEADER = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<style>
    :root { --bg: #f8fafc; --card: #ffffff; --text: #1e293b; }
    [data-theme='dark'] { --bg: #0f172a; --card: #1e293b; --text: #f1f5f9; }
    body { background-color: var(--bg); color: var(--text); transition: 0.3s; font-family: 'Segoe UI', sans-serif; }
    .glass-card { background: var(--card); border-radius: 15px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: none; }
    .navbar { background: #1e293b; }
    .table { color: inherit; }
    @media print { .no-print { display: none !important; } }
</style>
<nav class="navbar navbar-expand-lg navbar-dark mb-4 no-print">
    <div class="container">
        <a class="navbar-brand fw-bold" href="/"><i class="fas fa-graduation-cap me-2"></i> STUDENT MANAGEMENT SYSTEM</a>
        <div class="navbar-nav ms-auto align-items-center">
            <button onclick="document.documentElement.setAttribute('data-theme', document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark')" class="btn btn-outline-light btn-sm me-3">🌓 Mode</button>
            <a class="nav-link" href="/">Register</a>
            <a class="nav-link" href="/database">Database</a>
            <a class="nav-link text-danger" href="/logout">Logout</a>
        </div>
    </div>
</nav>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['logged_in'] = True
            return redirect(url_for('index'))
    return f"{UI_HEADER}<div class='container mt-5 text-center'><div class='glass-card mx-auto' style='max-width:350px;'><h4>🔑 Admin Login</h4><form method='POST'><input type='text' name='username' class='form-control mb-2' placeholder='User'><input type='password' name='password' class='form-control mb-3' placeholder='Pass'><button class='btn btn-primary w-100'>Login</button></form></div></div>"

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(UI_HEADER + """
    <div class="container"><div class="row g-4">
        <div class="col-md-7"><div class="glass-card">
            <h4 class="mb-4 text-primary">Student Registration</h4>
            <form action="/add" method="POST" enctype="multipart/form-data">
                <div class="row g-2 mb-3">
                    <div class="col-md-4"><input type="text" name="sid" placeholder="Roll No" class="form-control" required></div>
                    <div class="col-md-5"><input type="text" name="name" placeholder="Full Name" class="form-control" required></div>
                    <div class="col-md-3"><input type="text" name="sclass" placeholder="Class" class="form-control" required></div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col"><input type="number" name="maths" placeholder="Math" class="form-control" required></div>
                    <div class="col"><input type="number" name="science" placeholder="Sci" class="form-control" required></div>
                    <div class="col"><input type="number" name="english" placeholder="Eng" class="form-control" required></div>
                </div>
                <div class="row g-2 mb-3">
                    <div class="col-md-8"><input type="email" name="email" placeholder="Email" class="form-control"></div>
                    <div class="col-md-4"><input type="number" name="attendance" placeholder="Attend %" class="form-control"></div>
                </div>
                <input type="file" name="photo" class="form-control mb-4">
                <button class="btn btn-primary w-100 py-2 fw-bold">REGISTER STUDENT</button>
            </form>
        </div></div>
        <div class="col-md-5"><div class="glass-card" style="border-top: 5px solid #0d6efd;">
            <h4 class="mb-3">Bulk Import</h4>
            <p class="small text-muted">Upload CSV with headers: sid, name, sclass, maths, science, english, attendance</p>
            <form action="/bulk_import" method="POST" enctype="multipart/form-data">
                <input type="file" name="file" class="form-control mb-3" accept=".csv">
                <button class="btn btn-outline-primary w-100">Process CSV File</button>
            </form>
        </div></div>
    </div></div>
    """)

@app.route('/database')
def database():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect("sms_final.db")
    df = pd.read_sql_query("SELECT * FROM students", conn)
    
    # Polar Chart Data
    avg_m = df['maths'].mean() if not df.empty else 0
    avg_s = df['science'].mean() if not df.empty else 0
    avg_e = df['english'].mean() if not df.empty else 0
    conn.close()

    return render_template_string(UI_HEADER + """
    <div class="container">
        <div class="row mb-4">
            <div class="col-md-4"><div class="glass-card text-center">
                <h6>Class Performance Analysis 📊</h6>
                <canvas id="polarChart"></canvas>
            </div></div>
            <div class="col-md-8"><div class="glass-card">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5>Student Records</h5>
                    <input type="text" id="searchInput" class="form-control w-50" placeholder="Search name or ID..." onkeyup="filterTable()">
                </div>
                <table class="table align-middle" id="studentTable">
                    <thead><tr><th>ID</th><th>Name</th><th>Class</th><th>Attend%</th><th>Actions</th></tr></thead>
                    <tbody>
                        {% for _, s in df.iterrows() %}
                        <tr>
                            <td>{{s['sid']}}</td><td>{{s['name']}}</td><td>{{s['sclass']}}</td>
                            <td><span class="badge {{ 'bg-danger' if s['attendance'] < 75 else 'bg-success' }}">{{s['attendance']}}%</span></td>
                            <td>
                                <a href="/report/{{s['sid']}}" class="btn btn-sm btn-dark"><i class="fas fa-eye"></i></a>
                                <a href="/delete/{{s['sid']}}" class="btn btn-sm btn-danger" onclick="return confirm('Delete this record?')"><i class="fas fa-trash"></i></a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div></div>
        </div>
    </div>
    <script>
        function filterTable() {
            let input = document.getElementById('searchInput').value.toUpperCase();
            let tr = document.getElementById('studentTable').getElementsByTagName('tr');
            for (let i = 1; i < tr.length; i++) {
                let txt = tr[i].innerText.toUpperCase();
                tr[i].style.display = txt.indexOf(input) > -1 ? "" : "none";
            }
        }
        new Chart(document.getElementById('polarChart'), {
            type: 'polarArea',
            data: { labels: ['Math', 'Sci', 'Eng'], datasets: [{ data: [{{avg_m}}, {{avg_s}}, {{avg_e}}], backgroundColor: ['#ff6384', '#36a2eb', '#ffce56'] }] }
        });
    </script>
    """, df=df, avg_m=avg_m, avg_s=avg_s, avg_e=avg_e)

@app.route('/report/<sid>')
def report(sid):
    conn = sqlite3.connect("sms_final.db")
    cursor = conn.cursor(); cursor.execute("SELECT * FROM students WHERE sid=?", (sid,))
    s = cursor.fetchone(); conn.close()
    f_g, f_c = get_grade(s[7])

    return render_template_string(UI_HEADER + """
    <div class="container no-print text-center mb-3">
        <button onclick="downloadPDF()" class="btn btn-primary"><i class="fas fa-file-pdf"></i> Download PDF</button>
        <button onclick="window.print()" class="btn btn-dark ms-2"><i class="fas fa-print"></i> Print</button>
    </div>
    <div id="pdf-area" class="container"><div class="glass-card mx-auto shadow-lg" style="max-width: 800px; border-top: 10px solid #1e293b;">
        <div class="row mb-4 align-items-center">
            <div class="col-8">
                <h1 class="fw-bold text-uppercase">Academic Report</h1>
                <h2 class="text-primary">{{s[1]}}</h2>
                <p class="h5">Roll: {{s[0]}} | Class: {{s[2]}}</p>
                <button class="btn btn-sm btn-outline-primary no-print" onclick="alert('Email logic triggered for parent!')">📧 Email Report</button>
            </div>
            <div class="col-4 text-end"><img src="/static/uploads/{{s[9]}}" width="130" class="img-thumbnail rounded-3"></div>
        </div>
        <div class="row">
            <div class="col-md-6"><canvas id="radarChart"></canvas></div>
            <div class="col-md-6 text-center">
                <table class="table table-bordered h5 mt-4">
                    <tr class="table-light"><th>Subject</th><th>Score</th></tr>
                    <tr><td>Math</td><td>{{s[3]}}</td></tr>
                    <tr><td>Sci</td><td>{{s[4]}}</td></tr>
                    <tr><td>Eng</td><td>{{s[5]}}</td></tr>
                    <tr class="table-dark"><th>Total</th><td>{{s[6]}} / 300</td></tr>
                </table>
                <div class="p-3 border rounded mt-3">
                    <h1 class="{{f_c}} fw-bold mb-0">{{f_g}}</h1>
                    <p class="mb-0">Final Grade | {{s[7]}}%</p>
                    <p class="text-muted">CGPA: {{s[8]}}</p>
                </div>
            </div>
        </div>
    </div></div>
    <script>
        new Chart(document.getElementById('radarChart'), {
            type: 'radar',
            data: { labels: ['Math', 'Sci', 'Eng'], datasets: [{ label: 'Performance', data: [{{s[3]}}, {{s[4]}}, {{s[5]}}], backgroundColor: 'rgba(54, 162, 235, 0.2)', borderColor: 'rgb(54, 162, 235)' }] }
        });
        function downloadPDF() {
            const element = document.getElementById('pdf-area');
            html2pdf().from(element).save('{{s[1]}}_Report.pdf');
        }
    </script>
    """, s=s, f_g=f_g, f_c=f_c)

@app.route('/add', methods=['POST'])
def add():
    m, s, e = int(request.form['maths']), int(request.form['science']), int(request.form['english'])
    total, perc = m + s + e, round(((m+s+e)/300)*100, 2)
    photo = request.files.get('photo'); photo_path = photo.filename if photo else "default.png"
    if photo: photo.save(os.path.join(UPLOAD_FOLDER, photo_path))
    conn = sqlite3.connect("sms_final.db")
    conn.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                 (request.form['sid'], request.form['name'], request.form['sclass'], m, s, e, total, perc, round(perc/9.5, 2), photo_path, "", request.form.get('attendance', 100), ""))
    conn.commit(); conn.close()
    return redirect(url_for('database'))

@app.route('/bulk_import', methods=['POST'])
def bulk_import():
    file = request.files['file']
    if file:
        df = pd.read_csv(file)
        conn = sqlite3.connect("sms_final.db")
        for _, r in df.iterrows():
            total, perc = (r['maths']+r['science']+r['english']), round(((r['maths']+r['science']+r['english'])/300)*100, 2)
            conn.execute("INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                         (str(r['sid']), r['name'], r['sclass'], int(r['maths']), int(r['science']), int(r['english']), total, perc, round(perc/9.5, 2), "default.png", "", int(r['attendance']), ""))
        conn.commit(); conn.close()
    return redirect(url_for('database'))

@app.route('/delete/<sid>')
def delete_student(sid):
    conn = sqlite3.connect("sms_final.db"); conn.execute("DELETE FROM students WHERE sid=?", (sid,)); conn.commit(); conn.close()
    return redirect(url_for('database'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    init_db(); app.run(debug=True)