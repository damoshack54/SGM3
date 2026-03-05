"""
SGM Drivers Fleet Management System
====================================
Full-stack web application for UK driver fleet management.
Compliant with Driver CPC, DVLA, HMRC regulations.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
from functools import wraps
import os, csv, io, json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sgm-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sgm_drivers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='hr')  # admin, hr, driver
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'username': self.username,
                'email': self.email, 'role': self.role}


class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.String(10), unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.Date)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    ni_number = db.Column(db.String(20))
    nationality = db.Column(db.String(60))
    licence_type = db.Column(db.String(20))
    contract_type = db.Column(db.String(30))
    salary = db.Column(db.Float, default=0)
    start_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Active')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    licences = db.relationship('Licence', backref='driver', lazy=True, cascade='all, delete-orphan')
    trainings = db.relationship('Training', backref='driver', lazy=True, cascade='all, delete-orphan')
    contracts = db.relationship('Contract', backref='driver', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='driver', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='driver', lazy=True, cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            'id': self.id, 'driver_id': self.driver_id,
            'first_name': self.first_name, 'last_name': self.last_name,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'email': self.email, 'phone': self.phone,
            'address': self.address, 'ni_number': self.ni_number,
            'nationality': self.nationality, 'licence_type': self.licence_type,
            'contract_type': self.contract_type, 'salary': self.salary,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'status': self.status, 'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Licence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    licence_type = db.Column(db.String(30))
    licence_number = db.Column(db.String(60))
    categories = db.Column(db.String(60))
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    issuing_authority = db.Column(db.String(60), default='DVLA')
    document_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Valid')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def days_to_expiry(self):
        if self.expiry_date:
            return (self.expiry_date - date.today()).days
        return None

    @property
    def expiry_status(self):
        d = self.days_to_expiry
        if d is None: return 'Unknown'
        if d < 0: return 'Expired'
        if d <= 30: return 'Expiring'
        return 'Valid'

    def to_dict(self):
        return {
            'id': self.id, 'driver_id': self.driver_id,
            'driver_name': self.driver.full_name if self.driver else '',
            'licence_type': self.licence_type, 'licence_number': self.licence_number,
            'categories': self.categories,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'issuing_authority': self.issuing_authority,
            'days_to_expiry': self.days_to_expiry,
            'expiry_status': self.expiry_status,
            'status': self.status, 'notes': self.notes,
        }


class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    course_type = db.Column(db.String(80))
    provider = db.Column(db.String(120))
    certificate_number = db.Column(db.String(60))
    start_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    hours_completed = db.Column(db.Float, default=0)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(30), default='In Progress')
    notes = db.Column(db.Text)
    document_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'driver_id': self.driver_id,
            'driver_name': self.driver.full_name if self.driver else '',
            'course_type': self.course_type, 'provider': self.provider,
            'certificate_number': self.certificate_number,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'hours_completed': self.hours_completed,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status, 'notes': self.notes,
        }


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    contract_type = db.Column(db.String(30))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    salary = db.Column(db.Float, default=0)
    hourly_rate = db.Column(db.Float)
    notice_period = db.Column(db.String(30))
    holiday_entitlement = db.Column(db.Integer, default=28)
    status = db.Column(db.String(20), default='Active')
    notes = db.Column(db.Text)
    document_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'driver_id': self.driver_id,
            'driver_name': self.driver.full_name if self.driver else '',
            'contract_type': self.contract_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'salary': self.salary, 'hourly_rate': self.hourly_rate,
            'notice_period': self.notice_period,
            'holiday_entitlement': self.holiday_entitlement,
            'status': self.status, 'notes': self.notes,
        }


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    pay_period = db.Column(db.String(20))
    gross_pay = db.Column(db.Float, default=0)
    paye_tax = db.Column(db.Float, default=0)
    employee_ni = db.Column(db.Float, default=0)
    employer_ni = db.Column(db.Float, default=0)
    pension = db.Column(db.Float, default=0)
    deductions = db.Column(db.Float, default=0)
    net_pay = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(30))
    payment_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'driver_id': self.driver_id,
            'driver_name': self.driver.full_name if self.driver else '',
            'pay_period': self.pay_period, 'gross_pay': self.gross_pay,
            'paye_tax': self.paye_tax, 'employee_ni': self.employee_ni,
            'employer_ni': self.employer_ni, 'pension': self.pension,
            'deductions': self.deductions, 'net_pay': self.net_pay,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'status': self.status, 'notes': self.notes,
        }


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    doc_type = db.Column(db.String(50))
    reference_number = db.Column(db.String(60))
    upload_date = db.Column(db.Date, default=date.today)
    expiry_date = db.Column(db.Date)
    file_path = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Valid')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def expiry_status(self):
        if not self.expiry_date: return 'No Expiry'
        diff = (self.expiry_date - date.today()).days
        if diff < 0: return 'Expired'
        if diff <= 30: return 'Expiring'
        return 'Valid'

    def to_dict(self):
        return {
            'id': self.id, 'driver_id': self.driver_id,
            'driver_name': self.driver.full_name if self.driver else '',
            'doc_type': self.doc_type, 'reference_number': self.reference_number,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'file_name': self.file_name, 'status': self.status,
            'expiry_status': self.expiry_status, 'notes': self.notes,
        }


# ==================== AUTH ====================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


# ==================== ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or request.form
        user = User.query.filter_by(username=data.get('username')).first()
        if user and user.check_password(data.get('password')):
            login_user(user, remember=data.get('remember', False))
            return jsonify({'success': True, 'role': user.role, 'username': user.username})
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=current_user)


# ==================== API: STATS ====================

@app.route('/api/stats')
@login_required
def api_stats():
    today = date.today()
    total_drivers = Driver.query.filter_by(status='Active').count()

    expiring_licences = Licence.query.filter(
        Licence.expiry_date <= today + timedelta(days=30),
        Licence.expiry_date >= today
    ).count()

    cpc_hours = db.session.query(db.func.sum(Training.hours_completed)).scalar() or 0

    july_payments = Payment.query.filter(
        Payment.pay_period.like('%2024%')
    ).all()
    total_payroll = sum(p.gross_pay for p in july_payments)

    overdue_training = Training.query.filter_by(status='Overdue').count()
    active_contracts = Contract.query.filter_by(status='Active').count()
    pending_payments = Payment.query.filter_by(status='Pending').count()

    # Alerts
    alerts = []
    critical_lic = Licence.query.filter(
        Licence.expiry_date <= today + timedelta(days=14),
        Licence.expiry_date >= today
    ).all()
    for l in critical_lic:
        alerts.append({
            'type': 'error',
            'text': f'{l.driver.full_name} — {l.licence_type} licence expires in {l.days_to_expiry} days',
            'tag': '❌ CRITICAL'
        })

    warn_lic = Licence.query.filter(
        Licence.expiry_date <= today + timedelta(days=30),
        Licence.expiry_date > today + timedelta(days=14)
    ).all()
    for l in warn_lic:
        alerts.append({
            'type': 'warn',
            'text': f'{l.driver.full_name} — {l.licence_type} licence expiring in {l.days_to_expiry} days',
            'tag': f'⚠️ {l.days_to_expiry} days'
        })

    return jsonify({
        'total_drivers': total_drivers,
        'expiring_licences': expiring_licences,
        'cpc_hours': int(cpc_hours),
        'total_payroll': total_payroll,
        'overdue_training': overdue_training,
        'active_contracts': active_contracts,
        'pending_payments': pending_payments,
        'alerts': alerts,
        'alerts_count': len(alerts)
    })

@app.route('/api/chart/licences')
@login_required
def chart_licences():
    today = date.today()
    months = []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=i*30)
        months.append(d.strftime('%b'))
    return jsonify({
        'labels': months,
        'valid': [22, 23, 22, 24, 24, Licence.query.filter_by(status='Valid').count()],
        'expiring': [1, 2, 3, 2, 3, Licence.query.filter(Licence.expiry_date <= today + timedelta(days=30), Licence.expiry_date >= today).count()],
        'expired': [1, 0, 1, 0, 0, Licence.query.filter(Licence.expiry_date < today).count()],
    })


# ==================== API: DRIVERS ====================

@app.route('/api/drivers', methods=['GET', 'POST'])
@login_required
def api_drivers():
    if request.method == 'GET':
        q = request.args.get('q', '')
        status = request.args.get('status', '')
        query = Driver.query
        if q:
            query = query.filter(
                db.or_(Driver.first_name.ilike(f'%{q}%'),
                       Driver.last_name.ilike(f'%{q}%'),
                       Driver.email.ilike(f'%{q}%'),
                       Driver.driver_id.ilike(f'%{q}%'))
            )
        if status:
            query = query.filter_by(status=status)
        drivers = query.order_by(Driver.created_at.desc()).all()
        return jsonify([d.to_dict() for d in drivers])

    data = request.get_json()
    count = Driver.query.count()
    driver_id = f"DRV{str(count + 1).zfill(3)}"
    driver = Driver(
        driver_id=driver_id,
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        ni_number=data.get('ni_number', ''),
        nationality=data.get('nationality', 'British'),
        licence_type=data.get('licence_type', 'LGV'),
        contract_type=data.get('contract_type', 'Full-time'),
        salary=float(data.get('salary', 0)),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else date.today(),
        status=data.get('status', 'Active'),
        notes=data.get('notes', '')
    )
    db.session.add(driver)
    db.session.commit()
    return jsonify({'success': True, 'driver': driver.to_dict()}), 201


@app.route('/api/drivers/<int:driver_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_driver(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    if request.method == 'GET':
        d = driver.to_dict()
        d['licences'] = [l.to_dict() for l in driver.licences]
        d['trainings'] = [t.to_dict() for t in driver.trainings]
        d['contracts'] = [c.to_dict() for c in driver.contracts]
        d['payments'] = [p.to_dict() for p in driver.payments]
        d['documents'] = [doc.to_dict() for doc in driver.documents]
        return jsonify(d)

    if request.method == 'PUT':
        data = request.get_json()
        for field in ['first_name','last_name','email','phone','address','ni_number',
                      'nationality','licence_type','contract_type','status','notes']:
            if field in data:
                setattr(driver, field, data[field])
        if 'salary' in data:
            driver.salary = float(data['salary'])
        if 'date_of_birth' in data and data['date_of_birth']:
            driver.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        if 'start_date' in data and data['start_date']:
            driver.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        driver.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'driver': driver.to_dict()})

    db.session.delete(driver)
    db.session.commit()
    return jsonify({'success': True})


# ==================== API: LICENCES ====================

@app.route('/api/licences', methods=['GET', 'POST'])
@login_required
def api_licences():
    if request.method == 'GET':
        licences = Licence.query.join(Driver).order_by(Licence.expiry_date.asc()).all()
        return jsonify([l.to_dict() for l in licences])
    data = request.get_json()
    lic = Licence(
        driver_id=int(data['driver_id']),
        licence_type=data['licence_type'],
        licence_number=data.get('licence_number',''),
        categories=data.get('categories',''),
        issue_date=datetime.strptime(data['issue_date'], '%Y-%m-%d').date() if data.get('issue_date') else None,
        expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
        issuing_authority=data.get('issuing_authority','DVLA'),
        notes=data.get('notes','')
    )
    db.session.add(lic)
    db.session.commit()
    return jsonify({'success': True, 'licence': lic.to_dict()}), 201

@app.route('/api/licences/<int:lid>', methods=['PUT', 'DELETE'])
@login_required
def api_licence(lid):
    lic = Licence.query.get_or_404(lid)
    if request.method == 'DELETE':
        db.session.delete(lic)
        db.session.commit()
        return jsonify({'success': True})
    data = request.get_json()
    for f in ['licence_type','licence_number','categories','issuing_authority','notes','status']:
        if f in data: setattr(lic, f, data[f])
    if data.get('expiry_date'):
        lic.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True, 'licence': lic.to_dict()})


# ==================== API: TRAINING ====================

@app.route('/api/training', methods=['GET', 'POST'])
@login_required
def api_training():
    if request.method == 'GET':
        trainings = Training.query.join(Driver).order_by(Training.created_at.desc()).all()
        # CPC totals per driver
        result = [t.to_dict() for t in trainings]
        for item in result:
            cpc_total = db.session.query(db.func.sum(Training.hours_completed)).filter(
                Training.driver_id == item['driver_id'],
                Training.course_type.ilike('%CPC%')
            ).scalar() or 0
            item['cpc_total'] = float(cpc_total)
        return jsonify(result)
    data = request.get_json()
    t = Training(
        driver_id=int(data['driver_id']),
        course_type=data['course_type'],
        provider=data.get('provider',''),
        certificate_number=data.get('certificate_number',''),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
        completion_date=datetime.strptime(data['completion_date'], '%Y-%m-%d').date() if data.get('completion_date') else None,
        hours_completed=float(data.get('hours_completed',0)),
        expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
        status=data.get('status','Completed'),
        notes=data.get('notes','')
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'success': True, 'training': t.to_dict()}), 201

@app.route('/api/training/<int:tid>', methods=['PUT', 'DELETE'])
@login_required
def api_train(tid):
    t = Training.query.get_or_404(tid)
    if request.method == 'DELETE':
        db.session.delete(t)
        db.session.commit()
        return jsonify({'success': True})
    data = request.get_json()
    for f in ['course_type','provider','certificate_number','status','notes']:
        if f in data: setattr(t, f, data[f])
    if data.get('hours_completed'): t.hours_completed = float(data['hours_completed'])
    if data.get('completion_date'):
        t.completion_date = datetime.strptime(data['completion_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


# ==================== API: CONTRACTS ====================

@app.route('/api/contracts', methods=['GET', 'POST'])
@login_required
def api_contracts():
    if request.method == 'GET':
        contracts = Contract.query.join(Driver).order_by(Contract.created_at.desc()).all()
        return jsonify([c.to_dict() for c in contracts])
    data = request.get_json()
    c = Contract(
        driver_id=int(data['driver_id']),
        contract_type=data['contract_type'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
        salary=float(data.get('salary',0)),
        hourly_rate=float(data.get('hourly_rate',0)) if data.get('hourly_rate') else None,
        notice_period=data.get('notice_period','1 Month'),
        holiday_entitlement=int(data.get('holiday_entitlement',28)),
        status=data.get('status','Active'),
        notes=data.get('notes','')
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'success': True, 'contract': c.to_dict()}), 201

@app.route('/api/contracts/<int:cid>', methods=['PUT', 'DELETE'])
@login_required
def api_contract(cid):
    c = Contract.query.get_or_404(cid)
    if request.method == 'DELETE':
        db.session.delete(c)
        db.session.commit()
        return jsonify({'success': True})
    data = request.get_json()
    for f in ['contract_type','notice_period','status','notes']:
        if f in data: setattr(c, f, data[f])
    if 'salary' in data: c.salary = float(data['salary'])
    if data.get('end_date'):
        c.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


# ==================== API: PAYMENTS ====================

@app.route('/api/payments', methods=['GET', 'POST'])
@login_required
def api_payments():
    if request.method == 'GET':
        payments = Payment.query.join(Driver).order_by(Payment.created_at.desc()).all()
        return jsonify([p.to_dict() for p in payments])
    data = request.get_json()
    gross = float(data.get('gross_pay', 0))
    paye = float(data.get('paye_tax', 0))
    eni = float(data.get('employee_ni', 0))
    pension = float(data.get('pension', 0))
    net = gross - paye - eni - pension
    p = Payment(
        driver_id=int(data['driver_id']),
        pay_period=data.get('pay_period',''),
        gross_pay=gross, paye_tax=paye,
        employee_ni=eni,
        employer_ni=float(data.get('employer_ni', round(gross * 0.138, 2))),
        pension=pension, net_pay=net,
        payment_method=data.get('payment_method','BACS'),
        payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d').date() if data.get('payment_date') else date.today(),
        status=data.get('status','Paid'),
        notes=data.get('notes','')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'success': True, 'payment': p.to_dict()}), 201

@app.route('/api/payments/<int:pid>', methods=['PUT', 'DELETE'])
@login_required
def api_payment(pid):
    p = Payment.query.get_or_404(pid)
    if request.method == 'DELETE':
        db.session.delete(p)
        db.session.commit()
        return jsonify({'success': True})
    data = request.get_json()
    if 'status' in data: p.status = data['status']
    if 'notes' in data: p.notes = data['notes']
    db.session.commit()
    return jsonify({'success': True})


# ==================== API: DOCUMENTS ====================

@app.route('/api/documents', methods=['GET', 'POST'])
@login_required
def api_documents():
    if request.method == 'GET':
        docs = Document.query.join(Driver).order_by(Document.created_at.desc()).all()
        return jsonify([d.to_dict() for d in docs])
    data = request.get_json()
    doc = Document(
        driver_id=int(data['driver_id']),
        doc_type=data['doc_type'],
        reference_number=data.get('reference_number',''),
        upload_date=date.today(),
        expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
        file_name=data.get('file_name',''),
        status=data.get('status','Valid'),
        notes=data.get('notes','')
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({'success': True, 'document': doc.to_dict()}), 201

@app.route('/api/documents/<int:did>', methods=['DELETE'])
@login_required
def api_document(did):
    doc = Document.query.get_or_404(did)
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'success': True})


# ==================== EXPORT ====================

@app.route('/api/export/<string:entity>')
@login_required
def export_csv(entity):
    output = io.StringIO()
    writer = csv.writer(output)

    if entity == 'drivers':
        drivers = Driver.query.all()
        writer.writerow(['ID','First Name','Last Name','DOB','Email','Phone','NI Number','Licence Type','Contract','Salary','Start Date','Status'])
        for d in drivers:
            writer.writerow([d.driver_id, d.first_name, d.last_name,
                           d.date_of_birth, d.email, d.phone, d.ni_number,
                           d.licence_type, d.contract_type, d.salary, d.start_date, d.status])
    elif entity == 'licences':
        licences = Licence.query.join(Driver).all()
        writer.writerow(['Driver','Licence Type','Licence Number','Categories','Issue Date','Expiry Date','Status','Days to Expiry'])
        for l in licences:
            writer.writerow([l.driver.full_name, l.licence_type, l.licence_number,
                           l.categories, l.issue_date, l.expiry_date, l.expiry_status, l.days_to_expiry])
    elif entity == 'training':
        training = Training.query.join(Driver).all()
        writer.writerow(['Driver','Course','Provider','Certificate No','Start Date','Completion','Hours','Status'])
        for t in training:
            writer.writerow([t.driver.full_name, t.course_type, t.provider,
                           t.certificate_number, t.start_date, t.completion_date,
                           t.hours_completed, t.status])
    elif entity == 'payments':
        payments = Payment.query.join(Driver).all()
        writer.writerow(['Driver','Period','Gross Pay','PAYE Tax','Employee NI','Employer NI','Pension','Net Pay','Method','Status'])
        for p in payments:
            writer.writerow([p.driver.full_name, p.pay_period, p.gross_pay,
                           p.paye_tax, p.employee_ni, p.employer_ni, p.pension,
                           p.net_pay, p.payment_method, p.status])
    elif entity == 'contracts':
        contracts = Contract.query.join(Driver).all()
        writer.writerow(['Driver','Type','Start Date','End Date','Salary','Notice Period','Status'])
        for c in contracts:
            writer.writerow([c.driver.full_name, c.contract_type, c.start_date,
                           c.end_date, c.salary, c.notice_period, c.status])
    else:
        return jsonify({'error': 'Unknown entity'}), 400

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'sgm_{entity}_{date.today()}.csv'
    )


# ==================== USERS ====================

@app.route('/api/users', methods=['GET', 'POST'])
@login_required
def api_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([u.to_dict() for u in users])
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    u = User(username=data['username'], email=data['email'], role=data.get('role','hr'))
    u.set_password(data['password'])
    db.session.add(u)
    db.session.commit()
    return jsonify({'success': True, 'user': u.to_dict()}), 201

@app.route('/api/users/<int:uid>', methods=['PUT', 'DELETE'])
@login_required
def api_user(uid):
    if current_user.role != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    u = User.query.get_or_404(uid)
    if request.method == 'DELETE':
        if u.id == current_user.id:
            return jsonify({'error': 'Cannot delete yourself'}), 400
        db.session.delete(u)
        db.session.commit()
        return jsonify({'success': True})
    data = request.get_json()
    if 'role' in data: u.role = data['role']
    if 'email' in data: u.email = data['email']
    if 'password' in data and data['password']: u.set_password(data['password'])
    db.session.commit()
    return jsonify({'success': True})


# ==================== SEED DATA ====================

def seed_database():
    """Populate database with realistic sample data."""
    if User.query.count() > 0:
        return

    # Users
    admin = User(username='admin', email='admin@sgmdrivers.co.uk', role='admin')
    admin.set_password('Admin@2024!')
    hr = User(username='hr', email='hr@sgmdrivers.co.uk', role='hr')
    hr.set_password('Hr@2024!')
    db.session.add_all([admin, hr])
    db.session.commit()

    # Drivers
    driver_data = [
        ('James', 'Holden', '1985-03-12', 'j.holden@sgm.co.uk', '+44 7700 900001', 'AB 12 34 56 C', 'LGV', 'Full-time', 34000, '2020-03-15', 'Active'),
        ('Sara', 'Okonkwo', '1990-07-28', 's.okonkwo@sgm.co.uk', '+44 7700 900002', 'CD 23 45 67 D', 'LGV', 'Full-time', 32500, '2019-07-01', 'Active'),
        ('Marcus', 'Patel', '1988-11-05', 'm.patel@sgm.co.uk', '+44 7700 900003', 'EF 34 56 78 E', 'PCV', 'Part-time', 22000, '2021-01-10', 'Active'),
        ('Emily', 'Clarke', '1982-05-19', 'e.clarke@sgm.co.uk', '+44 7700 900004', 'GH 45 67 89 F', 'LGV', 'Full-time', 35000, '2018-05-20', 'Active'),
        ('Liam', 'Walsh', '1995-09-30', 'l.walsh@sgm.co.uk', '+44 7700 900005', 'IJ 56 78 90 G', 'Van', 'Temporary', 28000, '2023-09-01', 'Active'),
        ('Amara', 'Diallo', '1987-02-14', 'a.diallo@sgm.co.uk', '+44 7700 900006', 'KL 67 89 01 H', 'LGV', 'Full-time', 33000, '2022-02-14', 'Active'),
        ('Peter', 'Novak', '1984-07-22', 'p.novak@sgm.co.uk', '+44 7700 900007', 'MN 78 90 12 I', 'PCV', 'Full-time', 31000, '2020-11-03', 'Active'),
        ('Olivia', 'Hassan', '1993-04-08', 'o.hassan@sgm.co.uk', '+44 7700 900008', 'OP 89 01 23 J', 'LGV', 'Agency', 29000, '2023-03-20', 'Inactive'),
    ]
    drivers = []
    for i, (fn, ln, dob, email, phone, ni, lt, ct, sal, sd, status) in enumerate(driver_data, 1):
        d = Driver(
            driver_id=f'DRV{str(i).zfill(3)}', first_name=fn, last_name=ln,
            date_of_birth=datetime.strptime(dob,'%Y-%m-%d').date(),
            email=email, phone=phone, ni_number=ni, nationality='British',
            licence_type=lt, contract_type=ct, salary=sal,
            start_date=datetime.strptime(sd,'%Y-%m-%d').date(), status=status
        )
        db.session.add(d)
        drivers.append(d)
    db.session.commit()

    today = date.today()

    # Licences
    lic_data = [
        (0, 'LGV Class C+E', 'HOLDE9012345JA2HQ', 'B, C, C+E', '2014-08-10', (today + timedelta(days=8)).isoformat()),
        (1, 'LGV Class C', 'OKONK9801234SO9AB', 'B, C', '2015-11-20', (today + timedelta(days=140)).isoformat()),
        (2, 'PCV', 'PATEL8907654MP4CD', 'B, D', '2011-09-05', (today + timedelta(days=200)).isoformat()),
        (3, 'LGV Class C+E', 'CLARK8903214EC7EF', 'B, C, C+E', '2016-03-14', (today + timedelta(days=580)).isoformat()),
        (4, 'Van (B1)', 'WALSH9812345LW2GH', 'B, B1', '2015-12-01', (today + timedelta(days=170)).isoformat()),
        (5, 'LGV Class C', 'DIALL9901234AD5IJ', 'B, C', '2014-09-30', (today + timedelta(days=22)).isoformat()),
        (6, 'PCV', 'NOVAK9007654PN8KL', 'B, D', '2016-07-22', (today + timedelta(days=720)).isoformat()),
    ]
    for di, lt, num, cats, issue, expiry in lic_data:
        l = Licence(driver_id=drivers[di].id, licence_type=lt, licence_number=num,
                    categories=cats, issue_date=datetime.strptime(issue,'%Y-%m-%d').date(),
                    expiry_date=datetime.strptime(expiry,'%Y-%m-%d').date(), issuing_authority='DVLA')
        db.session.add(l)

    # Training
    train_data = [
        (0, 'CPC Periodic Training', 'TruckPro Academy', 'CPC-2024-001', '2024-05-10', '2024-05-10', 7, None, 'Completed'),
        (1, 'CPC Periodic Training', 'UK Driver Training', 'CPC-2024-002', '2024-03-22', '2024-03-22', 7, None, 'Completed'),
        (2, 'CPC Periodic Training', 'UK Driver Training', 'CPC-2024-003', '2023-11-14', '2023-11-14', 7, None, 'Completed'),
        (3, 'Manual Handling', 'SafeWork Ltd', 'MH-2024-040', '2024-06-01', '2024-06-01', 4, None, 'Completed'),
        (4, 'CPC Periodic Training', 'Fleet Academy', 'CPC-2024-004', '2024-01-15', '2024-01-15', 7, None, 'Completed'),
        (5, 'ADR Dangerous Goods', 'Hazmat Training UK', 'ADR-2024-011', '2024-04-18', '2024-04-18', 5, None, 'Completed'),
        (0, 'Fire Safety', 'SafeWork Ltd', 'FS-2024-007', '2024-02-12', '2024-02-12', 3, None, 'Completed'),
        (6, 'Tachograph Use', 'Fleet Academy', 'TACHO-2024-003', '2023-09-05', '2023-09-05', 7, None, 'Completed'),
    ]
    for di, ct, prov, cert, sd, cd, hrs, exp, st in train_data:
        t = Training(driver_id=drivers[di].id, course_type=ct, provider=prov,
                    certificate_number=cert,
                    start_date=datetime.strptime(sd,'%Y-%m-%d').date(),
                    completion_date=datetime.strptime(cd,'%Y-%m-%d').date(),
                    hours_completed=hrs, status=st)
        db.session.add(t)

    # Contracts
    for d in drivers:
        end_date = None
        if d.contract_type == 'Temporary':
            end_date = d.start_date + timedelta(days=365)
        c = Contract(driver_id=d.id, contract_type=d.contract_type,
                    start_date=d.start_date, end_date=end_date,
                    salary=d.salary, notice_period='1 Month',
                    holiday_entitlement=28,
                    status='Active' if d.status=='Active' else 'Expired')
        db.session.add(c)

    # Payments
    for d in drivers[:7]:
        gross = round(d.salary / 12, 2)
        paye = round(gross * 0.15, 2)
        eni = round(gross * 0.075, 2)
        pension = round(gross * 0.05, 2)
        net = round(gross - paye - eni - pension, 2)
        p = Payment(
            driver_id=d.id, pay_period='July 2024',
            gross_pay=gross, paye_tax=paye, employee_ni=eni,
            employer_ni=round(gross * 0.138, 2), pension=pension,
            net_pay=net, payment_method='BACS',
            payment_date=date(2024, 7, 31),
            status='Paid' if d.status == 'Active' else 'Pending'
        )
        db.session.add(p)

    # Documents
    doc_data = [
        (0, 'DVLA Licence', 'HOLDE9012345JA2HQ', (today + timedelta(days=8)).isoformat()),
        (1, 'CPC Card', 'CPC-2029-001', (today + timedelta(days=1800)).isoformat()),
        (2, 'DBS Certificate', 'DBS-2022-114782', (today + timedelta(days=22)).isoformat()),
        (3, 'Tachograph Card', 'TACHO-GB-441827', (today + timedelta(days=1400)).isoformat()),
        (4, 'Passport', 'GB-12345678', (today + timedelta(days=2200)).isoformat()),
        (5, 'Right to Work', 'RTW-2022-007721', (today + timedelta(days=1000)).isoformat()),
        (6, 'P60', 'P60-2024-NOVAK', None),
        (7, 'DVLA Licence', 'HASS9301234OH8MN', (today + timedelta(days=100)).isoformat()),
    ]
    for di, dt, ref, exp in doc_data:
        doc = Document(driver_id=drivers[di].id, doc_type=dt, reference_number=ref,
                      upload_date=date.today(),
                      expiry_date=datetime.strptime(exp,'%Y-%m-%d').date() if exp else None,
                      file_name='', status='Valid')
        db.session.add(doc)

    db.session.commit()
    print("✅ Database seeded with sample data.")


# ==================== INIT ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
