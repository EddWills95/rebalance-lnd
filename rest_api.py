from flask import Flask, request, render_template
from flask.json import jsonify
from output import Output
from rebalance import Rebalance, get_argument_parser
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, send
import os

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)

argument_parser = get_argument_parser()
basic_arguments = argument_parser.parse_args()
basic_arguments.lnddir = os.environ.get('LNDDIR')
basic_arguments.grpc = os.environ.get('GRPC')

rebalancer = Rebalance(basic_arguments)


# class WebSocketOutput(Output, ):
# @staticmethod
# def print_line(message, end='\n'):

@socketio.on('connect')
def test_connect(auth):
    print('connected')
    send('Connected')
    emit('my response', {'data': 'Connected'})


@socketio.on('message')
def message(message):
    print(message)


@socketio.on('json')
def json(message):
    print(message)


@app.get('/')
def index():
    return render_template('index.html')


@app.route("/rebalance")
def rebalance():
    print(basic_arguments)
    basic_arguments.to = request.args.get('to')
    Rebalance(basic_arguments).start()
    return "Hello"


if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=True)
