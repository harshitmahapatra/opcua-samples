import asyncio

import requests
from asyncua import Client

url = "opc.tcp://localhost:4840/factoryml/server/"
namespace = "http://factoryml.alexandra.dk"


def call_addition_model(val_a, val_b):
    # mlflow_url = "http://localhost:5000/invocations"

    # payload = {
    #     "dataframe_split": {"columns": ["a", "b", "c"], "data": [[1, 2, 3], [4, 5, 6]]}
    # }

    # payload_actual = {"a": val_a, "b": val_b}

    # sum = requests.get(url=mlflow_url,json=payload_actual)
    # print(sum)
    # raise ValueError()
    return val_a + val_b


async def main():
    print(f"Connecting to {url} ...")
    async with Client(url=url) as client:
        # Find the namespace index
        nsidx = await client.get_namespace_index(namespace)
        print(f"Namespace Index for '{namespace}': {nsidx}")

        # Get the variable node for read / write
        a = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:MLObject", f"{nsidx}:a"]
        )
        val_a = await a.read_value()
        print(f"Value of a ({a}): {val_a}")

        b = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:MLObject", f"{nsidx}:a"]
        )
        val_b = await b.read_value()
        print(f"Value of b ({b}): {val_b}")

        sum = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:MLObject", f"{nsidx}:sum"]
        )
        val_sum = await sum.read_value()
        print(f"Value of sum ({sum}): {val_sum}")

        calc_sum = call_addition_model(val_a, val_b)

        print(f"Setting value of sum to {calc_sum} ...")
        await sum.write_value(calc_sum)


if __name__ == "__main__":
    asyncio.run(main())
