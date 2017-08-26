from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from helpers import *
import string
from werkzeug.utils import secure_filename
import os
import datetime

class Del:
  def __init__(self, keep=string.digits):
    self.comp = dict((ord(c),c) for c in keep)
  def __getitem__(self, k):
    return self.comp.get(k)

# configure application
app = Flask(__name__)

#global variables
global void
global first
void="void_VOID_void"
first=True

#settign upload folder
UPLOAD_FOLDER = './'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['csv'])

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///farm.db")






#### LOGIN/LOGOUT ####



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("animals"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted and confirmed
        elif not request.form.get("password"):
            return apology("must provide password")

        elif not request.form.get("confirm_password"):
            return apology("must confirm password")

        #ensure password match
        if request.form.get("confirm_password") != request.form.get("password"):
            return apology("passwords do not match")

        # add username to database
        search = db.execute("SELECT * FROM users WHERE username == :username", username=request.form.get("username"))
        if len(search)!=0:
            return apology("username taken")

        # insert the new user into users, storing the hash of the user's password
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", \
                             username=request.form.get("username"), hash=pwd_context.hash(request.form.get("password")))


        # remember which user has logged in
        session["user_id"] = db.execute("SELECT id FROM users WHERE username LIKE :username", username=request.form.get("username"))
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("animals"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method=="POST":
        if not request.form.get("password") or not request.form.get("confirm_password"):
            return apology("blank field")

        if request.form.get("confirm_password") != request.form.get("password"):
            return apology("passwords do not match")

        db.execute("UPDATE users SET hash=:password WHERE id=:id",\
        password=pwd_context.hash(request.form.get("password")), id=session["user_id"])

        return render_template("password_changed.html")

    else:
        return render_template("change_password.html")









#### ANIMAL INFORMATION ####








@app.route("/", methods=["GET", "POST"])
@login_required
def animals():
    """ show list of animals """

    global first
    global tag

    if request.method=="POST" and first==False:
        tag= request.form["details"]
        first=True
        return animal_details()

    first=False
    info= db.execute("SELECT * FROM animals WHERE user_id=:id", id=session["user_id"])


    return render_template("animals.html", info=info )


@app.route("/details", methods=["GET", "POST"])
@login_required
def animal_details():
    """ Show details for one animal """

    global first
    global tag

    if request.method =="POST" and first==False:
        #delete medication from an animal

        first=True
        if 'delete' in request.form:
            line_id=request.form.get("delete")
            db.execute("DELETE FROM medication WHERE line_id=:line_id", line_id=line_id)
            return animal_details()

        #add medication to the animal
        tag=request.form["add_medication"]
        return add_individual_med()


    animal= db.execute("SELECT * FROM animals WHERE user_id=:id AND tag=:tag", id=session["user_id"], tag=tag)
    infos= db.execute("SELECT * FROM medication WHERE user_id=:id AND tag=:tag", id=session["user_id"], tag=tag)



    first=False
    return render_template("animal_details.html", animal=animal, infos=infos, tag=tag)


@app.route("/medication", methods=["GET", "POST"])
@login_required
def medication():
    """ display all medical info for all animals """
    global first

    if request.method =="POST" and  first==False:
        first=True

        if 'delete' in request.form:
            line_id=request.form.get("delete")
            db.execute("DELETE FROM medication WHERE line_id=:line_id", line_id=line_id)
            return medication()

        return add_medication()

    info= db.execute("SELECT * FROM medication WHERE user_id=:id", id=session["user_id"])

    first=False
    return render_template("medication.html", info=info)





#### EDIT ANIMAL INFO ####







@app.route("/remove", methods=["GET", "POST"])
@login_required
def remove():
    """Remove animals """

    global first

    if request.method=="POST" and first==False:
        first=True

        tags = request.form.getlist('tag')

        for tag in tags:

            animal_id=db.execute("SELECT animal_id FROM animals WHERE user_id=:id AND tag=:tag", id=session["user_id"], tag=tag)

            animal=animal_id[0]['animal_id']

            db.execute("DELETE FROM animals WHERE animal_id=:animal", animal=animal)

            db.execute("DELETE FROM medication WHERE animal_id=:animal", animal=animal)



        return animals()

    first=False
    info= db.execute("SELECT * FROM animals WHERE user_id=:id", id=session["user_id"])

    return render_template("remove.html", info=info)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add animals"""
    global first

    if request.method == "POST" and first==False:
        first=True

        if 'upload' in request.form :

            return upload()

        if not request.form.get("tag") or not request.form.get("gender") or not request.form.get("breed"):
            return apology("blank field(s)")

        tag=request.form.get("tag")
        gender=request.form.get("gender")
        notes=request.form.get("notes")
        breed=request.form.get("breed")

        DOB= request.form.get("DOB")
        TB_test_date= request.form.get("TB_test_date")
        date_moved_in= request.form.get("Date_moved_in")

        #ensure the tag is not a duplicate
        bad= db.execute("SELECT * FROM animals WHERE user_id=:id AND tag=:tag", id=session["user_id"], tag=tag)
        if bad!=[]:
            return apology("tag already in use")

        #add the animals to the database
        db.execute("INSERT INTO animals (user_id, tag, gender, DOB, notes, breed, TB_test_date, date_moved_in) VALUES(:id, :tag, :gender, :DOB, :notes, :breed, :TB_test_date, :date_moved_in)", id=session["user_id"], tag=tag, gender=gender, DOB=DOB, notes=notes, breed=breed, TB_test_date=TB_test_date, date_moved_in=date_moved_in)
        return animals()

    first=False
    return render_template("add.html")

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """ upload a file of animals to database """
    global first

    if request.method == 'POST'and first==False:


        if request.files['file'] is None:
            return apology("no file submitted")

        f = request.files['file']
        if f.filename == '':
            return apology("no selected file")


        filename= secure_filename(f.filename)
        if filename.endswith(".csv"):
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            return apology("wrong file type (.csv only)")

        file = open(filename, "r")

        top=0
        for line in file:
            tag=""
            gender=""
            DOB=""
            breed=""
            date_moved_in=""
            TB_test_date=""
            if top!=0:

                position=1

                a=line[position]
                while a!='"':
                    tag=tag+a
                    position=position+1
                    a=line[position]

                position=position+3
                a=line[position]
                while a!='"':
                    gender=gender+a
                    position=position+1
                    a=line[position]

                position=position+3
                a=line[position]
                while a!='"':
                    DOB=DOB+a
                    position=position+1
                    a=line[position]

                position=position+3
                a=line[position]
                while a!='"':
                    breed=breed+a
                    position=position+1
                    a=line[position]

                position=position+3
                a=line[position]
                while a!='"':
                    date_moved_in=date_moved_in+a
                    position=position+1
                    a=line[position]

                position=position+3
                a=line[position]
                while a!='"':
                    TB_test_date=TB_test_date+a
                    position=position+1
                    a=line[position]

                db.execute("INSERT INTO animals (user_id, tag, gender, DOB, breed, date_moved_in, TB_test_date) VALUES (:id, :tag, :gender, :DOB, :breed, :date_moved_in, :TB_test_date)", id=session["user_id"], tag=tag, gender=gender, DOB=DOB, breed=breed, date_moved_in=date_moved_in, TB_test_date=TB_test_date)

            top=1

        first=True
        os.remove(filename)
        return animals()

    first=False
    return render_template("upload.html")








#### MEDICAL INFORMATION ####






@app.route("/medical_index", methods=["GET", "POST"])
@login_required
def medication_cabinet():
    """ display alist of all drugs with withdrawal periods and any notes """
    global first
    global void

    if request.method=="POST" and first==False:
        #remove a drug from database

        first=True
        if 'foo' in request.form:
            return new_medication()
        if not request.form.get('delete'):
            return apology('bad form submission')

        drug_id=request.form.get('delete')

        db.execute('UPDATE drugs SET notes=:void WHERE drug_id=:drug_id', void=void, drug_id=drug_id)

    info= db.execute("SELECT * FROM drugs WHERE user_id=:id AND notes<>:void AND name<>:void", void=void, id=session["user_id"])
    first=False
    return render_template("medication_cabinet.html", info=info )






#### EDIT MEDICAL INFORMATION ####






@app.route("/new_medication", methods=["GET", "POST"])
@login_required
def new_medication():
    """ add new drug to the database """

    global first

    if request.method == 'POST' and first==False:
        first=True

        if not request.form.get('name') or not request.form.get('meat_withdrawal') or not request.form.get('milk_withdrawal'):
            return apology('blank field(s)')

        name=request.form.get('name')

        n=db.execute("SELECT name FROM drugs WHERE user_id=:user_id", user_id=session["user_id"])

        b=n[0]['name']

        if name==b:
            return apology("name already in use")


        meat_withdrawal=request.form.get('meat_withdrawal')
        milk_withdrawal=request.form.get('milk_withdrawal')
        notes=request.form.get('notes')

        db.execute("INSERT INTO drugs (user_id, name, meat_withdrawal, milk_withdrawal, notes) VALUES (:user_id, :name, :meat_withdrawal, :milk_withdrawal,:notes)", user_id=session["user_id"], name=name, meat_withdrawal=meat_withdrawal, milk_withdrawal=milk_withdrawal, notes=notes)

        return medication_cabinet()

    first=False
    return render_template("new_medication.html")

@app.route("/add_individual_med", methods=["GET", "POST"])
@login_required
def add_individual_med():
    """ Add medication to an animal (After clicking the button from the details page) """

    global first
    global tag
    global void

    if request.method =="POST" and first==False:

        if not request.form.get("selected") or not request.form.get("date_administered") :
            return apology("empty field(s)")

        aid=db.execute("SELECT animal_id FROM animals WHERE user_id=:id AND tag=:tag", id=session["user_id"], tag=tag)
        if aid==[]:
            return apology("tag does not exist")

        drug_id=request.form.get("selected")
        date_administered=request.form.get("date_administered")
        notes=request.form.get("notes")

        dru=db.execute("SELECT name FROM drugs WHERE drug_id=:drug_id", drug_id=drug_id)
        mewithdrawal= db.execute("SELECT meat_withdrawal FROM drugs WHERE drug_id=:drug_id", drug_id=drug_id)
        miwithdrawal= db.execute("SELECT milk_withdrawal FROM drugs WHERE drug_id=:drug_id", drug_id=drug_id)

        drug=dru[0]['name']
        meat=mewithdrawal[0]['meat_withdrawal']
        milk=miwithdrawal[0]['milk_withdrawal']

        meat_withdrawal_end=date_administered+datetime.timedelta(days=int(meat))
        milk_withdrawal_end=date_administered+datetime.timedelta(days=int(milk))


        animal_id=aid[0]['animal_id']

        db.execute("INSERT INTO medication (user_id, tag, animal_id, drug, date_administered, meat_withdrawal, milk_withdrawal, notes) VALUES(:id, :tag, :animal_id, :drug, :date_administered, :meat_withdrawal_end,:milk_withdrawal_end, :notes)",\
                    id=session["user_id"], tag=tag, animal_id=animal_id, drug=drug, date_administered=date_administered, meat_withdrawal_end=meat_withdrawal_end, milk_withdrawal_end=milk_withdrawal_end, notes=notes)

        first=True
        return animal_details()

    info=db.execute("SELECT * FROM drugs WHERE user_id=:id AND notes<>:void", id=session["user_id"], void=void)
    first=False
    return render_template("individual_medication.html", info=info)

@app.route("/add_medication", methods=["GET", "POST"])
@login_required
def add_medication():
    """ add new drug to an animal """

    global first
    global void

    if request.method=="POST" and first==False:
        first=True
        if not request.form.get("selected"):
            return apology("form not completed")

        drug_id=request.form.get("selected")
        date_administered=request.form.get("date_administered")
        notes=request.form.get("notes")

        dru=db.execute("SELECT name FROM drugs WHERE drug_id=:drug_id", drug_id=drug_id)
        mewithdrawal= db.execute("SELECT meat_withdrawal FROM drugs WHERE drug_id=:drug_id", drug_id=drug_id)
        miwithdrawal= db.execute("SELECT milk_withdrawal FROM drugs WHERE drug_id=:drug_id", drug_id=drug_id)

        drug=dru[0]['name']
        meat=mewithdrawal[0]['meat_withdrawal']
        milk=miwithdrawal[0]['milk_withdrawal']

        meat_withdrawal_end=date_administered+datetime.timedelta(days=int(meat))
        milk_withdrawal_end=date_administered+datetime.timedelta(days=int(milk))

        if 'multiple' in request.form:

            global medical_info
            medical_info={'drug' : drug, 'date_administered' : date_administered, 'meat_withdrawal_end' : meat_withdrawal_end, 'milk_withdrawal_end' : milk_withdrawal_end, 'notes' : notes}
            return multiple_medication()

        return apology("form error")

    info=db.execute("SELECT * FROM drugs WHERE user_id=:id AND notes<>:void", id=session["user_id"], void=void)

    first=False
    return render_template("add_medication.html", info=info)

@app.route("/multiple_medication", methods=["GET", "POST"])
@login_required
def multiple_medication():
    """ add medication to multiple animals """

    global first
    global medical_info

    if request.method=="POST" and first==False:
        first=True

        tags = request.form.getlist('tag')

        for tag in tags:
            animal=db.execute("SELECT animal_id FROM animals WHERE user_id=:id AND tag=:tag", id=session["user_id"], tag=tag)
            animal_id=animal[0]['animal_id']

            drug=medical_info['drug']
            date_administered=medical_info['date_administered']
            meat_withdrawal=medical_info['meat_withdrawal_end']
            milk_withdrawal=medical_info['milk_withdrawal_end']
            notes=medical_info['notes']

            db.execute("INSERT INTO medication (user_id, tag, animal_id, drug, date_administered, milk_withdrawal, meat_withdrawal, notes) VALUES(:id, :tag, :animal_id, :drug, :date_administered, :milk_withdrawal, :meat_withdrawal, :notes)",\
                        id=session["user_id"], tag=tag, animal_id=animal_id, drug=drug, date_administered=date_administered, milk_withdrawal=milk_withdrawal, meat_withdrawal=meat_withdrawal, notes=notes)

        return medication()

    first=False
    info= db.execute("SELECT * FROM animals WHERE user_id=:id", id=session["user_id"])

    return render_template("multiple_medication.html", info=info)

if __name__ == '__main__':
    app.run(debug=True)