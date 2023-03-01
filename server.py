import asyncio
import logging

import yaml
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

    mlObject = await server.nodes.objects.add_object(idx, "pyfunc")
    weight_of_platform = await mlObject.add_variable(idx, "weight_of_platform", 5)
    weight_of_load = await mlObject.add_variable(idx, "weight_of_load", 6)
    total_weight = await mlObject.add_variable(idx, "total_weight", 0)
    predict = await mlObject.add_variable(idx, "predict", True)

    # Set output variable to be writable by client
    await weight_of_platform.set_writable()
    await weight_of_load.set_writable()
    await total_weight.set_writable()
    await predict.set_writable()

    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            val_wieght_of_platform = await weight_of_platform.get_value()
            val_weight_of_load = await weight_of_load.get_value()
            val_total_weight = await total_weight.get_value()
            val_predict = await predict.get_value()
            _logger.info(f"total weight: {val_total_weight}; weight_of_platform {val_wieght_of_platform}; weight_of_load {val_weight_of_load}; predict {val_predict}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)