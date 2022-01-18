from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
from sandbox import get_accounts
import base64
import os

from app import get_approval, get_clear

client = algod.AlgodClient("a"*64, "http://localhost:4001")

def get_method(c: Contract, name: str) -> Method:
    for m in c.methods:
        if m.name == name:
            return m
    raise Exception("No method with the name {}".format(name))


def demo():
    # Create acct
    addr, pk = get_accounts()[0]
    print("Using {}".format(addr))


    signer = AccountTransactionSigner(pk)

    c = get_contract_from_json() 

    # Create app
    first_app_id = create_app(addr, pk)
    print("Created App with id: {}".format(first_app_id))

    # Create app
    second_app_id = create_app(addr, pk)
    print("Created App with id: {}".format(second_app_id))

    sp = client.suggested_params()
    sp.fee = sp.min_fee*3
    sp.min_fee = sp.min_fee*3

    atc = AtomicTransactionComposer()
    atc.add_method_call(first_app_id, get_method(c, "call"), addr, sp, signer, method_args=[second_app_id])
    result = atc.execute(client, 4)
    print(result.abi_results[0].__dict__)


def create_app(addr, pk):
    # Get suggested params from network
    sp = client.suggested_params()

    # Read in approval teal source && compile
    app_result = client.compile(get_approval())
    app_bytes = base64.b64decode(app_result["result"])

    # Read in clear teal source && compile
    clear_result = client.compile(get_clear())
    clear_bytes = base64.b64decode(clear_result["result"])

    # We dont need no stinkin storage
    schema = StateSchema(0, 0)

    # Create the transaction
    create_txn = ApplicationCreateTxn(
        addr, sp, 0, app_bytes, clear_bytes, schema, schema
    )

    # Sign it
    signed_txn = create_txn.sign(pk)

    # Ship it
    txid = client.send_transaction(signed_txn)

    # Wait for the result so we can return the app id
    result = wait_for_confirmation(client, txid, 4)

    return result["application-index"]

def get_contract_from_json():
    with open("contract.json") as f:
        js = f.read()

    return Contract.from_json(js)

if __name__ == "__main__":
    demo()

