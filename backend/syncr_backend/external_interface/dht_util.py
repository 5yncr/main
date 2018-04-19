import asyncio
from typing import Any
from typing import Dict  # NOQA
from typing import List
from typing import Tuple

from kademlia.network import Server  # type: ignore
from kademlia.storage import ForgetfulStorage  # type: ignore

from syncr_backend.util import crypto_util
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)

_node_instance = None


def get_dht() -> Server:
    """
    returns the node_instance of the dht
    Throws TypeError if DHT has not been initialized
    """
    global _node_instance
    if _node_instance is None:
        raise TypeError("DHT has not been initilized")
    return _node_instance


def initialize_dht(
    bootstrap_ip_port_pair_list: List[Tuple[str, int]],
    listen_port: int,
) -> None:
    """
    connects to the distributed hash table
    if no bootstrap ip port pair list is given, it starts a new dht
    :param bootstrap_ip_port_pair_list:
    list of ip port tuples to connect to the dht
    :param listen_port: port to listen on
    :return: instance of server
    """
    global _node_instance

    get_logger("kademlia")

    logger.debug("set up DHT: %s", str(bootstrap_ip_port_pair_list))

    node = Server(storage=DropPeerDHTStorage())
    node.listen(listen_port)
    loop = asyncio.get_event_loop()
    if len(bootstrap_ip_port_pair_list) > 0:
        loop.run_until_complete(node.bootstrap(bootstrap_ip_port_pair_list))

    # t1 = threading.Thread(target=dht_thread, args=(
    #     loop, node, listen_port,)
    # )
    # t1.start()

    _node_instance = node


class DropPeerDHTStorage(ForgetfulStorage):
    """
    Extension of the default kademlia storage module
    It is different in that when given a list of bytes, it checks to see if
    it is an encoded set. If it is, it unions it with the rest of the
    sets
    """

    def __init__(self) -> None:
        """

        """
        self.timeouts = {}  # type: Dict[Tuple[Any, int, str], int]

        super().__init__()

    def __setitem__(self, key: Any, value: Any) -> None:
        """
        :param key: key to look up in dht
        :param value: value to put in dht under key
        """
        valuepeer = crypto_util.decode_peerlist(value)
        if valuepeer is not None:
            if key in self.data:
                peerlist = crypto_util.decode_peerlist(
                    self.data[key][1],
                )
                if peerlist is not None:
                    new_peerlist = \
                        crypto_util.encode_peerlist(
                            (peerlist + valuepeer),
                        )
                    return super().__setitem__(key, new_peerlist)

            return super().__setitem__(
                key,
                crypto_util.encode_peerlist(valuepeer),
            )

        return super().__setitem__(key, value)
