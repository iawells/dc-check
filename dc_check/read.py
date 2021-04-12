import click
import sys

from .rack.load import NotValid, read_server_file
from .rack.pprint import dump_conns_by_rack_and_device


@click.command()
@click.argument('filename', nargs=1)
def cmd(filename: str) -> None:
    try:
        server_file_data = read_server_file(filename)

        print(f'{filename}: connections by device:')
        dump_conns_by_rack_and_device(server_file_data)

    except NotValid as e:
        print("Not valid:")
        print(e.msg)
        sys.exit(1)


if __name__ == '__main__':
    cmd()
