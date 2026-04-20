from flask import Flask, render_template, session, redirect, url_for, request
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mahjong-secret-key'

with open('data/quiz.json') as f:
    questions = json.load(f)

total = len(questions)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/start')
def start():
    session.clear() # clear last record
    session['started_at'] = datetime.now().isoformat() # start time
    session['answers'] = {}
    return redirect(url_for('quiz', question_num=1))


@app.route('/resume')
def resume():
    answers = session.get('answers', {})
    if not answers:
        return redirect(url_for('start'))
    for i in range(1, total + 1):
        if str(i) not in answers:
            return redirect(url_for('quiz', question_num=i))
    return redirect(url_for('results'))


@app.route('/learn/<int:lesson_num>')
def learn(lesson_num):
    return render_template('learn.html', lesson_num=lesson_num)


@app.route('/quiz/<int:question_num>', methods=['GET', 'POST'])
def quiz(question_num):
    if question_num < 1 or question_num > total:
        return redirect(url_for('results'))

    q = questions[question_num - 1]
    answers = session.get('answers', {})

    if request.method == 'POST':
        answer = request.form.get('answer')
        showing_feedback = request.form.get('submitted') == '1'

        if not showing_feedback and answer is not None:
            answers[str(question_num)] = answer
            session['answers'] = answers
            session.modified = True

            try:
                is_correct = int(answer) == q['answer']
            except (TypeError, ValueError):
                is_correct = False

            return render_template('quiz.html',
                q=q,
                question_num=question_num,
                total=total,
                submitted_answer=answer,
                is_correct=is_correct,
                show_feedback=True
            )

        next_page = question_num + 1 if question_num < total else None
        if next_page:
            return redirect(url_for('quiz', question_num=next_page))
        return redirect(url_for('results'))

    previous = answers.get(str(question_num))
    return render_template('quiz.html',
        q=q,
        question_num=question_num,
        total=total,
        submitted_answer=previous,
        is_correct=None,
        show_feedback=False
    )


@app.route('/results')
def results():
    answers = session.get('answers', {})
    if not answers:
        return redirect(url_for('home'))

    score = 0
    results = []

    for q in questions:
        user_ans = answers.get(str(q['id']))

        if user_ans is None:
            results.append({
                'question': q['question'],
                'explanation': q['explanation'],
                'is_correct': False,
                'skipped': True
            })
            continue

        try:
            correct = int(user_ans) == q['answer']
        except (TypeError, ValueError):
            correct = False

        if correct:
            score += 1

        results.append({
            'question': q['question'],
            'explanation': q['explanation'],
            'is_correct': correct,
            'skipped': False
        })

    percent = round(score / total * 100)
    return render_template('results.html',
        score=score,
        total=total,
        answered=len(answers),
        percent=percent,
        results=results
    )


if __name__ == '__main__':
    app.run(debug=True)
