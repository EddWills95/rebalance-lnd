from argparse import Namespace
from flask import Flask, request, render_template
from flask import json
from flask.json import jsonify
from output import Output, format_channel_id
from rebalance import Rebalance, get_argument_parser, get_local_available, get_remote_available
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, send
from flask_cors import CORS
import json
import os
import re

load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class WebSocketOutput(Output):
    @staticmethod
    def print_line(message, end='\n'):
        emit('rebalance', ansi_escape.sub('', message))
        print(message)

    @staticmethod
    def print_without_linebreak(message):
        emit('rebalance', ansi_escape.sub('', message))
        print(message)


argument_parser = get_argument_parser()
basic_arguments = argument_parser.parse_args()
basic_arguments.lnddir = os.environ.get('LNDDIR')
basic_arguments.grpc = os.environ.get('GRPC')

rebalancer = Rebalance(basic_arguments)
rebalancer.ouput = WebSocketOutput(rebalancer.lnd)


@socketio.on('connect')
def test_connect(auth):
    print('Connected', auth)
    send('Connected')


@socketio.on('rebalance')
def message(incoming):
    message = json.loads(incoming)
    args = vars(basic_arguments)
    # Build Args
    args['list_candidates'] = False
    args['to'] = message.get('to')
    args['amount'] = message.get('amount')
    args['first_hop_channel_id'] = message.get('from')
    args['last_hop_channel_id'] = message.get('to')
    temp_rebalancer = Rebalance(Namespace(**args))
    temp_rebalancer.output = WebSocketOutput(temp_rebalancer.lnd)
    temp_rebalancer.start()


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/channels')
def channels():

    args = vars(basic_arguments)

    args['list_candidates'] = True

    # Collect channels and convert to nice JSON
    channels = Rebalance(Namespace(**args)).start()
    return jsonify(list(map(lambda c:
                            {
                                "channelId": str(c.chan_id),
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
    try:
        socketio.run(app, debug=True)
    except BaseException as base:
        print('Preventing normal exit', base)
