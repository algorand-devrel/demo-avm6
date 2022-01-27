from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
import base64

from .app import get_approval, get_clear
from ..utils import get_accounts, create_app, delete_app

client = algod.AlgodClient("a" * 64, "http://localhost:4001")


def demo():

    accts = get_accounts()

    addr, pk = accts[0]
    print("Using {}".format(addr))

    addr2, _ = accts[1]
    addr3, _ = accts[2]

    # Read in the json contract description and create a Contract object
    c = get_contract_from_json()

    try:
        # Create app
        app_id = create_app(
            client, addr, pk, get_approval=get_approval, get_clear=get_clear
        )
        app_addr = logic.get_application_address(app_id)
        print("Created App with id: {} and address: {}".format(app_id, app_addr))

        sp = client.suggested_params()

        paytxn = PaymentTxn(addr, sp, app_addr, 10000000)
        txid = client.send_transaction(paytxn.sign(pk))
        wait_for_confirmation(client, txid, 2)

        signer = AccountTransactionSigner(pk)

        # Create atc to handle method calling for us
        atc = AtomicTransactionComposer()
        # add a method call to "acct_param" method, pass the second account we want to get params for
        atc.add_method_call(
            app_id, get_method(c, "acct_param"), addr, sp, signer, method_args=[addr]
        )

        # add a method call to "bsqrt" method, pass a biggish number that gets encoded for us
        atc.add_method_call(
            app_id,
            get_method(c, "bsqrt"),
            addr,
            sp,
            signer,
            method_args=[int(1e6) ** 2],
        )

        # add a method call to "gitxn" method, pass a the accounts we want to pay and how much to pay them
        sp.fee = sp.min_fee * 3  # increase fee so we cover inners
        atc.add_method_call(
            app_id,
            get_method(c, "gitxn"),
            addr,
            sp,
            signer,
            method_args=[addr2, 10000, addr3, 20000],
        )

        result = atc.execute(client, 4)
        for res in result.abi_results:
            print(res.return_value)

    finally:
        delete_app(client, app_id, addr, pk)


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
