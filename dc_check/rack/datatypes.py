from typing import Type, TypeVar, Callable, Any, List, Dict, Optional, Set, \
    Tuple, Iterable

from dataclasses import dataclass
from abc import abstractmethod, ABC

__all__ = ['Device', 'Server', 'Switch', 'Rack', 'Connection',
           'ServerFileData']


# NB: ABC, mypy and dataclass don't mix well
@dataclass(eq=True, frozen=True)  # type: ignore
class Device(ABC):
    name: str
    serial: str

    @abstractmethod
    def text(self) -> str:
        pass


class Server(Device):

    def text(self) -> str:
        return f"Server-{self.name}#{self.serial}"


class Switch(Device):

    def text(self) -> str:
        return f"Switch-{self.name}"


@dataclass(eq=True, frozen=True)
class Rack:
    name: str
    devices: Dict[int, Device]

    def devs(self, devtype: type) -> Iterable[Device]:
        for f in self.devices.values():
            if isinstance(f, devtype):
                yield f


@dataclass
# TODO(ijw): better to normalise on the __lt__ of hashes?
class Connection:
    # Has the lower devname
    dev1: Device
    port1: int

    # Has the higher devname
    dev2: Device
    port2: int

    def __init__(self,
                 dev1: Device, port1: int,
                 dev2: Device, port2: int):
        if dev1 == dev2 and port1 == port2:
            raise ValueError("Can't connect a port to itself")

        if (dev1.name < dev2.name
                or (dev1 == dev2 and port1 < port2)):
            self.dev1 = dev1
            self.port1 = port1
            self.dev2 = dev2
            self.port2 = port2
        else:
            # Swap; this is now normalised, so if the args were given
            # the other way around you'd get the same object.
            self.dev2 = dev1
            self.port2 = port1
            self.dev1 = dev2
            self.port1 = port2

    def text(self) -> str:
        """Print for humans"""
        return (f"{self.dev1.text()}:port#{self.port1} "
                f"to {self.dev2.text()}:port#{self.port2}")

    # Otherwise, this is a fairly standard data object

    def __hash__(self) -> int:
        """Hash func: allows use in sets"""
        return hash((self.dev1, self.dev2, self.port1, self.port2))

    def __repr__(self) -> str:
        return (f'Connection({self.dev1}:{self.port1} -> '
                f'{self.dev2}:{self.port2}')

    def __eq__(self, c: object) -> bool:
        if not isinstance(c, Connection):
            return False

        return (c.dev1 == self.dev1
                and c.dev2 == self.dev2
                and c.port1 == self.port1
                and c.port2 == self.port2)


# The type of our output data:
@dataclass
class ServerFileData:
    servers: Dict[str, Server]
    switches: Dict[str, Switch]
    devices: Dict[str, Device]
    racks: Dict[str, Rack]
    connections: Set[Connection]

    def find_conns(self, device_name: str) -> Dict[int, Tuple[Device, int]]:
        device = self.devices[device_name]

        conns = [x for x in self.connections
                 if (x.dev1 == device
                     or x.dev2 == device)]

        conns_rv = {}
        for f in conns:
            if f.dev1 == device:
                conns_rv[f.port1] = (f.dev2, f.port2,)
            else:
                conns_rv[f.port2] = (f.dev1, f.port1,)

        return conns_rv
