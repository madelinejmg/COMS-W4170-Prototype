from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/learn/<int:lesson_num>")
def learn(lesson_num):
    return render_template("learn.html", lesson_num=lesson_num)

@app.route("/quiz/<int:question_num>")
def quiz(question_num):
    return render_template("quiz.html", question_num=question_num)

@app.route("/results")
def results():
    return render_template("results.html")

if __name__ == "__main__":
    app.run(debug=True)