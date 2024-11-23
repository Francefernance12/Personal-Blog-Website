import smtplib
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from functools import wraps
from os import getenv
from dotenv import load_dotenv
from flask_migrate import Migrate
# Importing personal module
from forms import CreatePostForm, UserForm, LoginForm, CommentForm, ContactForm
from config import Config
from dbModels import db, User, BlogPost, Comments, Roles

load_dotenv()

# Flask app
app = Flask(__name__)
app.config.from_object(Config)
migrate = Migrate(app, db)
# Initialize extensions
Bootstrap5(app)
ckeditor = CKEditor(app)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# create db
with app.app_context():
    db.create_all()


# Creates role decorator
def role_required(role_names):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"Checking roles for user: {current_user.username if current_user.is_authenticated else 'Guest'}")
            if not current_user.is_authenticated:
                print("User is not authenticated.")
                abort(403)
            if current_user.role.name not in role_names:
                print(f"Access denied. Role '{current_user.role.name}' not in {role_names}.")
                abort(403)
            print("Access granted.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# roles_required
WEBSITE_ROLES = ["Administrator", "Editor", "User"]
ADMIN_ROLES = [WEBSITE_ROLES[0]]
EDIT_ROLES = WEBSITE_ROLES[:2]

# Routes


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = UserForm()
    # once form is submitted
    if register_form.validate_on_submit():
        # Extract user data
        email = register_form.email.data
        username = register_form.username.data
        password = register_form.password.data

        # checking if the user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User already exists. Please log in.')
            return redirect(url_for('register'))

        # assigning roles to new registered users
        user_role_id = db.session.query(Roles).filter_by(name='User').first().id

        # Create a new User object
        new_user = User(email=email, username=username, role_id=user_role_id)
        new_user.set_password(password)

        # add user to db
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving to the database. Please try again.')
            print(f"Database error: {e}")

        # log user in
        login_user(new_user)
        flash('Registration successful!')
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=register_form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        # user data
        email = login_form.email.data
        password = login_form.password.data

        # finding the user in db
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        # checks if user
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')  # Retrieve the 'next' parameter
            flash('Logged In!')
            return redirect(next_page or url_for('get_all_posts'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template("login.html", form=login_form, logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out")
    return redirect(url_for('get_all_posts'))


# home page
@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated)


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comments(
            text=comment_form.comment.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, logged_in=current_user.is_authenticated,
                           comment_form=comment_form)


@app.route("/new-post", methods=["GET", "POST"])
@role_required(ADMIN_ROLES)
def add_new_post():
    print("Entered add_new_post route")
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            creation_date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        try:
            db.session.commit()
            print("Post added to database")
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {e}")
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@role_required(EDIT_ROLES)
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@role_required(ADMIN_ROLES)
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


#
@app.route("/delete-comment/<int:post_id>/<int:comment_id>")
@role_required(ADMIN_ROLES)
def delete_comment(post_id, comment_id):
    comment_to_delete = db.get_or_404(Comments, comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('show_post', post_id=post_id))


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    msg_sent = False
    form = ContactForm()
    if form.validate_on_submit():
        recipient = getenv("RECIPIENT_EMAIL")
        app_password = getenv("APP_PASSWORD")
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as connection:  # Port 587 for TLS
                connection.starttls()  # Secure the connection
                connection.login(user=recipient, password=app_password)
                message = (
                    f"Subject:Blog Contact Message\n\n"
                    f"Name: {form.name.data}\n"
                    f"Email: {form.email.data}\n"
                    f"Phone: {form.phone.data}\n\n"
                    f"Message: {form.message.data}"
                )
                connection.sendmail(
                    from_addr=form.email.data,
                    to_addrs=recipient,
                    msg=message
                )
            msg_sent = True
        except Exception as e:
            # Log or print the exception for debugging
            print(f"Failed to send email: {e}")

    return render_template("contact.html", logged_in=current_user.is_authenticated, form=form, msg_sent=msg_sent)


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)
