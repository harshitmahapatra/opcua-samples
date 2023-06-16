# OPCUA Experiments with Asyncua

The repository contains code to start a OPC UA server and a corresponding client using the python based asyncua library.

**N.B. asyncua is licensed under LGPLv3, that means it is free to be used in a commercial software without any requirements, however if the library itself is modified, then those modifications must be published under LGPLv3.**

The client and server examples are taken from the asyncua repository and are thus assumed to have the LGPLv3 license.


**N.B. opcua-gui-client is licensed under GPLv3 which means that it cannot be used or modified without the associated software also being distributed under GPLv3, thus the use of opcua-gui-client in any potentially commercial software is not recommended.**

## Setup

1. Create and activate the virtual environment.
    ```bash
    python3 -m venv .venv
    . ./.venv/bin/activate
    ```
2. Install the [asyncua](https://github.com/FreeOpcUa/opcua-asyncio) library.
    ```bash
    pip install asyncua
    ```
3. Install the [GUI client](https://github.com/FreeOpcUa/opcua-client-gui) and pyqtgraph
    ```bash
    pip install opcua-client
    pip install pyqtgraph
    ```

## Usage

1. Run the server
```bash
python server.py
```
2. Run the client
```bash
python client.py
```
3. Run the GUI client
```bash
opcua-client
```
