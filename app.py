from flask import Flask, flash, redirect, render_template, request, session, abort, url_for

# Flask app setup
app = Flask(__name__)

# Firebase Pyrebase config (for auth only)z

Config = {
  "apiKey": "AIzaSyBdkeUCyJwP1Ip4M05kyxksMGs3T0e_Z0c",
  "authDomain": "finance-game-7c716.firebaseapp.com",
  "databaseURL": "https://finance-game-7c716-default-rtdb.firebaseio.com",
  "projectId": "finance-game-7c716",
  "storageBucket": "finance-game-7c716.firebasestorage.app",
  "messagingSenderId": "100856364080",
  "appId": "1:100856364080:web:be1ca42f5a035be29c41f5",
  "databaseURL": "https://finance-game-7c716-default-rtdb.firebaseio.com/",

}

# Homepage
@app.route("/")
def index():
    return render_template("front_page.html")

# Login page
@app.route("/login")
def login():
    return render_template("/login/index.html")

@app.route("/dashboard")
def dashboard():
    try:
        if session["loginSuccess"] is None:
            print("Session loginSuccess is None")
        else:
            return render_template("dashboard.html", user=session["loginSuccess"])
    except KeyError:
        print("KeyError: 'loginSuccess' not found in session")
        # return redirect(url_for("login"))
    return render_template("dashboard.html", user=None)    
# Run the Flask app
# if __name__ == "__main__":
#     app.run(debug=True)
