from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_required, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text,ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm,RegisterForm,LogInForm,CommentForm
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
load_dotenv()

current_year=date.today().strftime("%Y")
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["FLASK_KEY"]
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager=LoginManager()
login_manager.init_app(app)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URI"]
db = SQLAlchemy(model_class=Base)
db.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)



######### Relational DataBase   
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))   
    #This will act like a List of BlogPost objects attached to each User. 
    #The "author" refers to the author property in the BlogPost class.
    posts: Mapped[list["BlogPost"]] = relationship(back_populates="author")
    comments:Mapped[list["Comment"]]=relationship(back_populates="comment_author")
    
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
        
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author: Mapped["User"] = relationship(back_populates="posts")
    
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments:Mapped[list["Comment"]]=relationship(back_populates="comment_blogpost")

class Comment(db.Model):
    __tablename__="comments"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    text:Mapped[str]=mapped_column(String(500),nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    comment_author: Mapped["User"] = relationship(back_populates="comments")
    blogpost_id:Mapped[int]=mapped_column(Integer,ForeignKey("blog_posts.id"))
    comment_blogpost:Mapped["BlogPost"]=relationship(back_populates="comments")
with app.app_context():
    db.create_all()
    

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))


#Create admin-only decorator
def admin_only(f):
    @login_required
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)        
    return decorated_function

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register',methods=["GET","POST"])
def register():
    register_form=RegisterForm()
    if register_form.validate_on_submit():
        pw=register_form.password.data
        email_form=register_form.email.data
        name_form=register_form.name.data
        if pw and email_form and name_form:
            duplicate_entry=db.session.execute(db.select(User).where(User.email==email_form)).scalar()
            if duplicate_entry:
                flash("User already prersent. Please Login instead","warning")
                return redirect(url_for('login'))
            hashed_and_salted_password=generate_password_hash(password=pw,method="pbkdf2:sha256",salt_length=8)
            new_user=User(
                name=name_form,
                email=email_form,
                password=hashed_and_salted_password
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("Registered and Logged In","success")
            return redirect(url_for("get_all_posts"))
    header_title = 'Register'
    return render_template("register.html",form=register_form,logged_in=current_user.is_authenticated,title=header_title,footer=current_year)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login',methods=["GET","POST"])
def login():
    login_form=LogInForm()
    if login_form.validate_on_submit():
        email_login=login_form.email.data
        password_login=login_form.password.data
        if email_login and password_login:
            user_data=db.session.execute(db.select(User).where(User.email==email_login)).scalar()
            if user_data:
                if check_password_hash(user_data.password,password_login) and user_data.email==email_login:
                    login_user(user_data)
                    flash("You're Successfully Logged In","success")
                    return redirect(url_for("get_all_posts"))
                else:
                    flash("Invalid Email or Password","danger")
                    return redirect(url_for('login'))
            else:
                flash("User data not available, Please Register first","warning")
                return redirect(url_for('register'))
    header_title = 'LogIn'
    return render_template("login.html",form=login_form,logged_in=current_user.is_authenticated,title=header_title,footer=current_year)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Successfully Logged Out","info")
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    header_title = 'BlogHub'
    return render_template("index.html", all_posts=posts,logged_in=current_user.is_authenticated,title=header_title,footer=current_year)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods=["GET","POST"])

def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form=CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment","warning")
            return redirect(url_for("login"))
        new_comment = Comment(
            text=comment_form.body.data,
            comment_author=current_user,
            comment_blogpost=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    header_title = 'BlogHub'
    return render_template("post.html", post=requested_post,logged_in=current_user.is_authenticated,form=comment_form,user=current_user,gravatar=gravatar,title=header_title,footer=current_year)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    header_title = 'New Post'
    is_admin = current_user.is_authenticated and current_user.id == 1
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated, is_edit=False, is_admin=is_admin,title=header_title,footer=current_year)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author.name,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        #post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    header_title = 'Edit'
    is_admin = current_user.is_authenticated and current_user.id == 1
    return render_template("make-post.html", form=edit_form, is_edit=True, logged_in=current_user.is_authenticated, is_admin=is_admin,title=header_title,footer=current_year)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    header_title = 'About'
    return render_template("about.html",logged_in=current_user.is_authenticated,title=header_title,footer=current_year)


@app.route("/contact",methods=['GET','POST'])
def contact():
    if request.method=='POST':
        _email=os.environ["EMAIL"]
        password=os.environ["PASS"]
        name=request.form['name']
        email=request.form['email']
        ph_no=request.form['phone']
        msg=request.form['message']
        new_letter=f"Name: {name}\nEmail Id: {email}\nPhone no: {ph_no}\nMessage:{msg}"
        data=[name,email,ph_no,msg]

        email_message = MIMEText(new_letter)
        email_message['Subject'] = f"Feedback from {name}"
        email_message['From'] = _email
        email_message['To'] = "devilsayan16@gmail.com"

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                connection.starttls()
                connection.login(user=_email, password=password)
                connection.sendmail(from_addr=_email, to_addrs=["devilsayan16@gmail.com"],
                                    msg=email_message.as_string())
            #print(f"Email sent successfully to: {"devilsayan16@gmail.com"}")  # Detailed success message
            flash("Successfully Sent Your Message","success")

        except smtplib.SMTPAuthenticationError:
            print("Authentication error. Check your email and password (or App Password).")
            flash("Something Went Wrong","danger")
        except smtplib.SMTPDataError as e:
            print(f"SMTP Data Error: {e}")
            flash("Something Went Wrong","danger")
        except Exception as e:
            print(f"An error occurred: {e}")
            flash("Something Went Wrong","danger")
        #print("Email sending process completed for this birthday.")  # End of email process
        return render_template("contact.html",msg_sent=True)
    else:
        header_title = 'Contact'
        return render_template("contact.html",title=header_title,logged_in=current_user.is_authenticated,footer=current_year)
    


if __name__ == "__main__":
    app.run(debug=False, port=5002)
