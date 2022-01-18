AVM 1.0 `log` opcode demo
------------------------

This demo is meant to illustrate how you can use the new `log` opcode in a Smart Contract to write bytes and read bytes generated during the evaluation of an App Call.

The Smart Contracts are written in [PyTeal](https://developer.algorand.org/docs/get-details/dapps/pyteal/) in `app.py` and are compiled to TEAL. The only function they perform is that during a NoOp AppCall transaction evaluation, they log the first several lines from the "99 Bottles of Beer" song.  This is done using a For loop and a subroutine to log the bytes. 

The `demo.py` file contains logic to deploy the Application from the Smart Contracts on chain, then call the application,  then read and print the logs from the pending transaction pool.

The logs are returned in the `logs` array of the PendingTransactions return object and are base64 encoded bytestrings. 

Technical Details
-----------------

The `log` opcode has the following technical limits:

    - It may only be called in a Smart Contract (as opposed to a Smart Signature)
    - It may only be called in TEAL version  >= 5 
    - It may be called up to 32 times per program execution 
    - It may log up to 1024 bytes total per program execution


Further, the log opcode is intended to be used in the future for ABI return values. It may not useful for debugging in the case a transaction fails, since no logs will be stored. 

