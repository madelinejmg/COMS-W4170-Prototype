from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Load data
def load_json(filename):
    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_user_data(data):
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'user_data.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Initialize or load user data
def get_user_data():
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'user_data.json')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    except:
        pass
    return {"started_at": None, "lesson_visits": {}, "practice_answers": {}, "quiz_answers": {}}


@app.route("/")
def home():
    # Reset user data on new session
    user_data = {"started_at": None, "lesson_visits": {}, "practice_answers": {}, "quiz_answers": {}}
    save_user_data(user_data)
    return render_template("home.html")


@app.route("/start")
def start():
    user_data = get_user_data()
    user_data["started_at"] = datetime.now().isoformat()
    save_user_data(user_data)
    return redirect(url_for('learn', lesson_num=1))


@app.route("/learn/<int:lesson_num>")
def learn(lesson_num):
    lessons = load_json('lessons.json')
    total_lessons = len(lessons)

    if lesson_num < 1 or lesson_num > total_lessons:
        return redirect(url_for('learn', lesson_num=1))

    lesson = lessons[lesson_num - 1]

    # Record visit time
    user_data = get_user_data()
    user_data["lesson_visits"][str(lesson_num)] = datetime.now().isoformat()
    save_user_data(user_data)

    return render_template("learn.html",
                           lesson=lesson,
                           lesson_num=lesson_num,
                           total_lessons=total_lessons)


@app.route("/practice/<int:question_num>")
def practice(question_num):
    questions = load_json('practice.json')
    total = len(questions)

    if question_num < 1 or question_num > total:
        return redirect(url_for('practice', question_num=1))

    question = questions[question_num - 1]

    return render_template("practice.html",
                           question=question,
                           question_num=question_num,
                           total=total)


@app.route("/practice/<int:question_num>/answer", methods=["POST"])
def practice_answer(question_num):
    questions = load_json('practice.json')
    question = questions[question_num - 1]

    selected = int(request.form.get("answer", -1))
    correct = question["correct"]
    is_correct = selected == correct

    # Store practice answer
    user_data = get_user_data()
    user_data["practice_answers"][str(question_num)] = {
        "selected": selected,
        "correct": correct,
        "is_correct": is_correct,
        "time": datetime.now().isoformat()
    }
    save_user_data(user_data)

    return render_template("practice.html",
                           question=question,
                           question_num=question_num,
                           total=len(questions),
                           selected=selected,
                           is_correct=is_correct,
                           show_result=True)


@app.route("/quiz/<int:question_num>")
def quiz(question_num):
    questions = load_json('quiz.json')
    total = len(questions)

    if question_num < 1 or question_num > total:
        return redirect(url_for('quiz', question_num=1))

    question = questions[question_num - 1]

    return render_template("quiz.html",
                           question=question,
                           question_num=question_num,
                           total=total)


@app.route("/quiz/<int:question_num>/answer", methods=["POST"])
def quiz_answer(question_num):
    questions = load_json('quiz.json')
    question = questions[question_num - 1]
    total = len(questions)

    selected = int(request.form.get("answer", -1))
    correct = question["correct"]
    is_correct = selected == correct

    # Store answer
    user_data = get_user_data()
    user_data["quiz_answers"][str(question_num)] = {
        "selected": selected,
        "correct": correct,
        "is_correct": is_correct,
        "time": datetime.now().isoformat()
    }
    save_user_data(user_data)

    return render_template("quiz.html",
                           question=question,
                           question_num=question_num,
                           total=total,
                           selected=selected,
                           is_correct=is_correct,
                           show_result=True)


@app.route("/results")
def results():
    user_data = get_user_data()
    quiz_answers = user_data.get("quiz_answers", {})
    questions = load_json('quiz.json')
    total = len(questions)
    correct_count = sum(1 for a in quiz_answers.values() if a.get("is_correct"))

    return render_template("results.html",
                           score=correct_count,
                           total=total,
                           answers=quiz_answers)


if __name__ == "__main__":
    app.run(debug=True)
