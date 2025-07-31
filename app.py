from flask import Flask, request, render_template, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] =False
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)       
    password = db.Column(db.String(100))
    is_librarian=db.Column(db.Boolean, nullable=False, default=False)
    book_id = db.relationship('Books', backref="user")    

class Section(db.Model):
     id = db.Column(db.Integer(), primary_key=True)
     name =db.Column(db.String(200), nullable = False)
     datecreate = db.Column(db.DateTime, default=datetime.utcnow)    
     description = db.Column(db.String(), nullable = False)
     section_id = db.Column(db.Integer(), db.ForeignKey('user.id'))    
     books = db.relationship('Books', backref="section", cascade = "all, delete")    
     user_id=db.Column(db.Integer(), db.ForeignKey('user.id'))

class Books(db.Model):
     id = db.Column(db.Integer(), primary_key=True)
     name =db.Column(db.String(200), unique = True, nullable = False)     
     content = db.Column(db.String, nullable=False)
     author =db.Column(db.String(200), nullable = False)
     dateissued = db.Column(db.DateTime, default=datetime.utcnow)
     section_name=db.Column(db.String(200), db.ForeignKey('section.name'))
     requests = db.relationship('Request', back_populates='book')     
     user_id=db.Column(db.Integer(), db.ForeignKey('user.id'))    

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    request_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_by_user = db.Column(db.Boolean, default=False) 
    return_date = db.Column(db.DateTime, nullable=True)
    number_of_days=db.Column(db.Integer(), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')     
    user = db.relationship('User', backref='requests')
    book = db.relationship('Books', back_populates='requests')      

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_feedback = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref='feedbacks')     

with app.app_context():
    db.create_all()
    librarian = User.query.filter_by(username = 'librarian').first()
    if not librarian:
        librarian = User(username ='librarian', password='librarian', is_librarian=True)
        db.session.add(librarian)
        db.session.commit()

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):        
        if 'user_id' not in session:
            flash('Please login to your account')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner

def librarian_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash(('Please login to your account.'))
            return redirect(url_for('login'))       
        user = User.query.get(session['user_id'])
        if not user.is_librarian:
            flash('You need to have librarian access')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():    
    username = request.form.get('username')
    password = request.form.get('password')
    if username =='' or password =='':
        flash('username or password needs to be filled')
        return redirect(url_for('login'))    
    user = User.query.filter_by(username = username).first()    
    if user:       
        if user.password==password:
            session['user_id']=user.id
            session['is_librarian']= user.is_librarian
            return redirect(url_for('user_dash'))   
        else:
            flash('Password is incorrect')
            return redirect(url_for('login'))   
    else:
        flash('User does not exist')
        return redirect(url_for('login'))   

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_post():
    username = request.form.get('username')
    password = request.form.get('password')
   # name = request.form.get('name')
    if username =='' or password =='':
        flash('username or password cannot be empty')
        return redirect(url_for('signup'))
    if User.query.filter_by(username = username).first():
        flash('User with this username already exist. Please search another name')
        return redirect(url_for('signup'))
    else:
        user = User(username=username, password = password)
        db.session.add(user)
        db.session.commit()
        flash('User account successfully created')
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You are logged out')
    return redirect(url_for('index'))

@app.route('/user_dash')
@auth_required
def user_dash():    
    if session['is_librarian']:
        return redirect(url_for('dashboard'))
    elif session['user_id']:
                all_sects=Section.query.all()
                all_books=Books.query.all()
                user_request= Request.query.filter_by(user_id=session['user_id']).all()
                return render_template('user_home.html', all_sects=all_sects, all_books=all_books, user_request= user_request, user_feedback=Feedback.query.all())
    else:
        flash('You need to log in first.')
        return redirect(url_for('login_page'))     

@app.route('/profile')
@auth_required
def profile():
    user_id=User.query.get(session["user_id"])
    if user_id:
        user_request= Request.query.filter_by(user_id=session['user_id']).all()
        request_book=Books.query.all()
        return render_template('profile.html', user_request= user_request, request_book=request_book)
    else:
        flash('You need to login in first')
        return redirect(url_for('login'))  

@app.route('/user_requeststatus')
@librarian_required
def user_requeststatus():       
    user_request= Request.query.all()
    feedback=Feedback.query.all()    
    return render_template('user_requeststatus.html', user_request=user_request, feedback=feedback)

@app.route("/add_sect", methods = ['GET', 'POST'])
@librarian_required
def add_sect():
    if request.method == "POST":
        name = request.form.get("name")       
        description = request.form.get("description")
        section_id = request.form.get("section_id")        
        new_sect = Section(name=name, description= description, section_id = section_id)
        db.session.add(new_sect)
        db.session.commit()
        flash('Section added successfully')
        return redirect(url_for('dashboard'))
    all_sects=Section.query.all()
    return render_template('add_sect.html')

@app.route("/<int:id>/update", methods = ['GET', 'POST'])
@librarian_required
def update_sect(id):
    this_sect = Section.query.get(id)
    if request.method =='POST':
        updt_name = request.form.get("name")
        this_sect.name = updt_name 
        updt_desc = request.form.get("description")
        this_sect.description = updt_desc
        db.session.commit()
        return redirect("/dashboard")
    return render_template('edit_section.html', this_sect=this_sect)

@app.route("/<int:id>/delete")
@librarian_required
def del_sect(id):
    this_sect = Section.query.get(id)
    db.session.delete(this_sect)
    db.session.commit()
    return redirect("/dashboard")

