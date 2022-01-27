from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *

from .app import get_approval, get_clear
from ..utils import get_accounts, create_app, delete_app

client = algod.AlgodClient("a" * 64, "http://localhost:4001")

def demo():
    # Create acct
    addr, pk = get_accounts()[0]
    print("Using {}".format(addr))

    # Read in the json contract description and create a Contract object
    c = get_contract_from_json()

    try:
        # Create app
        first_app_id = create_app(client, addr, pk, get_approval=get_approval, get_clear=get_clear)
        print("Created App with id: {}".format(first_app_id))

        # Create app
        second_app_id = create_app(client, addr, pk, get_approval=get_approval, get_clear=get_clear)
        print("Created App with id: {}".format(second_app_id))

        signer = AccountTransactionSigner(pk)

        # set the fee to 2x min fee, this allows the inner app call to proceed even though the app address is not funded
        sp = client.suggested_params()
        sp.fee = sp.min_fee * 2

        # Create atc to handle method calling for us
        atc = AtomicTransactionComposer()
        # add a method call to "call" method, pass the second app id so we can dispatch a call
        atc.add_method_call(
            first_app_id,
            get_method(c, "call"),
            addr,
            sp,
            signer,
            method_args=[second_app_id],
        )
        # run the transaction and wait for the restuls
        result = atc.execute(client, 4)

        # Print out the result
        print(
            """Result of inner app call: 
        {}""".format(
                result.abi_results[0].return_value
            )
        )
    except Exception as e:
        print("Fail :( {}".format(e.with_traceback()))
    finally:
        delete_app(client, first_app_id, addr, pk)
        delete_app(client, second_app_id, addr, pk)


def get_method(c: Contract, name: str) -> Method:
    for m in c.methods:
        if m.name == name:
            return m
    raise Exception("No method with the name {}".format(name))

def get_contract_from_json():
    import os

    path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(path, "contract.json")) as f:
        js = f.read()

    return Contract.from_json(js)


if __name__ == "__main__":
    demo()
