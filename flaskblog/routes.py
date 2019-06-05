import secrets
import os
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm
from flaskblog.model import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

    


##@app.route("/pagename") helps create a new route that can be access by adding /pagename at the end of address
##def pagename():
##    return "the webpage content"
##since it is to messy to input the whole html webpage here so we use render_template to return the html file
##render_template("filename", variables=variables) the file should be in  ./templates directory, variables are info you want to access in this page

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template('home-temp.html', posts = posts)

@app.route("/about")
def about():
    return render_template('about-temp.html', title = 'About')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,email=form.email.data,password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created for {}, you are now able to log in!'.format(form.username.data), 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        #get user info from database
        user = User.query.filter_by(email=form.email.data).first()
        #if the password matches the email
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            #login the user
            login_user(user, remember=form.remember.data)
            #if they are directed here because login is reqired for some page then after login send them back to that page
            next_page = request.args.get('next')
            flash('Log in successfully for {}!'.format(form.email.data), 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password!', 'danger')
    return render_template('login.html', title='login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/account")
@login_required
def account():
    image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
    return render_template('account.html', title='my account', image_file=image_file)
##    if current_user.is_authenticated:
##        return render_template('account.html', title='my account')
##    else:
##        return redirect(url_for('login'))
##    implemented by login_required

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    #scale down the size
    output_size = (125,125)
    tn = Image.open(form_picture)
    tn.thumbnail(output_size)
    
    tn.save(picture_path)
    return picture_fn

@app.route("/update_info", methods=['GET', 'POST'])
@login_required
def update_info():
    form = UpdateAccountForm()
    image_file = url_for('static', filename='profile_pics/'+current_user.image_file)
    if form.validate_on_submit():
        #checking if profile picture is updated
        if form.picture.data:
            picture_fn = save_picture(form.picture.data)
            current_user.image_file = picture_fn
        #update the user info in database
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account info updated!','success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('update_info.html', title='update info', form=form, image_file=image_file)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('New post has been created!','success')
        return redirect(url_for('home'))
    return render_template('new_post.html',title='New Post', form=form, legend='Update Post')


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title='post.title', post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Your post has been updated!','success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method=='GET':
        form.title.data=post.title
        form.content.data=post.content
    return render_template('new_post.html',title='Update Post', form=form, legend='Update Post', post_id=post_id)

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!','success')

    
    return redirect(url_for('home'))

@app.route("/user/<string:username>")
def user_post(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
            .order_by(Post.date_posted.desc())\
            .paginate(page=page, per_page=4)
    return render_template('user_post.html', posts = posts, user=user)

def send_reset_email(user):
    token =  user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='lyz625747835@gmail.com',
                  recipients=[user.email])
    msg.body = '''To reset your password, visit the following link in 10 min:
{}

If you did not make the request then just ignore this email.
'''.format(url_for('reset_password', token=token, _external=True))
    mail.send(msg)


@app.route("/forget_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email with instructions to reset your password has been sent to your email address!','info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Forget Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('The link is invalid or has expired, please request for reset email again', 'warning')
        return  redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_pw
        db.session.commit()
        flash('Your password has been updated, you are now able to log in!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password', form=form)