@app.route("/add_book", methods = ['GET', 'POST'])
@librarian_required
def add_book():
    if request.method == "POST":
        name = request.form.get("name")
        content=request.form.get("content")
        author = request.form.get("author")
        dateissued=request.form.get("dateissued")
        section_name = request.form.get("section_name")
        new_books = Books(name=name, content= content, author=author, section_name = section_name)
        db.session.add(new_books)
        db.session.commit()
        flash('Book added successfully')
        return redirect(url_for('dashboard'))
    all_books=Books.query.all()
    return render_template('add_book.html')

@app.route("/<int:id>/updatebooks", methods = ['GET', 'POST'])
@librarian_required
def update_books(id):
    this_books = Books.query.get(id)
    if request.method =='POST':
        updt_name = request.form.get("name")
        this_books.name = updt_name 
        updt_content = request.form.get("content")
        this_books.content = updt_content
        updt_author=request.form.get("author")
        this_books.author=updt_author
        updt_section=request.form.get("section_name")
        this_books.section_name=updt_section       
        db.session.commit()
        return redirect("/dashboard")
    return render_template('edit_books.html', this_books=this_books)

@app.route("/<int:id>/deletebooks")
@librarian_required
def del_books(id):
    this_books = Books.query.get(id)
    db.session.delete(this_books)
    db.session.commit()
    return redirect("/dashboard")

@app.route('/dashboard')
@librarian_required
def dashboard():
    if 'user_id' in session and session['is_librarian']:
        return render_template('dashboard.html', all_users=User.query.all(), all_sects=Section.query.all(), all_books= Books.query.all())
    else:
        flash('Admin login required')    
        return redirect(url_for('login'))

@app.route("/request-book/<int:id>", methods = ['GET', 'POST'])
@auth_required
def request_book(id):
    user_id = session.get('user_id')
    if user_id:
        user_request_count = Request.query.filter_by(user_id=user_id).count()
        if user_request_count >= 5:
            flash('You have already requested the maximum number of books.')
            return redirect(url_for('user_dash'))
        request_book=Books.query.get(id)
        if request_book:
            number_of_days=request.form.get("number_of_days")             
            existing_request = Request.query.filter_by(user_id=session["user_id"], number_of_days= number_of_days, book_id=id).first()
            if existing_request:
                flash('You have already requested this book.')
                return redirect(url_for('user_dash'))
        if request.method == "POST":       
            number_of_days=request.form.get("number_of_days")        
            new_request= Request(user_id=session["user_id"], book_id=id, number_of_days=number_of_days)
            db.session.add(new_request)
            db.session.commit()
            flash('Request added successfully')
            return redirect(url_for('user_dash'))
        user_request=Request.query.all()
        return render_template('request_books.html', request_book=request_book)   
    
@app.route("/approve_request/<int:id>")
def approve_request(id):
    request_book = Request.query.get(id)
    if request_book:
        request_book.status = "Approved"
        request_book.return_date=datetime.now() + timedelta(days=request_book.number_of_days)
        db.session.commit()
        flash("Approved")
    return redirect(url_for("user_requeststatus"))    

@app.route("/reject_request/<int:id>")
@librarian_required
def reject_request(id):
    request_book = Request.query.get(id)
    if request_book:
        if request_book.status == 'Rejected':
            flash('Access for this request has already been rejected.', 'error')
            return redirect(url_for('user_requeststatus'))
        request_book.status = "Rejected"
        db.session.commit()
        flash("Rejected")
    return redirect(url_for("user_requeststatus"))

@app.route('/revoke_access/<int:id>')
@librarian_required
def revoke_access(id):
    request_book = Request.query.get(id)
    if request_book:
        if request_book.status == 'Rejected':
            flash('Access for this request has already been rejected.', 'error')
            return redirect(url_for('user_requeststatus'))
        request_book.status = 'Revoked'     
        db.session.commit()
        flash('Access revoked successfully.', 'success')
        return redirect(url_for('user_requeststatus'))
    flash('Request not found')
    return redirect(url_for('user_dash'))

@app.route("/mark_as_read/<int:id>")
def mark_as_read(id):    
    request_book = Request.query.get(id)
    if request_book.status=='Approved':
        request_book.read_by_user = True
        db.session.commit()               
    return redirect(url_for('profile'))

@app.route('/submit_feedback/<int:id>', methods=['GET', 'POST'])
@auth_required
def submit_feedback(id):
    user_id = session.get('user_id')
    if user_id:
        request_book=Books.query.get(id)
        if request_book:
            if request.method=='POST':
                user_feedback = request.form.get('user_feedback')
                feedback = Feedback(book_id=id, user_id=user_id, user_feedback=user_feedback)
                db.session.add(feedback)
                db.session.commit()        
                flash('Feedback submitted successfully.') 
                return redirect(url_for('profile'))
            return render_template('feedback.html', request_book = request_book)       
        else:
            flash('Book Not Found.')   
            return redirect(url_for('profile')) 
    else:
        flash('login as user')
        return redirect('login')
    
@app.route('/userfeedback')
def userfeedback():
    return render_template('userfeedback.html', feedback=Feedback.query.all())

@app.route('/book')
def book():
    return render_template('book.html', all_books=Books.query.all())

@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")
    if query:        
        ebooks = Books.query.filter(
        (Books.name.ilike(f"%{query}%")) |
        (Books.author.ilike(f"%{query}%")) |
        (Books.section_name.ilike(f"%{query}%"))).all()           
    else:
        ebooks=[] 
    return render_template("user_home.html", all_books=ebooks)

if __name__ == '__main__':
    app.run(debug=True)
