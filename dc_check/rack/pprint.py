from .datatypes import *


def dump_conns_by_rack_and_device(
        server_file_data: ServerFileData) -> None:
    for name, rack in server_file_data.racks.items():
        print(f" - rack {name}")
        dump_conns_by_device(server_file_data, rack)


def dump_conns_by_device(
        server_file_data: ServerFileData,
        rack: Rack) -> None:
    for slot in sorted(rack.devices.keys()):
        device = rack.devices[slot]
        print(f"    - slot {slot}: device {device.name}")
        conns = server_file_data.find_conns(device.name)

        for port in sorted(conns.keys()):
            other_dev, other_port = conns[port]
            print(f'      port {port} to '
                  f'device {other_dev.name} port {other_port}')
