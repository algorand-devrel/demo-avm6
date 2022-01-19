Demo for AVM 1.1 features
-------------------------

Contract To Contract calls

requires sandbox with this feature branch: https://github.com/algorand/go-algorand/tree/feature/contract-to-contract

requires this branch of pyteal https://github.com/algorand/pyteal/pull/149 

when the sandbox is running, you should be able to call `python demo.py` 

see comments inline for what is happening

# C2C 

Simple example of calling one app from another using an inner transaction created by the first app.  This example uses the ABI scheme to encode/decode the arguments and return values.

## c2c files
-----
app.py  - contains approval and clear programs in pyteal
demo.py - contains python logic to create the applications and call them
sandbox.py - utility to get all the accounts from `unencrypted-default-wallet`
contract.json - json file describing the ABI for the contracts

# Trampoline

Simple example to demonstrate the use of an existing application to dynamically create a transaction to pay an account who's address is unknown at transaction signing time. 

This is especially useful in the case that an application creator wants to create an application _and_ fund it within a single (grouped) transaction.

## trampoline files
-----
app.py  - contains approval and clear programs in pyteal
demo.py - contains python logic to create the applications and call them
sandbox.py - utility to get all the accounts from `unencrypted-default-wallet`
contract.json - json file describing the ABI for the contracts
