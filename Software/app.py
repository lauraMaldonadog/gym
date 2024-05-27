from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATA_FILE = 'Software/users.json'
def load_routines():
    with open('Software/routines.json', 'r') as file:
        return json.load(file)


def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return []


def save_users(users):
    with open(DATA_FILE, 'w') as file:
        json.dump(users, file, indent=4)

        
@app.route('/')
def home():
    user_name = None
    if 'user' in session:
        user_name = session.get('user_name')
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
    return render_template('index.html', user_name=user_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        user = next((u for u in users if u['email'] == email and u['password'] == password), None)
        if user:
            session['user'] = user['email']
            session['user_name'] = user['name']
            session['is_admin'] = user.get('is_admin', False)
            if session['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            return 'Invalid credentials', 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        valid_until = (datetime.now() + timedelta(days=30)).date().isoformat()
        users = load_users()
        if any(u['email'] == email for u in users):
            return 'Email already registered', 400
        users.append({
            'name': name,
            'email': email,
            'password': password,
            'attendance': [],
            'valid_until': valid_until,
            'is_admin': False,
            'routine': ""
        })
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    users = load_users()
    for user in users:
        if not user.get('routine'):
            user['routine'] = "No asignada"
    return render_template('dashboard.html', users=users)

@app.route('/assign_routine/<email>', methods=['GET', 'POST'])
def assign_routine(email):
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    users = load_users()
    user = next((u for u in users if u['email'] == email), None)
    
    if request.method == 'POST':
        routine = request.form['routine']
        if user:
            user['routine'] = routine
            save_users(users)
        return redirect(url_for('admin_dashboard'))
    
    routines = load_routines()  # Cargar las rutinas
    return render_template('assign_routine.html', user=user, routines=routines)

@app.route('/view_exercises/<email>')
def view_exercises(email):
    if 'user' not in session or (session['user'] != email and not session.get('is_admin')):
        return redirect(url_for('login'))
    users = load_users()
    user = next((u for u in users if u['email'] == email), None)
    if not user:
        return 'Usuario no encontrado', 404

    routines = load_routines()
    user_routine = next((r for r in routines if r['name'] == user['routine']), None)

    return render_template('view_exercises.html', user=user, user_routine=user_routine)

@app.route('/view_routine/<email>')
def view_routine(email):
    if 'user' not in session or (session['user'] != email and not session.get('is_admin')):
        return redirect(url_for('login'))
    users = load_users()
    user = next((u for u in users if u['email'] == email), None)
    if not user:
        return 'Usuario no encontrado', 404

    routines = load_routines()
    user_routine = next((r for r in routines if r['name'] == user['routine']), None)

    return render_template('view_routine.html', user=user, user_routine=user_routine)

@app.route('/delete_user/<email>', methods=['GET', 'POST'])
def delete_user(email):
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    users = load_users()
    users = [u for u in users if u['email'] != email]
    save_users(users)
    
    return redirect(url_for('admin_dashboard'))

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        plan = request.form['plan']
        valid_until = (datetime.now() + timedelta(days=30)).date().isoformat()
        
        users = load_users()
        if any(u['email'] == email for u in users):
            return 'Email already registered', 400
        
        users.append({
            'name': name,
            'email': email,
            'password': password,
            'plan': plan,
            'attendance': [],
            'valid_until': valid_until,
            'is_admin': False,
            'routine': "No asignada"
        })
        save_users(users)
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_user.html')

@app.route('/view_plans')
def view_plans():
    # Aquí puedes cargar los planes desde donde los tengas almacenados
    planes = [
        {'nombre': 'Plan Básico', 'descripcion': 'Acceso al gimnasio durante horas laborables.', 'precio': '$30/mes'},
        {'nombre': 'Plan Avanzado', 'descripcion': 'Acceso ilimitado al gimnasio.', 'precio': '$50/mes'},
        {'nombre': 'Plan Premium', 'descripcion': 'Acceso ilimitado al gimnasio + entrenamiento personalizado.', 'precio': '$80/mes'}
    ]
    return render_template('planes.html', planes=planes)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)