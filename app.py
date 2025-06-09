from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
# import openai
import json
# from google.generativeai import Model
import google.generativeai as genai
import re
# Flask app setup
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session

genai.configure(api_key="AIzaSyBjqSYnsr2Le7-QgX_eoATrrQ-Y9mGNS2U")
model = genai.GenerativeModel("gemini-1.5-flash")
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

def build_level1_prompt():
    return (
        "You are an educational game assistant for teenagers learning about finance. "
        "Teach a concept about money in a fun, simple way, then ask a multiple-choice question (MCQ) with 4 options about what you just taught. "
        "Today's topic is: 'What is money and why do we use it?'. "
        "Format your response as:\n"
        "Paragraph: <your paragraph>\n"
        "Question: <your question>\n"
        "Options:\nA) <option1>\nB) <option2>\nC) <option3>\nD) <option4>"
    )

@app.route("/level1", methods=["GET", "POST"])
def level1():
    if request.method == "GET" or "level1_paragraph" not in session:
        prompt = build_level1_prompt()
        response = model.generate_content(prompt)
        content = response.text

        # Parse the response
        paragraph_match = re.search(r'Paragraph:\s*(.*?)\s*Question:', content, re.DOTALL)
        question_match = re.search(r'Question:\s*(.*?)\s*Options:', content, re.DOTALL)
        options_match = re.findall(r'[A-D]\)\s*(.*)', content)

        paragraph = paragraph_match.group(1).strip() if paragraph_match else ""
        question = question_match.group(1).strip() if question_match else ""
        options = options_match if options_match else []

        # Store in session
        session['level1_paragraph'] = paragraph
        session['level1_question'] = question
        session['level1_options'] = options
        session['level1_correct'] = "B"  # You may want to parse this from the API or set manually

    paragraph = session.get('level1_paragraph', "")
    question = session.get('level1_question', "")
    options = session.get('level1_options', [])
    correct = session.get('level1_correct', "B")

    feedback = None

    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        # Find which option letter was chosen
        answer_letter = ""
        for idx, opt in enumerate(options):
            if opt == user_answer:
                answer_letter = chr(ord('A') + idx)
                break
        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."

    return render_template(
        "level1.html",
        paragraph=paragraph,
        question=question,
        options=options,
        feedback=feedback
    )
# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
