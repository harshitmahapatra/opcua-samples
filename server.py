import asyncio
import logging
import random
from typing import Dict

import yaml
from asyncua import Node, Server


def load_config():
    with open("opcua_config.yml", "r") as file:
        config = yaml.safe_load(file)
    return config


async def main(config):
    opcua_server_url = config["opcua_server_url"]
    opcua_namespace = config["opcua_namespace"]
    model_name = config["model_name"]
    mlserver_grpc_url = config["mlserver_grpc_url"]
    inputs = config["tag_mapping"]["inputs"]
    outputs = config["tag_mapping"]["outputs"]

    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint(opcua_server_url)

    # set up our own namespace, not really necessary but should as spec
    uri = opcua_namespace
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root

    ml_object = await server.nodes.objects.add_object(idx, model_name)

    predict = await ml_object.add_variable(idx, "predict", True)
    await predict.set_writable()

    input_objects: Dict[str, Node] = {}
    output_objects: Dict[str, Node] = {}

    for input in inputs:
        input_obj = await ml_object.add_variable(
            idx, input["tag"], random.randint(1, 9)
        )
        await input_obj.set_writable()
        input_objects[input["tag"]] = input_obj

    for output in outputs:
        output_obj = await ml_object.add_variable(idx, output["tag"], 0)
        await output_obj.set_writable()
        output_objects[output["tag"]] = output_obj

    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            _logger.info("----START-LOOP---")
            for input in inputs:
                input_val = await input_objects[input["tag"]].get_value()
                _logger.info(f"Input: {input['tag']} has value {input_val}")
            for output in outputs:
                output_val = await output_objects[output["tag"]].get_value()
                _logger.info(f"Output: {output['tag']} has value {output_val}")
            predict_val = await predict.get_value()
            _logger.info(f"Predict has value {predict_val}")
            _logger.info("----END-LOOP---")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    config = load_config()
    asyncio.run(main(config), debug=True)
