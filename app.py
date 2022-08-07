from flask import Flask, request, render_template, jsonify
from wifi_capture import find_wlans_and_probes
import json

app = Flask(__name__)


@app.route('/update', methods=['GET'])
def start_tshark():
    # data = get_test_data()
    data = find_wlans_and_probes()
    return jsonify(data)


@app.route('/', methods=['GET'])
def load_app():
    return render_template('index.html')
