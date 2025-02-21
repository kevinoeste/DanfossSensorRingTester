from flask import Flask, render_template, request


app = Flask(__name__)

#flask page control
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/data")
def ViewData():
    return render_template('ViewData.html')


if __name__ == "__main__":
    app.run(debug=True)
