import os
import time
import pyrebase
from firebase_admin import credentials, firestore, initialize_app
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for, session
from datetime import timedelta
from PIL import Image
# from geopy.distance import geodesic
from operator import itemgetter
from flask_mobility import Mobility


firebaseConfig = {
    "apiKey": "AIzaSyDnN_lXnJRwcZrO3SBIbINjR20iJ5XhJyQ",
    "authDomain": "temaribet-af8a0.firebaseapp.com",
    "databaseURL": "https://temaribet-af8a0-default-rtdb.firebaseio.com",
    "projectId": "temaribet-af8a0",
    "storageBucket": "temaribet-af8a0.appspot.com",
    "messagingSenderId": "361477504348",
    "appId": "1:361477504348:web:bb1f559f4687130e691599"
}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()
rdb = firebase.database()  # firebase realtime db only for storing users
strj = firebase.storage()
cred = credentials.Certificate(
    'temaribet-af8a0-firebase-adminsdk-w1moa-500c242ed6.json')
default_app = initialize_app(cred)

db = firestore.client()  # firebase firestore to store form related data

person = {"is_logged_in": False, "is_verified": False,
          "name": "", "email": "", "number": "", "uid": "", "id": "", "role": ""}

app = Flask(__name__)
Mobility(app)
app.secret_key = "__temaribetsessionkey__"  # key for session
app.permanent_session_lifetime = timedelta(days=7)


@app.route("/home")
@app.route("/")
def home():
    return render_template('home.html', p=[])

# ......................................LOGIN METHOD......................................
# redirect route

@app.route('/admin')
def admin():
    print(list(db.collection('tutor_form').get()))
    return render_template('admin.html')


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/loginRes", methods=['GET', 'POST'])
def loginRes():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["password"]

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            # this query returns a list
            db_user = [u.val() for u in rdb.child("users").order_by_child(
                "uid").equal_to(user["localId"]).get()]
            # make sure token is refreshed
            sign_user = auth.refresh(user['refreshToken'])
            person["name"] = db_user[0]["username"]
            person["email"] = db_user[0]["email"]
            person["uid"] = db_user[0]["uid"]
            # person["role"] = db_user[0]["role"]
            person["is_verified"] = db_user[0]["is_verified"]
            person["number"] = db_user[0]["phone_number"]
            person["is_logged_in"] = True
            # token id wont e saved on rdb
            person["id"] = sign_user["idToken"]
            print(person)
            # session.permanent = True
            # session["user"] = person["id"]
            return redirect(url_for('index'))
        except Exception as error:
            error_string = str(error)
            print("INVALID_PASSWORD" in error_string)
            flash("Username or Password is not Correct", "info")
            return redirect(url_for('login'))
            # If there is any error, redirect back
    else:
        if person["is_logged_in"]:
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))

# ......................................SIGNUP METHOD......................................
# redirect route


@app.route("/signup")
def signup():
    return render_template("tutor.html")


@app.route("/signupRes", methods=['GET', 'POST'])
def signupRes():
    if request.method == "POST":
        result = request.form
        username = result["username"]
        email = result["email"]
        number = result["number"]
        password = result["password"]
        # role = request.form.get('role')

        try:
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
            person["email"] = user["email"]
            person["id"] = user["idToken"]
            person["uid"] = user["localId"]
            person["is_logged_in"] = True
            person["name"] = username
            person["number"] = number
            # person["role"] = role
            # only JSON type data is allowed to save on firebase
            json_user = {
                "username": username,
                "email": email,
                "phone_number": number,
                "uid": person["uid"],
                # "role": role,
                "is_verified": person["is_verified"],
            }
            print(json_user)
            res = rdb.child("users").child(person["uid"]).set(json_user)
            return redirect(url_for('index'))
        except:
            print("Error, please try again later.")
            # If there is any error, redirect back
            # return redirect(url_for('signup'))
    else:
        if person["is_logged_in"]:
            return redirect(url_for('index'))
        else:
            return redirect(url_for('signup'))


# ......................................INDEX METHOD......................................
# get the user from sess


