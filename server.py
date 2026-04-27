from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

def load_json(filename):
    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_user_data():
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'user_data.json')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    except:
        pass
    return {'started_at': None, 'lesson_visits': {}, 'practice_answers': {}, 'quiz_answers': {}}

def save_user_data(data):
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'user_data.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route('/')
def home():
    user_data = {'started_at': None, 'lesson_visits': {}, 'practice_answers': {}, 'quiz_answers': {}}
    save_user_data(user_data)
    return render_template('home.html')


@app.route('/start')
def start():
    user_data = get_user_data()
    user_data['started_at'] = datetime.now().isoformat()
    user_data['quiz_answers'] = {}
    save_user_data(user_data)
    return redirect(url_for('learn', lesson_num=1))


@app.route('/learn/<int:lesson_num>')
def learn(lesson_num):
    lessons = load_json('lessons.json')
    total_lessons = len(lessons)

    if lesson_num < 1 or lesson_num > total_lessons:
        return redirect(url_for('learn', lesson_num=1))

    lesson = lessons[lesson_num - 1]

    user_data = get_user_data()
    user_data['lesson_visits'][str(lesson_num)] = datetime.now().isoformat()
    save_user_data(user_data)

    return render_template('learn.html', lesson=lesson, lesson_num=lesson_num, total_lessons=total_lessons)


@app.route('/practice/<int:question_num>')
def practice(question_num):
    questions = load_json('practice.json')
    total = len(questions)

    if question_num < 1 or question_num > total:
        return redirect(url_for('practice', question_num=1))

    question = questions[question_num - 1]
    return render_template('practice.html', question=question, question_num=question_num, total=total)


@app.route('/practice/<int:question_num>/answer', methods=['POST'])
def practice_answer(question_num):
    questions = load_json('practice.json')
    question = questions[question_num - 1]

    selected = int(request.form.get('answer', -1))
    correct = question['correct']
    is_correct = selected == correct

    user_data = get_user_data()
    user_data['practice_answers'][str(question_num)] = {
        'selected': selected,
        'correct': correct,
        'is_correct': is_correct,
        'time': datetime.now().isoformat()
    }
    save_user_data(user_data)

    return render_template('practice.html', question=question, question_num=question_num,
                           total=len(questions), selected=selected, is_correct=is_correct, show_result=True)


@app.route('/quiz/<int:question_num>', methods=['GET', 'POST'])
def quiz(question_num):
    questions = load_json('quiz.json')
    total = len(questions)

    if question_num < 1 or question_num > total:
        return redirect(url_for('results'))

    q = questions[question_num - 1]
    user_data = get_user_data()
    answers = user_data.get('quiz_answers', {})

    if request.method == 'POST':
        answer = request.form.get('answer')
        showing_feedback = request.form.get('submitted') == '1'

        if not showing_feedback and answer is not None:
            try:
                is_correct = int(answer) == q['answer']
            except (TypeError, ValueError):
                is_correct = False

            answers[str(question_num)] = {
                'selected': answer,
                'is_correct': is_correct,
                'time': datetime.now().isoformat()
            }
            user_data['quiz_answers'] = answers
            save_user_data(user_data)

            return render_template('quiz.html', q=q, question_num=question_num, total=total,
                                   submitted_answer=answer, is_correct=is_correct, show_feedback=True)

        if question_num < total:
            return redirect(url_for('quiz', question_num=question_num + 1))
        return redirect(url_for('results'))

    previous = answers.get(str(question_num), {}).get('selected')
    return render_template('quiz.html', q=q, question_num=question_num, total=total,
                           submitted_answer=previous, is_correct=None, show_feedback=False)


@app.route('/resume')
def resume():
    questions = load_json('quiz.json')
    total = len(questions)
    user_data = get_user_data()
    answers = user_data.get('quiz_answers', {})

    if not answers:
        return redirect(url_for('quiz', question_num=1))

    for i in range(1, total + 1):
        if str(i) not in answers:
            return redirect(url_for('quiz', question_num=i))
    return redirect(url_for('results'))


@app.route('/results')
def results():
    questions = load_json('quiz.json')
    total = len(questions)
    user_data = get_user_data()
    answers = user_data.get('quiz_answers', {})

    if not answers:
        return redirect(url_for('home'))

    score = 0
    result_rows = []

    for q in questions:
        entry = answers.get(str(q['id']))

        if entry is None:
            result_rows.append({
                'question': q['question'],
                'explanation': q['explanation'],
                'is_correct': False,
                'skipped': True
            })
            continue

        correct = entry.get('is_correct', False)
        if correct:
            score += 1

        result_rows.append({
            'question': q['question'],
            'explanation': q['explanation'],
            'is_correct': correct,
            'skipped': False
        })

    return render_template('results.html', score=score, total=total,
                           answered=len(answers), results=result_rows)


if __name__ == '__main__':
    app.run(debug=True)
