from typing import Dict, List

import grpc
import numpy as np

import dataplane_pb2
import dataplane_pb2_grpc


def add_numbers(
    mlserver_grpc_url: str, model_name: str, input_values: Dict[str, np.ndarray]
) -> int:
    print("----INPUT VALUES----")
    print(input_values)

    channel = grpc.insecure_channel(target=mlserver_grpc_url)
    stub = dataplane_pb2_grpc.GRPCInferenceServiceStub(channel=channel)

    print("Gathering model request specification...")

    model_metadata_req = dataplane_pb2.ModelMetadataRequest(name=model_name)

    model_metadata: dataplane_pb2.ModelMetadataResponse = stub.ModelMetadata(
        model_metadata_req
    )

    print("----DISCOVERED INPUT SPEC----")
    print(model_metadata.inputs)
    print("----DISCOVERED OUTPUT SPEC----")
    print(model_metadata.outputs)

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

    print("----OUTPUT VALUES----")
    print(output_values)

    return 0


def generate_infer_inputs(
    inputs_metadata: List[dataplane_pb2.ModelMetadataResponse.TensorMetadata],
    inputs_values: Dict[str, np.ndarray],
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
):
    output_values = {}
    for infer_output in model_infer_outputs:
        output_value = extract_value_from_tensor_content(
            datatype=infer_output.datatype, tensor_contents=infer_output.contents
        )
        output_values[infer_output.name] = output_value
    return output_values


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


if __name__ == "__main__":
    mlserver_grpcs_url = "localhost:8081"
    model_name = "pyfunc"
    add_numbers(
        mlserver_grpc_url=mlserver_grpcs_url,
        model_name=model_name,
        input_values={"a": [5], "b": [6]},
    )
