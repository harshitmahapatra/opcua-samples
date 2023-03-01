import asyncio
import logging
from typing import Dict, List

import grpc
import yaml
from asyncua import Client

import dataplane_pb2
import dataplane_pb2_grpc


def call_model(mlserver_grpc_url: str, model_name: str, input_values: Dict) -> Dict:
    print(f"\n---INPUT VALUES---\n {input_values}")

    channel = grpc.insecure_channel(target=mlserver_grpc_url)
    stub = dataplane_pb2_grpc.GRPCInferenceServiceStub(channel=channel)

    print("Gathering model request specification...")

    model_metadata_req = dataplane_pb2.ModelMetadataRequest(name=model_name)

    model_metadata: dataplane_pb2.ModelMetadataResponse = stub.ModelMetadata(
        model_metadata_req
    )

    print(f"\n----DISCOVERED INPUT SPEC----\n {model_metadata.inputs}")
    print(f"\n----DISCOVERED OUTPUT SPEC----\n {model_metadata.outputs}")

    print("Calling model inference...")

    inference_inputs = generate_infer_inputs(
        inputs_metadata=model_metadata.inputs, inputs_values=input_values
    )

    model_inference_req = dataplane_pb2.ModelInferRequest(
        model_name=model_name, inputs=inference_inputs
    )

    model_inference_res: dataplane_pb2.ModelInferResponse = stub.ModelInfer(
        model_inference_req
    )

    output_values = parse_output_values(model_inference_res.outputs)

    print(f"\n----OUTPUT VALUES----\n {output_values}")

    return output_values


def generate_infer_inputs(
    inputs_metadata: List[dataplane_pb2.ModelMetadataResponse.TensorMetadata],
    inputs_values: Dict,
):
    input_iterable: List[dataplane_pb2.ModelInferRequest.InferInputTensor] = []

    for input in inputs_metadata:
        input_value = inputs_values[input.name]
        if not hasattr(input_value, "__iter__"):
            input_value = [input_value]
        input_tensor_contents = insert_value_into_tensor_content(
            datatype=input.datatype, input_value=input_value
        )

        input_iterable.append(
            dataplane_pb2.ModelInferRequest.InferInputTensor(
                name=input.name,
                datatype=input.datatype,
                shape=input.shape,
                parameters=input.parameters,
                contents=input_tensor_contents,
            )
        )
    return input_iterable


def parse_output_values(
    model_infer_outputs: List[dataplane_pb2.ModelInferResponse.InferOutputTensor],
) -> Dict:
    output_values = {}
    for infer_output in model_infer_outputs:
        output_value = extract_value_from_tensor_content(
            datatype=infer_output.datatype, tensor_contents=infer_output.contents
        )
        if is_shape_scalar(infer_output.shape):
            output_value = output_value[0]
        output_values[infer_output.name] = output_value
    return output_values

def is_shape_scalar(shape):
    for dim in shape:
        if (dim!=1) and (dim!=-1):
            return False
    return True


def insert_value_into_tensor_content(
    datatype: str, input_value
) -> dataplane_pb2.InferTensorContents:
    if datatype == "BOOL":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            bool_contents=input_value
        )
    elif datatype == "BYTES":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            bytes_contents=input_value
        )
    elif datatype == "FP32":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            fp32_contents=input_value
        )
    elif datatype == "FP64":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            fp64_contents=input_value
        )
    elif datatype == "INT64":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            int64_contents=input_value
        )
    elif datatype == "INT32":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            int_contents=input_value
        )
    elif datatype == "UINT32":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            uint64_contents=input_value
        )
    elif datatype == "UINT64":
        input_tensor_contents = dataplane_pb2.InferTensorContents(
            uint_contents=input_value
        )
    else:
        raise ValueError(f"Unknown input tensor datatype: {datatype} !")
    return input_tensor_contents


def extract_value_from_tensor_content(
    datatype: str, tensor_contents: dataplane_pb2.InferTensorContents
):
    if datatype == "BOOL":
        output_value = tensor_contents.bool_contents
    elif datatype == "BYTES":
        output_value = tensor_contents.bytes_contents
    elif datatype == "FP32":
        output_value = tensor_contents.fp32_contents
    elif datatype == "FP64":
        output_value = tensor_contents.fp64_contents
    elif datatype == "INT64":
        output_value = tensor_contents.int64_contents
    elif datatype == "INT32":
        output_value = tensor_contents.int_contents
    elif datatype == "UINT32":
        output_value = tensor_contents.uint_contents
    elif datatype == "UINT64":
        output_value = tensor_contents.uint64_contents
    else:
        raise ValueError(f"Unknown input tensor datatype: {datatype} !")
    return output_value


def load_config():
    with open("opcua_config.yml", "r") as file:
        config = yaml.safe_load(file)
    return config


async def link_opcua_server_and_ml_model(config):
    opcua_server_url = config["opcua_server_url"]
    opcua_namespace = config["opcua_namespace"]
    model_name = config["model_name"]
    mlserver_grpc_url = config["mlserver_grpc_url"]
    inputs = config["tag_mapping"]["inputs"]
    outputs = config["tag_mapping"]["outputs"]

    print(f"Connecting to {opcua_server_url} ...")
    async with Client(url=opcua_server_url) as client:
        # Find the namespace index
        nsidx = await client.get_namespace_index(opcua_namespace)
        print(f"Namespace Index for '{opcua_namespace}': {nsidx}")

        input_values = {}

        predict_obj = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:{model_name}", f"{nsidx}:predict"]
        )
        predict = await predict_obj.read_value()

        if predict:
            print("Predict is enabled continuing with prediction...")
            for input in inputs:
                input_obj = await client.nodes.root.get_child(
                    ["0:Objects", f"{nsidx}:{model_name}", f"{nsidx}:{input['tag']}"]
                )
                input_val = await input_obj.read_value()
                input_values[input["name"]] = input_val

            output_values = call_model(mlserver_grpc_url, model_name, input_values)

            for output in outputs:
                output_obj = await client.nodes.root.get_child(
                    ["0:Objects", f"{nsidx}:{model_name}", f"{nsidx}:{output['tag']}"]
                )
                await output_obj.write_value(output_values[output["name"]])
            await predict_obj.write_value(False)
        else:
            print("Predict is disabled skipping prediction...")

if __name__ == "__main__":
    config = load_config()
    asyncio.run(link_opcua_server_and_ml_model(config))
