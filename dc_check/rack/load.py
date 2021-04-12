from voluptuous import Schema, All, Required, Invalid, MultipleInvalid
from voluptuous.humanize import humanize_error
import yaml

from .datatypes import *

# NB: 'ware the conflict with voluptuous - both have Any and All
from typing import Type, TypeVar, Callable, Any, List, Dict, Optional, Set

# Helpers that convert input data to structured Python types

__all__ = ['read_server_file', 'NotValid']


T = TypeVar('T', str, int)


def Coerce(typ: Type[T], msg: str = None) -> Callable[[T], T]:
    """Coerce a value to a type.

    If the type constructor throws a ValueError, the value will be marked as
    Invalid.
    """
    def f(v: T) -> T:
        try:
            return typ(v)
        except ValueError:
            raise Invalid(msg or ('expected %s' % typ.__name__))
    return f


def int_range(min_v: int, max_v: int, msg: str = None) -> Callable[[int], int]:
    def f(v: int) -> int:
        try:
            val = int(v)
        except (TypeError, ValueError):
            raise Invalid(msg or 'expected int')
        if val < min_v or val > max_v:
            raise Invalid(f'Value must be from {min_v} to {max_v}')

        return val

    return f


# Typing found in the input data
# Base  ypes (mostly aliases)
rack_name = str
device_name = str
server_id = Coerce(str)
rack_loc = int_range(0, 41)
port_loc = int

# Structures
server_schema = {device_name: server_id}
switch_schema = {device_name: server_id}

rack_schema = {rack_name: {rack_loc: device_name}}

connection_schema = {
    rack_name: [
        [rack_loc, port_loc, rack_loc, port_loc]
    ]
}


def server_file_structure(data: dict) -> ServerFileData:
    """"Transform read data into the elegant form, validating extra things"""

    errs = []

    # Deal with servers
    servers = data['servers']
    server_ids = servers.values()

    # Deal with servers
    # NB: this is a dict input; server names are definitely unique

    servers_output: Dict[str, Server] = {
        k: Server(k, v) for k, v in servers.items()
    }

    # Deal with switches
    # NB: this is a dict input; switchnames are definitely unique

    switches = data['switches']
    switch_ids = switches.values()

    switches_output: Dict[str, Switch] = {
        k: Switch(k, v) for k, v in switches.items()
    }

    # Make device set from servers and switches

    devices_output: Dict[str, Device] = dict(servers_output)
    devices_output.update(switches_output)

    if len(servers) + len(switches) != len(devices_output.keys()):
        errs.append(Invalid("Server shares a name with a switch"))

    all_ids = list(server_ids)
    all_ids.extend(switch_ids)

    if len(server_ids) + len(switch_ids) != len(set(all_ids)):
        errs.append(Invalid(
            f"Server [{str(sorted(server_ids))}] "
            f"and switch [{str(sorted(switch_ids))}] "
            f"serial numbers are not unique"))

    try:
        # Construct racks

        racks = data['racks']

        racks_output: Dict[str, Rack] = {}

        for rack_name, elems in racks.items():
            rack_elems: Dict[int, Device] = {}
            for loc, dev_name in elems.items():
                dev_obj = devices_output.get(dev_name)
                if dev_obj is None:
                    errs.append(
                        Invalid(
                            f"Rack {rack_name} location {loc}: "
                            f"{dev_name} is an unknown device"))
                else:
                    rack_elems[loc] = dev_obj

            racks_output[rack_name] = Rack(dev_name, rack_elems)

        connections = data['connections']

        connections_output: Set[Connection] = set()
        # Confirm we're connecting devices that we know about.
        # Transform connections to device references.

        for rack_name, wires in connections.items():
            rack = racks_output.get(rack_name)
            if rack is None:
                errs.append(Invalid(f'In connections, {rack_name} '
                                    f'has not been defined'))
            else:
                # Sort: gets consistent error ordering.
                for f in sorted(wires):
                    rack_slot1, port1, rack_slot2, port2 = f

                    def get_dev(loc: int) -> Optional[Device]:
                        assert rack is not None  # for typechecking
                        dev = rack.devices.get(loc)
                        if dev is None:
                            errs.append(
                                Invalid(
                                    f'In connections, RU #{loc} '
                                    f'in {rack_name} has no device'))
                        return dev

                    rack_dev1 = get_dev(rack_slot1)
                    rack_dev2 = get_dev(rack_slot2)

                    if rack_dev1 is not None and rack_dev2 is not None:
                        conn = Connection(rack_dev1, port1,
                                          rack_dev2, port2)
                        if conn in connections_output:
                            errs.append(
                                Invalid(
                                    f"Duplicate connection: "
                                    f"slot#{rack_slot1}:port#{port1} "
                                    f"-> slot#{rack_slot2}:port#{port2} "
                                    f"results in {conn.text()} - "
                                    "do you have the reverse "
                                    "connection listed?"))
                        else:
                            connections_output.add(conn)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

    if errs:
        raise MultipleInvalid(errs)

    return ServerFileData(
        servers_output,
        switches_output,
        devices_output,
        racks_output,
        connections_output)


input_schema = All({
    Required('version'): 1,
    Required('servers'): server_schema,
    Required('switches'): switch_schema,
    Required('racks'): rack_schema,
    Required('connections'): connection_schema
}, server_file_structure)


class NotValid(Exception):
    def __init__(self, msg: str):
        self.msg = msg


def read_server_file(filename: str) -> ServerFileData:
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)

        vol_schema = Schema(input_schema)
        try:
            data = vol_schema(data)
        except MultipleInvalid as e:
            raise NotValid(msg=humanize_error(data, e,
                                              max_sub_error_length=40))

        return data
