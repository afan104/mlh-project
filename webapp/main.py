from flask import Flask, send_file, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return open("webpage.html").read()


@app.route("/download")
def download_file():
    # Replace 'yourfile.exe' with the path to your actual file
    return send_file("test_file.txt", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
