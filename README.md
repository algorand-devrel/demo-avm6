Demo for AVM 1.1 features
-------------------------


## Sandbox 

A sandbox running `release` branch.

The provided `config.release` will suite this need, `./sandbox up release` to start it (you may need to sandbox down/sandbox clean first)

## Python Requirements

Python 3.10 is required.
If Ubuntu 20.04, macOS 12, or HomeBrew on macOS is used, manual installation of Python 3.10 is required.

Once you've cloned this repo down, cd to this directory and run

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

to install the python requirements

With the sandbox running and the venv requirements in place, you should be able to run:

```sh
python -m demos.c2c.demo
# or
python -m demos.c2c_max_depth.demo
# or
python -m demos.eth_ecdsa_recover.demo
# or
python -m demos.new_ops.demo
# or
python -m demos.op_up.demo
# or
python -m demos.trampoline.demo
```

# C2C 

Contract To Contract calls

Simple example of calling one app from another using an inner transaction created by the first app.  This example uses the ABI scheme to encode/decode the arguments and return values.

## c2c files

    app.py  - contains approval and clear programs in pyteal
    demo.py - contains python logic to create the applications and call them
    contract.json - json file describing the ABI for the contracts


# C2C Max Depth

Useless example that shows the max depth limitation of 8 inner app calls.


## c2c max depth files

    app.py  - contains approval and clear programs in pyteal
    demo.py - contains python logic to create the applications and call them


# eth_ecdsa_recover

This example shows how to get the equivalent of OpenZeppelin ECDSA.recover for long 65-byte Ethereum signatures
(https://docs.openzeppelin.com/contracts/2.x/api/cryptography#ECDSA-recover-bytes32-bytes-)
Short 64-byte Ethereum signatures require some changes to the code.
This can be used in applications requiring some compatibility with Ethereum.
For pure Algorand applications, ed25519 is strongly recommended instead of ecdsa.

Like the other examples, this example has *NOT* been audited and *MUST NOT* be used in production code.
If this example is used in production code, a full audit is necessary due to the nature of this example
(use of cryptography).

## c2c max depth files

    app.py  - contains approval and clear programs in pyteal
    demo.py - contains python logic to create the applications and call them


# Trampoline

Fund app address during create

Simple example to demonstrate the use of an existing application to dynamically create a transaction to pay an account whose address is unknown at transaction signing time. 

This is especially useful in the case that an application creator wants to create an application _and_ fund it within a single (grouped) transaction.

## trampoline files

    app.py  - contains approval and clear programs in pyteal
    demo.py - contains python logic to create the applications and call them
    contract.json - json file describing the ABI for the contracts

# New Ops

Demonstate how to use the newly available opcodes

    - current opcode budget - Get the remaining budget for a currently evaluating contract
    - caller app id / app address - Get the app id or address for the application that called "me" from an inner txn
    - bsqrt - Take the square root of a large number (represented as big endian bytes)
    - gitxn / gitxna - Get the fields from the transactions of the last inner group transaction
    - gloadss - Get the scratch space of a transaction in the current group

## new ops files

    app.py  - contains approval and clear programs in pyteal
    demo.py - contains python logic to create the applications and call them
    contract.json - json file describing the ABI for the contracts

# Op up

NEED MORE POWER

While evaluating a contract, different code paths may require additional ops to complete successfully. This demo shows a way to check the current budget and request additional buget in the form of an application call transaction.

Note that current versions of PyTeal include such a logic using the `OpUp` function.

## op up files

    app.py  - contains approval and clear programs in pyteal
    demo.py - contains python logic to create the applications and call them
    contract.json - json file describing the ABI for the contracts




happy hacking :)