Demo for AVM 1.1 features
-------------------------

Contract To Contract calls

requires sandbox with this feature branch: https://github.com/algorand/go-algorand/tree/feature/contract-to-contract

requires this branch of pyteal https://github.com/algorand/pyteal/pull/149 

when the sandbox is running, you should be able to call `python demo.py` 

see comments inline for what is happening

## c2c files
-----
app.py  - contains approval and clear programs in pyteal
demo.py - contains python logic to create the applications and call them
sandbox.py - utility to get all the accounts from `unencrypted-default-wallet`
contract.json - json file describing the ABI for the contracts

## trampoline files
-----
app.py  - contains approval and clear programs in pyteal
demo.py - contains python logic to create the applications and call them
sandbox.py - utility to get all the accounts from `unencrypted-default-wallet`
contract.json - json file describing the ABI for the contracts
