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

LEVEL_QUESTIONS = {
    1: lambda: random.sample([
        {'paragraph': 'Money is a medium of exchange that people use to buy goods and services. It makes trading easier than bartering because everyone accepts it as payment.', 'question': 'Why do we use money instead of bartering?', 'options': ['Because it is made of precious metals', 'Because it never loses value', 'Because everyone accepts it as payment', 'Because it is easier to carry than goods'], 'correct_option': 'C'},
        {'paragraph': 'Currency is the physical form of money that we use in our daily lives. Different countries have different currencies, like dollars, euros, or yen.', 'question': 'What is currency?', 'options': ['A type of bank account', 'The physical form of money used in a country', 'A way to invest money', 'A type of credit card'], 'correct_option': 'B'},
        {'paragraph': 'The value of money can change over time due to inflation. This means that the same amount of money can buy fewer things in the future.', 'question': 'What happens to the value of money during inflation?', 'options': ['It decreases', 'It increases', 'It becomes worthless', 'It stays the same'], 'correct_option': 'A'},
        {'paragraph': 'Banks keep our money safe and help us manage it. They also pay us interest when we save money with them.', 'question': 'What is one main benefit of keeping money in a bank?', 'options': ['Banks let you spend more than you have', 'Banks give free gifts', 'Banks pay interest on savings', 'Banks give you free credit cards'], 'correct_option': 'C'},
        {'paragraph': 'Digital money, like online banking and mobile payments, makes it easier to send and receive money without using physical cash.', 'question': 'What is an advantage of digital money?', 'options': ['It is always free to use', 'It is always physical', 'It is easier to send and receive money', 'It never needs internet'], 'correct_option': 'C'}
    ], 5),
    2: lambda: random.sample([
        {'paragraph': 'Saving money means setting aside some of your income for future use. It helps you prepare for emergencies and achieve your financial goals.', 'question': 'What is the main benefit of saving money?', 'options': ['To spend it all at once', 'To prepare for emergencies and future goals', 'To show off to friends', 'To avoid paying taxes'], 'correct_option': 'B'},
        {'paragraph': 'A budget is a plan for how you will spend your money. It helps you track your income and expenses to make sure you don\'t spend more than you earn.', 'question': 'What is the main purpose of a budget?', 'options': ['To spend all your money quickly', 'To plan and track your spending', 'To avoid saving money', 'To get more credit cards'], 'correct_option': 'B'},
        {'paragraph': 'Emergency funds are savings set aside for unexpected expenses, like medical bills or car repairs. Experts recommend saving 3-6 months of expenses.', 'question': 'How much should you save in an emergency fund?', 'options': ['1 month of expenses', '3-6 months of expenses', '1 year of expenses', 'No need to save for emergencies'], 'correct_option': 'B'},
        {'paragraph': 'Needs are essential expenses you must pay for, like food and housing. Wants are things you would like to have but can live without.', 'question': 'What is the difference between needs and wants?', 'options': ['Needs are more expensive than wants', 'Needs are essential, wants are optional', 'Wants are more important than needs', 'There is no difference'], 'correct_option': 'B'},
        {'paragraph': 'Compound interest is when you earn interest on both your original savings and the interest you\'ve already earned. This helps your money grow faster over time.', 'question': 'How does compound interest help your savings?', 'options': ['It makes your money grow slower', 'It helps your money grow faster over time', 'It has no effect on your savings', 'It only works for large amounts'], 'correct_option': 'B'}
    ], 5),
    3: lambda: random.sample([
        {'paragraph': 'Investing is putting your money into something with the expectation of making a profit. Common investments include stocks, bonds, and mutual funds.', 'question': 'What is the main purpose of investing?', 'options': ['To spend money quickly', 'To make a profit over time', 'To avoid paying taxes', 'To keep money safe'], 'correct_option': 'B'},
        {'paragraph': 'Stocks represent ownership in a company. When you buy a stock, you become a shareholder and can benefit from the company\'s growth and profits.', 'question': 'What does buying a stock mean?', 'options': ['Lending money to a company', 'Becoming a partial owner of a company', 'Getting a guaranteed return', 'Making a short-term loan'], 'correct_option': 'B'},
        {'paragraph': 'Diversification means spreading your investments across different types of assets to reduce risk. It\'s like not putting all your eggs in one basket.', 'question': 'Why is diversification important in investing?', 'options': ['To make more money quickly', 'To reduce risk by spreading investments', 'To avoid paying taxes', 'To invest in only the best companies'], 'correct_option': 'B'},
        {'paragraph': 'Risk and return are related in investing. Generally, investments with higher potential returns also come with higher risks.', 'question': 'What is the relationship between risk and return?', 'options': ['Higher risk always means lower returns', 'Higher risk usually means higher potential returns', 'Risk and return are not related', 'Lower risk always means higher returns'], 'correct_option': 'B'},
        {'paragraph': 'Long-term investing means holding investments for many years. This strategy can help ride out market ups and downs and potentially earn better returns.', 'question': 'What is an advantage of long-term investing?', 'options': ['Getting rich quickly', 'Riding out market ups and downs', 'Avoiding all investment risks', 'Making daily profits'], 'correct_option': 'B'}
    ], 5),
    4: lambda: random.sample([
        {'paragraph': 'Credit is the ability to borrow money or access goods and services with the understanding that you\'ll pay for them later. Good credit management is essential for financial health.', 'question': 'What is credit?', 'options': ['Money you have in the bank', 'The ability to borrow money or access goods/services to pay later', 'A type of investment', 'A way to save money'], 'correct_option': 'B'},
        {'paragraph': 'A credit score is a number that represents your creditworthiness. It affects your ability to get loans and the interest rates you\'ll pay.', 'question': 'What does a credit score indicate?', 'options': ['How much money you have', 'Your creditworthiness and ability to get loans', 'Your monthly income', 'Your savings account balance'], 'correct_option': 'B'},
        {'paragraph': 'Interest is the cost of borrowing money. When you take out a loan, you pay back the original amount plus interest.', 'question': 'What is interest on a loan?', 'options': ['A gift from the bank', 'The cost of borrowing money', 'A type of savings', 'A way to avoid paying back loans'], 'correct_option': 'B'},
        {'paragraph': 'Debt management involves strategies to pay off debts efficiently. This includes making payments on time and paying more than the minimum when possible.', 'question': 'What is an important part of debt management?', 'options': ['Taking on more debt', 'Making payments on time and paying more than minimum', 'Ignoring payment due dates', 'Borrowing more to pay off existing debt'], 'correct_option': 'B'},
        {'paragraph': 'Credit cards can be useful financial tools when used responsibly. They offer convenience and can help build credit, but high interest rates can lead to debt if not managed properly.', 'question': 'What is a key to using credit cards responsibly?', 'options': ['Maxing out the credit limit', 'Paying the full balance on time each month', 'Making only minimum payments', 'Using multiple cards at once'], 'correct_option': 'B'}
    ], 5),
    5: lambda: generate_level5_questions()
}

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

