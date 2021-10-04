from flask import Flask, request, render_template
from flask import json
from flask.json import jsonify
from output import Output, format_channel_id
from rebalance import Rebalance, get_argument_parser, get_local_available, get_remote_available
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, send
import jsonpickle
import os

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)


class WebSocketOutput(Output):
    @staticmethod
    def print_line(message, end='\n'):
        send(message)

    @staticmethod
    def print_without_linebreak(message):
        send(message)


argument_parser = get_argument_parser()
basic_arguments = argument_parser.parse_args()
basic_arguments.lnddir = os.environ.get('LNDDIR')
basic_arguments.grpc = os.environ.get('GRPC')

rebalancer = Rebalance(basic_arguments)
rebalancer.ouput = WebSocketOutput(rebalancer.lnd)


@socketio.on('connect')
def test_connect(auth):
    print('connected')
    send('Connected')


@socketio.on('message')
def message(message):
    print(message)
    if (message['type'] == 'rebalance'):

        # Build Args
        basic_arguments.to = message['to']
        temp_rebalancer = Rebalance(basic_arguments)
        temp_rebalancer.output = WebSocketOutput(temp_rebalancer.lnd)
        temp_rebalancer.start()


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/channels')
def channels():
    # Check for incoming or outgoing.

    # Collect channels and convert to nice JSON
    channels = Rebalance(basic_arguments).list_channels()
    return jsonify(list(map(lambda c:
                            {
                                "channelId": c.chan_id,
                                "alias": rebalancer.lnd.get_node_alias(c.remote_pubkey),
                                "pubkey": c.remote_pubkey,
                                "channelPoint": c.channel_point,
                                "localRatio": float(c.local_balance) / (c.remote_balance + c.local_balance),
                                "capacity": c.capacity,
                                "remoteAvailable": get_remote_available(c),
                                "localAvailable": get_local_available(c),
                                "rebalanceAmount": rebalancer.get_rebalance_amount(c)
                            },
                            channels
                            )))


if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=True)
