import flask
from flask import request, jsonify
import json

import dc_check.rack.load

from typing import List, Dict, Any, Tuple

from .rack.datatypes import Switch, Server, Device
from .rack.load import read_server_file, NotValid

MGMT_SWITCH = 'mgmt'
MGMT_PORT = 0


def create_app(db: str) -> flask.Flask:
    app = flask.Flask('dc_check')

    # TODO(ijw): make this a setting we can change
    app.config['DEBUG'] = True

    ########################################

    @app.route('/', methods=['GET'])
    def index() -> flask.Response:
        return flask.Response(
            'This is the dc-check API server.  Call its APIs.',
            mimetype='text/plain')

    ########################################

    def shutdown_server() -> None:
        """Stop the (test) webserver."""
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route('/shutdown', methods=['GET'])
    def shutdown() -> str:
        """An API call that can end the server.

        Useful for automated tests using this server, or else it will
        run forever.
        """
        shutdown_server()
        return 'Server terminated.'

    ########################################

    @app.route('/rack/<rack_name>/mgmt', methods=['GET'])
    def mgmt(rack_name: str) -> Tuple[str, int]:
        """Report what servers are attached to the management switch"""

        db = app.config['db']

        try:
            server_file_data = read_server_file(db)

            conns = server_file_data.find_conns(MGMT_SWITCH)
            output = {}
            for k, v in conns.items():
                # device name: port on mgmt switch
                output[v[0].serial] = k

            return jsonify(output)
        except NotValid as e:
            return "DB file is not valid: {e.msg}", 400

    @app.route('/rack/<rack_name>/conns', methods=['GET'])
    def connectivity(rack_name: str) -> Tuple[str, int]:
        """Report what servers are attached to each other and the TORs

        Will show a server *if* it is connected to the management switch"""

        db = app.config['db']

        try:
            server_file_data = read_server_file(db)

            mgmt_conns = server_file_data.find_conns(MGMT_SWITCH)
            mgmt_connected_servers = [v[0] for k, v in mgmt_conns.items()]

            server_output = {}

            def make_portdict(device_list: List[Device]) \
                    -> Dict[str, Dict[str, Any]]:

                # We're a bit lax about this type; it's for JSONifying.
                devices: Dict[str, Dict[str, Any]] = {}
                for f in device_list:
                    conns = server_file_data.find_conns(f.name)

                    ports: Dict[str, Dict[str, Dict[str, str]]] = {}
                    for port, peer in conns.items():
                        ports[str(port)] = {
                            'peer': {
                                'serialNumber': peer[0].serial,
                                'port': str(peer[1])
                            }
                        }
                    devices[f.serial] = ports
                return devices

            server_output = {
                'rack': rack_name,
                'servers': make_portdict(mgmt_connected_servers),
                'switches': make_portdict(
                    server_file_data.racks[rack_name].devs(Switch))
            }

            return jsonify(server_output)
        except NotValid as e:
            return "DB file is not valid: {e.msg}", 400

    ########################################

    app.config.update({'db': db})

    return app


def run(db: str, port: int) -> None:
    app = create_app(db)
    app.run(host='0.0.0.0', port=port)
