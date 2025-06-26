from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import json
import re
import random
from functools import wraps
import os
import firebase_admin
from firebase_admin import credentials, firestore
from openai import OpenAI
import time

# Initialize Firebase Admin
cred = credentials.Certificate("finance-game-7c716-firebase-adminsdk-fbsvc-61b53e3b0e.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Flask app setup
app = Flask(__name__)
# Set a secure secret key for session
app.secret_key = os.urandom(24)  # Generate a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

# Pre-defined questions for Level 1 (Money Basics)
LEVEL1_QUESTIONS = [
    {
        'paragraph': 'Money is a medium of exchange that people use to buy goods and services. It makes trading easier than bartering because everyone accepts it as payment.',
        'question': 'Why do we use money instead of bartering?',
        'options': [
            'Because it is made of precious metals',
            'Because it never loses value',
            'Because everyone accepts it as payment',
            'Because it is easier to carry than goods'
        ],
        'correct_option': 'C'
    },
    {
        'paragraph': 'Currency is the physical form of money that we use in our daily lives. Different countries have different currencies, like dollars, euros, or yen.',
        'question': 'What is currency?',
        'options': [
            'A type of bank account',
            'The physical form of money used in a country',
            'A way to invest money',
            'A type of credit card'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'The value of money can change over time due to inflation. This means that the same amount of money can buy fewer things in the future.',
        'question': 'What happens to the value of money during inflation?',
        'options': [
            'It decreases',
            'It increases',
            'It becomes worthless',
            'It stays the same'
        ],
        'correct_option': 'A'
    },
    {
        'paragraph': 'Banks keep our money safe and help us manage it. They also pay us interest when we save money with them.',
        'question': 'What is one main benefit of keeping money in a bank?',
        'options': [
            'Banks let you spend more than you have',
            'Banks give free gifts',
            'Banks pay interest on savings',
            'Banks give you free credit cards'
        ],
        'correct_option': 'C'
    },
    {
        'paragraph': 'Digital money, like online banking and mobile payments, makes it easier to send and receive money without using physical cash.',
        'question': 'What is an advantage of digital money?',
        'options': [
            'It is always free to use',
            'It is always physical',
            'It is easier to send and receive money',
            'It never needs internet'
        ],
        'correct_option': 'C'
    }
]

# Pre-defined questions for Level 2 (Saving and Budgeting)
LEVEL2_QUESTIONS = [
    {
        'paragraph': 'Saving money means setting aside some of your income for future use. It helps you prepare for emergencies and achieve your financial goals.',
        'question': 'What is the main benefit of saving money?',
        'options': [
            'To spend it all at once',
            'To prepare for emergencies and future goals',
            'To show off to friends',
            'To avoid paying taxes'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'A budget is a plan for how you will spend your money. It helps you track your income and expenses to make sure you don\'t spend more than you earn.',
        'question': 'What is the main purpose of a budget?',
        'options': [
            'To spend all your money quickly',
            'To plan and track your spending',
            'To avoid saving money',
            'To get more credit cards'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Emergency funds are savings set aside for unexpected expenses, like medical bills or car repairs. Experts recommend saving 3-6 months of expenses.',
        'question': 'How much should you save in an emergency fund?',
        'options': [
            '1 month of expenses',
            '3-6 months of expenses',
            '1 year of expenses',
            'No need to save for emergencies'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Needs are essential expenses you must pay for, like food and housing. Wants are things you would like to have but can live without.',
        'question': 'What is the difference between needs and wants?',
        'options': [
            'Needs are more expensive than wants',
            'Needs are essential, wants are optional',
            'Wants are more important than needs',
            'There is no difference'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Compound interest is when you earn interest on both your original savings and the interest you\'ve already earned. This helps your money grow faster over time.',
        'question': 'How does compound interest help your savings?',
        'options': [
            'It makes your money grow slower',
            'It helps your money grow faster over time',
            'It has no effect on your savings',
            'It only works for large amounts'
        ],
        'correct_option': 'B'
    }
]

# Pre-defined questions for Level 3 (Investing Basics)
LEVEL3_QUESTIONS = [
    {
        'paragraph': 'Investing is putting your money into something with the expectation of making a profit. Common investments include stocks, bonds, and mutual funds.',
        'question': 'What is the main purpose of investing?',
        'options': [
            'To spend money quickly',
            'To make a profit over time',
            'To avoid paying taxes',
            'To keep money safe'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Stocks represent ownership in a company. When you buy a stock, you become a shareholder and can benefit from the company\'s growth and profits.',
        'question': 'What does buying a stock mean?',
        'options': [
            'Lending money to a company',
            'Becoming a partial owner of a company',
            'Getting a guaranteed return',
            'Making a short-term loan'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Diversification means spreading your investments across different types of assets to reduce risk. It\'s like not putting all your eggs in one basket.',
        'question': 'Why is diversification important in investing?',
        'options': [
            'To make more money quickly',
            'To reduce risk by spreading investments',
            'To avoid paying taxes',
            'To invest in only the best companies'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Risk and return are related in investing. Generally, investments with higher potential returns also come with higher risks.',
        'question': 'What is the relationship between risk and return?',
        'options': [
            'Higher risk always means lower returns',
            'Higher risk usually means higher potential returns',
            'Risk and return are not related',
            'Lower risk always means higher returns'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Long-term investing means holding investments for many years. This strategy can help ride out market ups and downs and potentially earn better returns.',
        'question': 'What is an advantage of long-term investing?',
        'options': [
            'Getting rich quickly',
            'Riding out market ups and downs',
            'Avoiding all investment risks',
            'Making daily profits'
        ],
        'correct_option': 'B'
    }
]

# Pre-defined questions for Level 4 (Credit and Debt Management)
LEVEL4_QUESTIONS = [
    {
        'paragraph': 'Credit is the ability to borrow money or access goods and services with the understanding that you\'ll pay for them later. Good credit management is essential for financial health.',
        'question': 'What is credit?',
        'options': [
            'Money you have in the bank',
            'The ability to borrow money or access goods/services to pay later',
            'A type of investment',
            'A way to save money'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'A credit score is a number that represents your creditworthiness. It affects your ability to get loans and the interest rates you\'ll pay.',
        'question': 'What does a credit score indicate?',
        'options': [
            'How much money you have',
            'Your creditworthiness and ability to get loans',
            'Your monthly income',
            'Your savings account balance'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Interest is the cost of borrowing money. When you take out a loan, you pay back the original amount plus interest.',
        'question': 'What is interest on a loan?',
        'options': [
            'A gift from the bank',
            'The cost of borrowing money',
            'A type of savings',
            'A way to avoid paying back loans'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Debt management involves strategies to pay off debts efficiently. This includes making payments on time and paying more than the minimum when possible.',
        'question': 'What is an important part of debt management?',
        'options': [
            'Taking on more debt',
            'Making payments on time and paying more than minimum',
            'Ignoring payment due dates',
            'Borrowing more to pay off existing debt'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Credit cards can be useful financial tools when used responsibly. They offer convenience and can help build credit, but high interest rates can lead to debt if not managed properly.',
        'question': 'What is a key to using credit cards responsibly?',
        'options': [
            'Maxing out the credit limit',
            'Paying the full balance on time each month',
            'Making only minimum payments',
            'Using multiple cards at once'
        ],
        'correct_option': 'B'
    }
]

# Pre-defined questions for Level 5 (Financial Planning and Goals)
LEVEL5_QUESTIONS = [
    {
        'paragraph': 'Financial planning is the process of setting goals and creating a strategy to achieve them. It involves managing your income, expenses, savings, and investments.',
        'question': 'What is the main purpose of financial planning?',
        'options': [
            'To spend all your money',
            'To set and achieve financial goals',
            'To avoid paying taxes',
            'To get rich quickly'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Short-term goals are financial objectives you want to achieve within a year, like saving for a vacation or building an emergency fund.',
        'question': 'What is a characteristic of short-term financial goals?',
        'options': [
            'They take many years to achieve',
            'They can be achieved within a year',
            'They require no planning',
            'They are always expensive'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Long-term goals are financial objectives that take several years to achieve, such as saving for retirement or buying a house.',
        'question': 'What is an example of a long-term financial goal?',
        'options': [
            'Buying lunch today',
            'Saving for retirement',
            'Paying monthly bills',
            'Buying a new phone'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'A financial plan should be flexible and adaptable to changes in your life circumstances, income, and goals.',
        'question': 'Why should a financial plan be flexible?',
        'options': [
            'To avoid making any decisions',
            'To adapt to life changes and circumstances',
            'To spend money freely',
            'To ignore financial goals'
        ],
        'correct_option': 'B'
    },
    {
        'paragraph': 'Setting SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound) helps you create clear and realistic financial objectives.',
        'question': 'What does the "M" in SMART goals stand for?',
        'options': [
            'Money',
            'Measurable',
            'Maximum',
            'Minimum'
        ],
        'correct_option': 'B'
    }
]

# Homepage
@app.route("/")
def index():
    return render_template("front_page.html")

# Login page
@app.route("/login")
def login():
    return render_template("/login/index.html")

# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not session.get("loginSuccess"):
#             return redirect(url_for("login"))
#         return f(*args, **kwargs)
#     return decorated_function

@app.route("/dashboard")
# @login_required
def dashboard():
    # Get level1 score from session (for backward compatibility)
    level1_score = session.get("level1_final_score", 0)
    return render_template("dashboard.html", level1_score=level1_score)

def generate_questions():
    # Return a random selection of 5 questions from the pre-defined set
    return random.sample(LEVEL1_QUESTIONS, 5)

@app.route("/level1", methods=["GET", "POST"])
def level1():
    total_questions = 5
    marks_per_question = 5

    # Initialize session variables if not set
    if "level1_questions" not in session or request.method == "GET":
        print("Generating new questions...")  # Debug print
        questions = generate_questions()
        session["level1_questions"] = questions
        session["level1_current_question"] = 0
        session["level1_score"] = 0
        session.modified = True  # Ensure session is saved
        print(f"Session after initialization: {session}")  # Debug print

    current_question = session["level1_current_question"]
    score = session["level1_score"]
    questions = session["level1_questions"]
    feedback = None

    print(f"Current session state: {session}")  # Debug print

    # On POST, check the answer
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        if not questions or current_question >= len(questions):
            # If questions are missing, regenerate them
            questions = generate_questions()
            session["level1_questions"] = questions
            session["level1_current_question"] = 0
            session["level1_score"] = 0
            session.modified = True
            return redirect(url_for("level1"))

        current_q = questions[current_question]
        options = current_q['options']
        correct = current_q['correct_option']
        
        # Find which option letter was chosen
        answer_letter = ""
        for idx, opt in enumerate(options):
            if opt == user_answer:
                answer_letter = chr(ord('A') + idx)
                break

        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
            score += marks_per_question
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."
        
        session["level1_score"] = score
        current_question += 1
        session["level1_current_question"] = current_question
        session.modified = True  # Ensure session is saved

    # If finished all questions, show final score and feedback
    if current_question >= total_questions:
        final_score = session["level1_score"]
        session["level1_final_score"] = final_score

        # Generate AI feedback
        feedback = generate_ai_feedback(1, final_score, total_questions * marks_per_question)
        session["level1_feedback"] = feedback

        # Update score in Firebase
        player_id = session.get("playerId")
        if player_id:
            try:
                user_ref = db.collection("users").document(player_id)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    current_high_score = user_doc.to_dict().get("hightScore", {}).get("level1", 0)
                    
                    if final_score > current_high_score:
                        user_ref.update({
                            "hightScore.level1": final_score
                        })
                        print(f"Updated level 1 score in Firebase for user {player_id}: {final_score}")
                    else:
                        print(f"Current score {final_score} not higher than high score {current_high_score}")
                else:
                    print(f"User document not found for player_id: {player_id}")
            except Exception as e:
                print(f"Error updating Firebase score: {str(e)}")
        else:
            print("No player_id found in session")

        # Clear level1 session data
        session.pop("level1_questions", None)
        session.pop("level1_current_question", None)
        session.pop("level1_score", None)
        session.modified = True
        
        return render_template(
            "level1.html",
            is_complete=True,
            final_score=final_score,
            total_questions=total_questions,
            feedback=feedback
        )

    # Get current question data
    if not questions or current_question >= len(questions):
        # If questions are missing or invalid, regenerate them
        questions = generate_questions()
        session["level1_questions"] = questions
        session["level1_current_question"] = 0
        session["level1_score"] = 0
        session.modified = True
        return redirect(url_for("level1"))

    current_q = questions[current_question]
    return render_template(
        "level1.html",
        paragraph=f"Question {current_question + 1} of {total_questions}:<br><br>{current_q['paragraph']}",
        question=current_q['question'],
        options=current_q['options'],
        feedback=feedback,
        total_questions=total_questions,
        current_score=score  # Pass current score to template
    )

def generate_level2_questions():
    # Return a random selection of 5 questions from the pre-defined set
    return random.sample(LEVEL2_QUESTIONS, 5)

@app.route("/level2", methods=["GET", "POST"])
def level2():
    total_questions = 5
    marks_per_question = 5

    # Initialize session variables if not set
    if "level2_questions" not in session or request.method == "GET":
        print("Generating new questions for level 2...")  # Debug print
        questions = generate_level2_questions()
        session["level2_questions"] = questions
        session["level2_current_question"] = 0
        session["level2_score"] = 0
        session.modified = True  # Ensure session is saved
        print(f"Session after initialization: {session}")  # Debug print

    current_question = session["level2_current_question"]
    score = session["level2_score"]
    questions = session["level2_questions"]
    feedback = None

    print(f"Current session state: {session}")  # Debug print

    # On POST, check the answer
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        if not questions or current_question >= len(questions):
            # If questions are missing, regenerate them
            questions = generate_level2_questions()
            session["level2_questions"] = questions
            session["level2_current_question"] = 0
            session["level2_score"] = 0
            session.modified = True
            return redirect(url_for("level2"))

        current_q = questions[current_question]
        options = current_q['options']
        correct = current_q['correct_option']
        
        # Find which option letter was chosen
        answer_letter = ""
        for idx, opt in enumerate(options):
            if opt == user_answer:
                answer_letter = chr(ord('A') + idx)
                break

        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
            score += marks_per_question
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."
        
        session["level2_score"] = score
        current_question += 1
        session["level2_current_question"] = current_question
        session.modified = True  # Ensure session is saved

    # If finished all questions, show final score and feedback
    if current_question >= total_questions:
        final_score = session["level2_score"]
        session["level2_final_score"] = final_score

        # Generate AI feedback
        feedback = generate_ai_feedback(2, final_score, total_questions * marks_per_question)
        session["level2_feedback"] = feedback

        # Update score in Firebase
        player_id = session.get("playerId")
        if player_id:
            try:
                user_ref = db.collection("users").document(player_id)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    current_high_score = user_doc.to_dict().get("hightScore", {}).get("level2", 0)
                    
                    if final_score > current_high_score:
                        user_ref.update({
                            "hightScore.level2": final_score
                        })
                        print(f"Updated level 2 score in Firebase for user {player_id}: {final_score}")
                    else:
                        print(f"Current score {final_score} not higher than high score {current_high_score}")
                else:
                    print(f"User document not found for player_id: {player_id}")
            except Exception as e:
                print(f"Error updating Firebase score: {str(e)}")
        else:
            print("No player_id found in session")

        # Clear level2 session data
        session.pop("level2_questions", None)
        session.pop("level2_current_question", None)
        session.pop("level2_score", None)
        session.modified = True
        
        return render_template(
            "level2.html",
            is_complete=True,
            final_score=final_score,
            total_questions=total_questions,
            feedback=feedback
        )

    # Get current question data
    if not questions or current_question >= len(questions):
        # If questions are missing or invalid, regenerate them
        questions = generate_level2_questions()
        session["level2_questions"] = questions
        session["level2_current_question"] = 0
        session["level2_score"] = 0
        session.modified = True
        return redirect(url_for("level2"))

    current_q = questions[current_question]
    return render_template(
        "level2.html",
        paragraph=f"Question {current_question + 1} of {total_questions}:<br><br>{current_q['paragraph']}",
        question=current_q['question'],
        options=current_q['options'],
        feedback=feedback,
        total_questions=total_questions,
        current_score=score  # Pass current score to template
    )

def generate_level3_questions():
    # Return a random selection of 5 questions from the pre-defined set
    return random.sample(LEVEL3_QUESTIONS, 5)

@app.route("/level3", methods=["GET", "POST"])
def level3():
    total_questions = 5
    marks_per_question = 5

    # Initialize session variables if not set
    if "level3_questions" not in session or request.method == "GET":
        print("Generating new questions for level 3...")  # Debug print
        questions = generate_level3_questions()
        session["level3_questions"] = questions
        session["level3_current_question"] = 0
        session["level3_score"] = 0
        session.modified = True  # Ensure session is saved
        print(f"Session after initialization: {session}")  # Debug print

    current_question = session["level3_current_question"]
    score = session["level3_score"]
    questions = session["level3_questions"]
    feedback = None

    print(f"Current session state: {session}")  # Debug print

    # On POST, check the answer
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        if not questions or current_question >= len(questions):
            # If questions are missing, regenerate them
            questions = generate_level3_questions()
            session["level3_questions"] = questions
            session["level3_current_question"] = 0
            session["level3_score"] = 0
            session.modified = True
            return redirect(url_for("level3"))

        current_q = questions[current_question]
        options = current_q['options']
        correct = current_q['correct_option']
        
        # Find which option letter was chosen
        answer_letter = ""
        for idx, opt in enumerate(options):
            if opt == user_answer:
                answer_letter = chr(ord('A') + idx)
                break

        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
            score += marks_per_question
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."
        
        session["level3_score"] = score
        current_question += 1
        session["level3_current_question"] = current_question
        session.modified = True  # Ensure session is saved

    # If finished all questions, show final score and feedback
    if current_question >= total_questions:
        final_score = session["level3_score"]
        session["level3_final_score"] = final_score

        # Generate AI feedback
        feedback = generate_ai_feedback(3, final_score, total_questions * marks_per_question)
        session["level3_feedback"] = feedback

        # Clear level3 session data
        session.pop("level3_questions", None)
        session.pop("level3_current_question", None)
        session.pop("level3_score", None)
        session.modified = True
        
        return render_template(
            "level3.html",
            is_complete=True,
            final_score=final_score,
            total_questions=total_questions,
            feedback=feedback
        )

    # Get current question data
    if not questions or current_question >= len(questions):
        # If questions are missing or invalid, regenerate them
        questions = generate_level3_questions()
        session["level3_questions"] = questions
        session["level3_current_question"] = 0
        session["level3_score"] = 0
        session.modified = True
        return redirect(url_for("level3"))

    current_q = questions[current_question]
    return render_template(
        "level3.html",
        paragraph=f"Question {current_question + 1} of {total_questions}:<br><br>{current_q['paragraph']}",
        question=current_q['question'],
        options=current_q['options'],
        feedback=feedback,
        total_questions=total_questions,
        current_score=score  # Pass current score to template
    )

def generate_level4_questions():
    # Return a random selection of 5 questions from the pre-defined set
    return random.sample(LEVEL4_QUESTIONS, 5)

@app.route("/level4", methods=["GET", "POST"])
def level4():
    total_questions = 5
    marks_per_question = 5

    # Initialize session variables if not set
    if "level4_questions" not in session or request.method == "GET":
        print("Generating new questions for level 4...")  # Debug print
        questions = generate_level4_questions()
        session["level4_questions"] = questions
        session["level4_current_question"] = 0
        session["level4_score"] = 0
        session.modified = True  # Ensure session is saved
        print(f"Session after initialization: {session}")  # Debug print

    current_question = session["level4_current_question"]
    score = session["level4_score"]
    questions = session["level4_questions"]
    feedback = None

    print(f"Current session state: {session}")  # Debug print

    # On POST, check the answer
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        if not questions or current_question >= len(questions):
            # If questions are missing, regenerate them
            questions = generate_level4_questions()
            session["level4_questions"] = questions
            session["level4_current_question"] = 0
            session["level4_score"] = 0
            session.modified = True
            return redirect(url_for("level4"))

        current_q = questions[current_question]
        options = current_q['options']
        correct = current_q['correct_option']
        
        # Find which option letter was chosen
        answer_letter = ""
        for idx, opt in enumerate(options):
            if opt == user_answer:
                answer_letter = chr(ord('A') + idx)
                break

        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
            score += marks_per_question
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."
        
        session["level4_score"] = score
        current_question += 1
        session["level4_current_question"] = current_question
        session.modified = True  # Ensure session is saved

    # If finished all questions, show final score and feedback
    if current_question >= total_questions:
        final_score = session["level4_score"]
        session["level4_final_score"] = final_score

        # Generate AI feedback
        feedback = generate_ai_feedback(4, final_score, total_questions * marks_per_question)
        session["level4_feedback"] = feedback

        # Clear level4 session data
        session.pop("level4_questions", None)
        session.pop("level4_current_question", None)
        session.pop("level4_score", None)
        session.modified = True
        
        return render_template(
            "level4.html",
            is_complete=True,
            final_score=final_score,
            total_questions=total_questions,
            feedback=feedback
        )

    # Get current question data
    if not questions or current_question >= len(questions):
        # If questions are missing or invalid, regenerate them
        questions = generate_level4_questions()
        session["level4_questions"] = questions
        session["level4_current_question"] = 0
        session["level4_score"] = 0
        session.modified = True
        return redirect(url_for("level4"))

    current_q = questions[current_question]
    return render_template(
        "level4.html",
        paragraph=f"Question {current_question + 1} of {total_questions}:<br><br>{current_q['paragraph']}",
        question=current_q['question'],
        options=current_q['options'],
        feedback=feedback,
        total_questions=total_questions,
        current_score=score  # Pass current score to template
    )

def generate_level5_questions():
    try:
        # Initialize OpenAI client with OpenRouter configuration
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="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"
        )

        # Create the prompt for generating questions
        prompt = """Generate 5 multiple-choice questions about financial planning and goals for a finance education game. Each question should include:
1. A paragraph explaining the concept
2. A question about the concept
3. Four options (A, B, C, D) where B is always the correct answer
4. The correct option marked as 'B'

Format each question as a JSON object with these fields:
- paragraph: The educational paragraph
- question: The multiple-choice question
- options: Array of 4 options
- correct_option: 'B'

Make the questions educational and engaging, covering topics like:
- Financial planning basics
- Short-term and long-term goals
- SMART goals
- Financial flexibility
- Goal setting strategies

Return only the JSON array of questions."""

        # Make the API call
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-8b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a financial education expert creating quiz questions."},
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the response
        questions_text = response.choices[0].message.content
        # Extract the JSON array from the response
        questions_json = questions_text[questions_text.find('['):questions_text.rfind(']')+1]
        questions = json.loads(questions_json)

        # Add a small delay to avoid rate limits
        time.sleep(1)

        return questions

    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        # Return pre-defined questions as fallback
        return random.sample(LEVEL5_QUESTIONS, 5)

@app.route("/level5", methods=["GET", "POST"])
def level5():
    total_questions = 5
    marks_per_question = 5

    # Initialize session variables if not set
    if "level5_questions" not in session or request.method == "GET":
        print("Generating new questions for level 5...")  # Debug print
        questions = generate_level5_questions()
        session["level5_questions"] = questions
        session["level5_current_question"] = 0
        session["level5_score"] = 0
        session.modified = True  # Ensure session is saved
        print(f"Session after initialization: {session}")  # Debug print

    current_question = session["level5_current_question"]
    score = session["level5_score"]
    questions = session["level5_questions"]
    feedback = None

    print(f"Current session state: {session}")  # Debug print

    # On POST, check the answer
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        if not questions or current_question >= len(questions):
            # If questions are missing, regenerate them
            questions = generate_level5_questions()
            session["level5_questions"] = questions
            session["level5_current_question"] = 0
            session["level5_score"] = 0
            session.modified = True
            return redirect(url_for("level5"))

        current_q = questions[current_question]
        options = current_q['options']
        correct = current_q['correct_option']
        
        # Find which option letter was chosen
        answer_letter = ""
        for idx, opt in enumerate(options):
            if opt == user_answer:
                answer_letter = chr(ord('A') + idx)
                break

        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
            score += marks_per_question
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."
        
        session["level5_score"] = score
        current_question += 1
        session["level5_current_question"] = current_question
        session.modified = True  # Ensure session is saved

    # If finished all questions, show final score and feedback
    if current_question >= total_questions:
        final_score = session["level5_score"]
        session["level5_final_score"] = final_score

        # Generate AI feedback
        feedback = generate_ai_feedback(5, final_score, total_questions * marks_per_question)
        session["level5_feedback"] = feedback

        # Clear level5 session data
        session.pop("level5_questions", None)
        session.pop("level5_current_question", None)
        session.pop("level5_score", None)
        session.modified = True
        
        return render_template(
            "level5.html",
            is_complete=True,
            final_score=final_score,
            total_questions=total_questions,
            feedback=feedback
        )

    # Get current question data
    if not questions or current_question >= len(questions):
        # If questions are missing or invalid, regenerate them
        questions = generate_level5_questions()
        session["level5_questions"] = questions
        session["level5_current_question"] = 0
        session["level5_score"] = 0
        session.modified = True
        return redirect(url_for("level5"))

    current_q = questions[current_question]
    return render_template(
        "level5.html",
        paragraph=f"Question {current_question + 1} of {total_questions}:<br><br>{current_q['paragraph']}",
        question=current_q['question'],
        options=current_q['options'],
        feedback=feedback,
        total_questions=total_questions,
        current_score=score  # Pass current score to template
    )

def generate_ai_feedback(level, score, total_score):
    try:
        # Initialize OpenAI client with OpenRouter configuration
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="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"
        )

        # Create the prompt for generating feedback
        prompt = f"""Generate personalized feedback for a student who completed Level {level} of a finance education game.
Score: {score} out of {total_score}
Level {level} topics:
{{
    '1': 'Introduction to Money',
    '2': 'Saving Money and Budgeting',
    '3': 'Investing Basics',
    '4': 'Credit and Debt Management',
    '5': 'Financial Planning and Goals'
}}[str({level})]

Generate a JSON object with:
1. A congratulatory message
2. Specific feedback based on their score
3. Areas of strength
4. Areas for improvement
5. Encouraging next steps

Format the response as a JSON object with these fields:
- congratulation: A brief congratulatory message
- score_feedback: Feedback specific to their score
- strengths: Array of 2-3 strengths
- improvements: Array of 2-3 areas to improve
- next_steps: Array of 2-3 encouraging next steps

Return only the JSON object."""

        # Make the API call
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-8b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a supportive and encouraging financial education expert providing personalized feedback."},
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the response
        feedback_text = response.choices[0].message.content
        # Extract the JSON object from the response
        feedback_json = feedback_text[feedback_text.find('{'):feedback_text.rfind('}')+1]
        feedback = json.loads(feedback_json)

        # Add a small delay to avoid rate limits
        time.sleep(5)

        return feedback

    except Exception as e:
        print(f"Error generating feedback: {str(e)}")
        # Return default feedback as fallback
        return {
            "congratulation": "Congratulations on completing the level!",
            "score_feedback": f"You scored {score} out of {total_score}.",
            "strengths": ["Your dedication to learning", "Your progress in the game"],
            "improvements": ["Keep practicing", "Review the concepts"],
            "next_steps": ["Try the next level", "Review your answers"]
        }

# Run the Flask app
# if __name__ == "__main__":
#     app.run(debug=True)