def generate_level5_questions():
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key="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")
        prompt = """Generate 5 multiple-choice questions about financial planning and goals for a finance education game. Each question should include:\n1. A paragraph explaining the concept\n2. A question about the concept\n3. Four options (A, B, C, D) where B is always the correct answer\n4. The correct option marked as 'B'\nFormat each question as a JSON object with these fields:\n- paragraph: The educational paragraph\n- question: The multiple-choice question\n- options: Array of 4 options\n- correct_option: 'B'\nMake the questions educational and engaging, covering topics like:\n- Financial planning basics\n- Short-term and long-term goals\n- SMART goals\n- Financial flexibility\n- Goal setting strategies\nReturn only the JSON array of questions."""
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-8b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a financial education expert creating quiz questions."},
                {"role": "user", "content": prompt}
            ]
        )
        questions_text = getattr(response.choices[0].message, 'content', None)
        if not questions_text:
            raise Exception("No content in OpenAI response")
        questions_json = questions_text[questions_text.find('['):questions_text.rfind(']')+1]
        questions = json.loads(questions_json)
        time.sleep(1)
        return questions
    except Exception:
        return LEVEL_QUESTIONS[5].__defaults__[0] if hasattr(LEVEL_QUESTIONS[5], '__defaults__') else []

def generate_ai_feedback(level, score, total_score):
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key="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")
        prompt = f"""Generate personalized feedback for a student who completed Level {level} of a finance education game.\nScore: {score} out of {total_score}\nLevel {level} topics:\n{{'1': 'Introduction to Money','2': 'Saving Money and Budgeting','3': 'Investing Basics','4': 'Credit and Debt Management','5': 'Financial Planning and Goals'}}[str({level})]\nGenerate a JSON object with:\n- congratulation\n- score_feedback\n- strengths\n- improvements\n- next_steps\nReturn only the JSON object."""
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-8b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a supportive and encouraging financial education expert providing personalized feedback."},
                {"role": "user", "content": prompt}
            ]
        )
        feedback_text = getattr(response.choices[0].message, 'content', None)
        if not feedback_text:
            raise Exception("No content in OpenAI response")
        feedback_json = feedback_text[feedback_text.find('{'):feedback_text.rfind('}')+1]
        feedback = json.loads(feedback_json)
        time.sleep(1)
        return feedback
    except Exception:
        return {"congratulation": "Congratulations on completing the level!","score_feedback": f"You scored {score} out of {total_score}.","strengths": ["Your dedication to learning", "Your progress in the game"],"improvements": ["Keep practicing", "Review the concepts"],"next_steps": ["Try the next level", "Review your answers"]}

