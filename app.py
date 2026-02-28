from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ---------- App Config ----------
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session & flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------- Models ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    link = db.Column(db.String(255))
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.isoformat(),
            'location': self.location,
            'description': self.description,
            'link': self.link,
            'category': self.category
        }

# ---------- Initialize DB ----------
with app.app_context():
    db.create_all()

# ---------- Routes ----------

# Home
@app.route('/')
def index():
    return redirect(url_for('login'))

# ---------- Authentication ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        print(role)

        user = User.query.filter_by(username=username, role=role).first()
        if user and user.check_password(password):
            session['username'] = username
            session['role'] = role
            flash(f"{role.title()} {username} logged in successfully!", "success")
            return redirect(url_for('admin_home') if role=='admin' else url_for('student_home'))
        else:
            flash("Invalid credentials!", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "error")
            return redirect(url_for('register'))

        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

# ---------- Student / Admin Home ----------
@app.route('/student')
def student_home():
    if 'role' in session and session['role'] == 'student':
        return render_template('studenthome.html')
    flash("Unauthorized!", "error")
    return redirect(url_for('login'))

@app.route('/admin')
def admin_home():
    if 'role' in session and session['role'] == 'admin':
        return render_template('adminhome.html')
    flash("Unauthorized!", "error")
    return redirect(url_for('login'))

# ---------- Event CRUD ----------
@app.route('/admin/upload-event', methods=['POST'])
def upload_event():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    date_str = request.form.get('event_date')
    try:
        event_date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({'message': 'Invalid date format'}), 400

    ev = Event(
        name=request.form.get('event_name'),
        date=event_date,
        location=request.form.get('event_location'),
        description=request.form.get('event_description'),
        link=request.form.get('event_link'),
        category=request.form.get('event_category')
    )
    db.session.add(ev)
    db.session.commit()
    return jsonify({'message': 'Event uploaded successfully'}), 201


@app.route('/admin/get-events')
def get_events():
    search_query = request.args.get('search', '').lower()
    q = Event.query
    if search_query:
        q = q.filter(
            db.or_(
                Event.name.ilike(f'%{search_query}%'),
                Event.location.ilike(f'%{search_query}%')
            )
        )
    events = q.order_by(Event.date.asc(), Event.id.asc()).all()
    return jsonify({'events': [e.serialize() for e in events]})


@app.route('/admin/delete-event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    ev = Event.query.get_or_404(event_id)
    db.session.delete(ev)
    db.session.commit()
    return jsonify({'message': 'Event deleted successfully'})

# ---------- Run App ----------
if __name__ == '__main__':
    app.run(debug=True)