@app.route("/index", methods=['GET'])
def index():
    info = auth.get_account_info(person['id'])
    if info['users'][0]["emailVerified"]:
        if person["is_verified"] != True:
            person["is_verified"] = True
            # db_user = [u.val() for u in rdb.child("users").order_by_child(
            #     "uid").equal_to(person["uid"]).get()]
            json_user = {
                "username": person["name"],
                "email": person["email"],
                "phone_number": person["number"],
                "uid": person["uid"],
                # "role": person["role"],
                "is_verified": person["is_verified"],
            }
            rdb.child("users").child(person["uid"]).update(json_user)
        return render_template('tutor_profile', person=person)
    else:
        return render_template("verify.html", name=person["name"])
# ......................................PARENT METHOD......................................


@app.route("/parent", methods=['POST'])
def parent():
    # get feild values
    req = request.form.to_dict()

    # to get values of <select> tag
    select = request.form.get('grade_level')
    select2 = request.form.get('grade_level_two')
    select3 = request.form.getlist('subjects')
    # check if all feilds are correctly filled
    if select == None or select2 == None or select3 == [] or req["email"] == "" or req["fname"] == "" or req["lname"] == "" or req["clname"] == "" or req["cfname"] == "":
        warning = "Please fill in all required fields!"
        return render_template("home.html", warning=warning)
    # get size from DB for id
    lenz = len(list(db.collection('parent_form').get()))
    # create object for DB
    doc = {
        "id": lenz + 1,
        "assigned": False,
        "parent_mail": req["email"],
        "parent_first_name": req["fname"],
        "parent_last_name": req["lname"],
        "address": "32,33",
        # childs_info
        "child_first_name": req["cfname"],
        "child_last_name": req["clname"],
        "sex": req["sex"],
        "grade_level": select,
        "grade_level_two": select2,
        "subjects": select3,
    }
    # write on DB
    db.collection('parent_form').document(str(lenz + 1)).set(doc)
    success = "Everything went perfect!, We will contact you using your email address."

    return render_template("home.html", success=success)

# ......................................TUTOR METHOD......................................


@app.route("/tutor", methods=['POST', 'GET'])
def tutor():

    if request.method == "POST":
        req = request.form.to_dict()
        # pic = request.files['img']

        # select3 = request.form.getlist('subject')

        # if select == None or select2 == None or select3 == [] or req["email"] == "" or req["fname"] == "" or req["lname"] == "" or req["clname"] == "" or req["cfname"] == "":
        # warning = "Please fill in all required fields!"
        # return render_template("home.html", warning=warning)

        # get size from DB for id
        lenz = len(list(db.collection('tutor_form').get()))

        doc = {
            "id": lenz + 1,
            # "tutor_img": req["img"],
            "assigned": False,
            "tutor_first_name": req["fname"],
            "tutor_last_name": req["lname"],
            "tutor_mail": req["email"],
            "tutor_phone": req["phone"],
            # "tutor_password": req["password"],
            "education_level": req["education"],
            "address": req["address"],
            "sex": req["sex"],
            # "subjects": select3,
        }

        # write on DB
        db.collection('tutor_form').document(str(lenz + 1)).set(doc)
        success = "Everything went perfect!, We will contact you using your email address."
        return render_template("tutor.html", success=success)

        # # This is to verify files are supported
        # ext = pic.filename.strip().lower().split(".")[-1]
        # name = req["fname"] + req["lname"]
        # if ext in {'jpg', 'jpeg', 'png'}:

        #     print('File supported moving on...')
        #     # blob = pic.read()
        #     # size = len(blob)
        #     # print(size)
        #     # if size > 500000000000:
        #     #     warning = "File too large!"
        #     #     return render_template("tutor.html", warning=warning)
        #     # else:

        #     # temp = tempfile.NamedTemporaryFile(delete=False)
        #     pic.save(name)
        #     print(name)
        #     print(pic)
        #     # strj.child(f"images/{name}").put(name)
        #     # strj.child("images/yoni.jpg").download("/", "yoni.jpg")
        #     # print(url)
        #     # time.sleep(1000)
        #     os.remove(name)
        #     # picture.save(temp.name)
        # else:
        #     warning = "Unsupported image format!"
        #     return render_template("tutor.html", warning=warning)

    return render_template("tutor.html")


if __name__ == '__main__':
    app.run(debug=True)