def update_firebase_score(level, final_score):
    player_id = session.get("playerId")
    if not player_id: return
    try:
        user_ref = db.collection("users").document(player_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            current_high_score = user_doc.to_dict().get("hightScore", {}).get(f"level{level}", 0)
            if final_score > current_high_score:
                user_ref.update({f"hightScore.level{level}": final_score})
    except Exception:
        pass

def get_level_session_keys(level):
    return {
        'questions': f'level{level}_questions',
        'current_question': f'level{level}_current_question',
        'score': f'level{level}_score',
        'final_score': f'level{level}_final_score',
        'feedback': f'level{level}_feedback'
    }

@app.route("/level<int:level>", methods=["GET", "POST"])
def level_route(level):
    if level not in LEVEL_QUESTIONS: return abort(404)
    total_questions, marks_per_question = 5, 5
    keys = get_level_session_keys(level)
    if keys['questions'] not in session or request.method == "GET":
        session[keys['questions']] = LEVEL_QUESTIONS[level]()
        session[keys['current_question']] = 0
        session[keys['score']] = 0
        session.modified = True
    current_question = session[keys['current_question']]
    score = session[keys['score']]
    questions = session[keys['questions']]
    feedback = None
    if request.method == "POST":
        user_answer = request.form.get("answer", "")
        if not questions or current_question >= len(questions):
            session[keys['questions']] = LEVEL_QUESTIONS[level]()
            session[keys['current_question']] = 0
            session[keys['score']] = 0
            session.modified = True
            return redirect(url_for("level_route", level=level))
        current_q = questions[current_question]
        options = current_q['options']
        correct = current_q['correct_option']
        answer_letter = next((chr(ord('A')+i) for i, opt in enumerate(options) if opt == user_answer), "")
        if answer_letter == correct:
            feedback = "✅ Correct! Great job!"
            score += marks_per_question
        else:
            feedback = f"❌ Incorrect. The correct answer was option {correct}."
        session[keys['score']] = score
        current_question += 1
        session[keys['current_question']] = current_question
        session.modified = True
    if current_question >= total_questions:
        final_score = session[keys['score']]
        session[keys['final_score']] = final_score
        feedback = generate_ai_feedback(level, final_score, total_questions * marks_per_question)
        session[keys['feedback']] = feedback
        update_firebase_score(level, final_score)
        for k in ['questions', 'current_question', 'score']:
            session.pop(keys[k], None)
        session.modified = True
        return render_template(f"level{level}.html", is_complete=True, final_score=final_score, total_questions=total_questions, feedback=feedback)
    if not questions or current_question >= len(questions):
        session[keys['questions']] = LEVEL_QUESTIONS[level]()
        session[keys['current_question']] = 0
        session[keys['score']] = 0
        session.modified = True
        return redirect(url_for("level_route", level=level))
    current_q = questions[current_question]
    return render_template(f"level{level}.html", paragraph=f"Question {current_question+1} of {total_questions}:<br><br>{current_q['paragraph']}", question=current_q['question'], options=current_q['options'], feedback=feedback, total_questions=total_questions, current_score=score)

# Run the Flask app
# if __name__ == "__main__":
#     app.run(debug=True)