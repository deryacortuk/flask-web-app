from flask import Flask,render_template,redirect,flash,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#user login decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      if "logged_in" in session:              
        
        return f(*args, **kwargs)
      else:
        flash("please login","danger")
        return redirect(url_for("signin"))
    return decorated_function




#user register form
class RegisterForm(Form):
    name = StringField("Name Surname:",validators=[validators.Length(min=4,max=25)])
    email = StringField("Email:",validators=[validators.Email(message="Email is invalid or already taken")])
    username = StringField("Username:",validators=[validators.Length(min=5,max=30)])
    password = PasswordField("Password:",validators=[validators.Length(min=4,max=25),validators.DataRequired(message="Make sure it's at least 15 characters OR at least 8 characters including a number and a lowercase letter"),validators.EqualTo(fieldname="confirm",message="not equal")])
    confirm =PasswordField("Password confirm")

#user login form
class LoginForm(Form):
    username =StringField("Name Surname:")
    password = PasswordField("Password:")
 #article form

class ArticleForm(Form):
    title = StringField("article title",validators=[validators.Length(min=2,max=50)])
    content = TextAreaField("article content",validators=[validators.Length(min=10)])
    

app= Flask(__name__)
app.secret_key="soft"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="softdb"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/article/<string:id>")
def article(id):
    cursor =mysql.connection.cursor()
    inquiry ="select * from article where id=%s"
    result =cursor.execute(inquiry,(id,))
    if result >0:
        article =cursor.fetchone()
        return render_template("detail.html",article=article)
    else:
        
        return render_template("detail.html")
   
   

@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name = form.name.data
        username=form.username.data
        email =form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor =mysql.connection.cursor()
        inquiry="Insert into users (name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(inquiry,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()    
        flash("You were successfully logged up.","success")    
        return redirect(url_for("signin"))
    else:    
        return render_template("register.html",form=form)

@app.route("/login",methods=["GET","POST"])
def signin():
    form =LoginForm(request.form)
    if request.method=="POST":
        username = form.username.data
        password_entered = form.password.data
        cursor =mysql.connection.cursor()
        inquiry ="Select * From users where username = %s"
        result =cursor.execute(inquiry,(username,))
        if result >0:
            data=cursor.fetchone()
            real_password =data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("you're successfully sign in","success")
                session["logged_in"] =True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("password is invalid","danger")
                return redirect(url_for("signin"))

        flash("Invalid login or password. Please try again.","warning")
        return redirect(url_for("signin"))
    return render_template("login.html",form=form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    inquiry="select * from article where author =%s"
    result =cursor.execute(inquiry,(session["username"],))
    if result > 0:
        article=cursor.fetchall()
        return render_template("dashboard.html",article=article)
    else:
        return render_template("dashboard.html")

    return render_template("dashboard.html")

# article page
@login_required
@app.route("/addarticle",methods=["POST","GET"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title =form.title.data    
        content = form.content.data    
        cursor =mysql.connection.cursor()
        inquiry = "Insert into article(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(inquiry,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("article is added","warning")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form=form)
@app.route("/articles",methods=["GET"])
def articles():
    cursor= mysql.connection.cursor()
    inquiry = "select * from article"
    result=cursor.execute(inquiry)
    if result>0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        flash("articles are not exist")
        return render_template("articles.html")

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor =mysql.connection.cursor()
    inquiry ="Select * from article where author=%s and id=%s"
    result =cursor.execute(inquiry,(session["username"],id))
    if result>0:
        inquiry1="Delete from article where id=%s"
        cursor.execute(inquiry1,(id,))        
        mysql.connection.commit()
        return redirect(url_for("dashboard"))    
               
        
    else:
        flash("article is not exist or you must not delete","danger")
        return redirect(url_for("index"))
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def edit(id):
    if request.method=="GET":
        cursor =mysql.connection.cursor()
        inquiry ="select * from article where id =%s and author = %s"
        result=cursor.execute(inquiry,(id,session["username"]))
        if result ==0:
            flash("article is not exist or you cannot do that","danger")
            return redirect(url_for("index"))

        else:
            article =cursor.fetchone()
            form =ArticleForm()
            form.title.data =article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form=form)

    else:
        form =ArticleForm(request.form)
        newTitle =form.title.data
        newcontent=form.content.data
        inquiry2="Update article Set title=%s ,content=%s where id =%s"
        cursor =mysql.connection.cursor()
        cursor.execute(inquiry2,(newTitle,newcontent,id))
        mysql.connection.commit()
        flash("article updated","success")
        return redirect(url_for("dashboard"))
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword =request.form.get("keyword")
        cursor =mysql.connection.cursor()
        inqury ="select * from article where title like '%" +keyword   + "%'"
        result = cursor.execute(inqury)
        if result ==0:
            flash("the article is not exist")
        else:
            articles =cursor.fetchall()
            return render_template("articles.html",articles=articles)




    

        
            
        







if __name__=="__main__":
    app.run(debug=True)
   