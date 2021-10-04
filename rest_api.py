from flask import Flask
from flask.json import jsonify
from rebalance import Rebalance, get_argument_parser
from dotenv import load_dotenv
import json
import os

load_dotenv()

app = Flask(__name__)

argument_parser = get_argument_parser()
basic_arguments = argument_parser.parse_args()
basic_arguments.lnddir = os.environ.get('LNDDIR')
basic_arguments.grpc = os.environ.get('GRPC')

rebalancer = Rebalance(basic_arguments)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/channels")
def list_channels():
    # return MessageToJson(rebalancer.list_channels())
    print(rebalancer.list_channels())
    return jsonify({"channels": jsonify(rebalancer.list_channels())})


if __name__ == '__main__':
    app.run(debug=True)
