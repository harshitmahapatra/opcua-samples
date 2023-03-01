import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.methods import uamethod


@uamethod
def func(parent, value):
    return value * 2


async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/factoryml/server/")

    # set up our own namespace, not really necessary but should as spec
    uri = "http://factoryml.alexandra.dk"
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root

    mlObject = await server.nodes.objects.add_object(idx, "MLObject")
    a = await mlObject.add_variable(idx, "a", 5)
    b = await mlObject.add_variable(idx, "b", 6)
    sum = await mlObject.add_variable(idx, "sum", 0)

    # Set output variable to be writable by client
    await a.set_writable()
    await b.set_writable()
    await sum.set_writable()

    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(5)
            val_a = await a.get_value()
            val_b = await b.get_value()
            val_sum = await sum.get_value()
            _logger.info(f"The sum of input a {val_a} and  input b {val_b} is sum {val_sum}.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)