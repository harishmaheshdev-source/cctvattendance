from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

attendance = []

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/mark', methods=['POST'])
def mark():
    data = request.json
    attendance.append(data)
    return jsonify({"status": "ok"})

@app.route('/data', methods=['GET'])
def data():
    return jsonify(attendance)

if __name__ == '__main__':
    app.run(debug=True)