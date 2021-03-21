from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from sqlalchemy.exc import IntegrityError
from forms import CreateUserForm, LoginForm, AddFeedback

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    """Home page"""
    return redirect('/register')
   

@app.route('/register', methods=["GET", "POST"])
def registration():
    """show register user form on GET request and handle form submit on POST request"""
    if 'username' not in session:
        form = CreateUserForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            email = form.email.data
            first_name = form.first_name.data
            last_name = form.last_name.data
            new_user = User.register(username, password, email, first_name, last_name)
            db.session.add(new_user)
            try:
                db.session.commit()
            except IntegrityError:
                form.username.errors.append('Username Taken')
                return render_template('register.html', form=form)
            session['username'] = new_user.username
            flash('Welcome! Successfully created your account!', 'success')
            return redirect(f'/users/{username}')

        return render_template('register.html', form=form)

    username = session['username']
    return redirect(f'/users/{username}')
    
@app.route('/login', methods=["GET", "POST"])
def login_user():
    """show login page on GET request and handle form submit for login on POST request."""
    if 'username' not in session:
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            user = User.authenticate(username, password)
            if user:
                flash(f"welcome back, {user.username}!", "primary")
                session['username'] = user.username
                return redirect(f'/users/{username}')
            else:
                form.username.errors = ['Invalid username/password']
    
        return render_template('login.html', form=form)

    username = session['username']
    return redirect(f'/users/{username}')

@app.route('/logout')
def logout_user():
    session.pop('username')
    flash('Goodbye', 'info')
    return redirect('/')

@app.route("/users/<username>", methods=["GET"])
def show_user(username):
    """Display secret page"""
    if 'username' not in session or username != session['username']:
        flash('You do not have permission to access this content', 'warning')
        return redirect('/')
    user = User.query.get_or_404(username)
    feedbacks = Feedback.query.filter_by(username=username).all()
    

    return render_template('userdetail.html', user=user, feedbacks=feedbacks)

@app.route("/users/<username>/delete", methods=["GET", "POST"])
def delete_user(username):
    """Delete user"""
    if 'username' not in session or username != session['username']:
        flash('you do not have permission to do that', 'warning')
        return redirect('/')
        
    user = User.query.get_or_404(username)

    db.session.delete(user)
    db.session.commit()

    flash(f'user account "{username}" has been deleted','danger')
    return redirect('/')

@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    """Render add feedback form on GET request and handle submit feedback form on POST request"""
    if 'username' not in session or username != session['username']:
        flash('you do not have permission to do that', 'warning')
        return redirect('/')
    form = AddFeedback()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_fb = Feedback(title=title, content=content, username=username)
        db.session.add(new_fb)
        db.session.commit()
        flash('feedback submitted', 'info')
        return redirect(f'/users/{username}')
    return render_template('feedback.html', form=form)

@app.route("/feedback/<int:id>/update", methods=["GET", "POST"])
def edit_feedback(id):
    """Render update feedback form on GET request and handle submit feedback form on POST request"""
    fb = Feedback.query.get_or_404(id)
    if 'username' not in session or fb.username != session['username']:
        flash('you do not have permission to do that', 'warning')
        return redirect('/')
    form = AddFeedback(obj=fb)

    if form.validate_on_submit():
        fb.title = form.title.data
        fb.content = form.content.data
        db.session.commit()
        flash('feedback edited', 'info')
        return redirect(f'/users/{fb.username}')
    
    return render_template('feedback.html', form=form)

@app.route("/feedback/<int:id>/delete", methods=["POST"]) 
def delete_feedback(id):
    """Delete feedback"""
    fb = Feedback.query.get_or_404(id)
    if 'username' not in session or fb.username != session['username']:
        flash('you do not have permission to do that', 'warning')
        return redirect('/')
    
    db.session.delete(fb)
    db.session.commit()

    flash(f'feedback deleted', 'danger')
    return redirect(f'/users/{fb.username}')