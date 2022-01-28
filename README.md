Demo for AVM 1.1 features
-------------------------


## Sandbox 

These demos require sandbox to be running with this feature branch: https://github.com/algorand/go-algorand/tree/feature/contract-to-contract

This can be done by setting the ALGOD_BRANCH in your config.* to `feature/contract-to-contract` and make sure the network template protocol version is `future`
```sh
export ALGOD_BRANCH="feature/contract-to-contract"
```


## Python Requirements

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
python -m demos.recusive_c2c.demo
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

# Trampoline

Fund app address during create

Simple example to demonstrate the use of an existing application to dynamically create a transaction to pay an account who's address is unknown at transaction signing time. 

This is especially useful in the case that an application creator wants to create an application _and_ fund it within a single (grouped) transaction.

## trampoline files

app.py  - contains approval and clear programs in pyteal
demo.py - contains python logic to create the applications and call them
contract.json - json file describing the ABI for the contracts

# New Ops

Demonstate how to use the newly available opcodes

current opcode budget - Get the remaining budget for a currently evaluating contract
caller app id / app address - Get the app id or address for the application that called "me" from an inner txn
bsqrt - Take the square root of a large number (represented as big endian bytes)
gitxn / gitxna - Get the fields from the transactions of the last inner group transaction
gloadss - Get the scratch space of a transaction in the current group

## new ops files

app.py  - contains approval and clear programs in pyteal
demo.py - contains python logic to create the applications and call them
contract.json - json file describing the ABI for the contracts

# Op up

NEED MORE POWER

While evaluating a contract, different code paths may require additional ops to complete successfully. This demo shows a way to check the current budget and request additional buget in the form of an application call transaction.

## op up files

app.py  - contains approval and clear programs in pyteal
demo.py - contains python logic to create the applications and call them
contract.json - json file describing the ABI for the contracts




happy hacking :)