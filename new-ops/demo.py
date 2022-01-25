from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
from sandbox import get_accounts
import base64

from app import get_approval, get_clear

client = algod.AlgodClient("a" * 64, "http://localhost:4001")


def get_method(c: Contract, name: str) -> Method:
    for m in c.methods:
        if m.name == name:
            return m
    raise Exception("No method with the name {}".format(name))


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
        app_id = create_app(addr, pk)
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
        delete_app(app_id, addr, pk)


def raise_rejected(txn):
    if "app-call-messages" in txn:
        if "REJECT" in txn["app-call-messages"]:
            print(txn)
            raise Exception(txn["app-call-messages"][-1])


def get_stats_from_dryrun(dryrun_result):
    logs, cost, trace_len = [], [], []
    for txn in dryrun_result["txns"]:
        raise_rejected(txn)
        if "logs" in txn:
            logs.extend([base64.b64decode(l).hex() for l in txn["logs"]])
        if "cost" in txn:
            cost.append(txn["cost"])
        if "app-call-trace" in txn:
            trace_len.append(len(txn["app-call-trace"]))
    return logs, cost, trace_len


def delete_app(app_id, addr, pk):
    # Get suggested params from network
    sp = client.suggested_params()

    # Create the transaction
    txn = ApplicationDeleteTxn(addr, sp, app_id)

    # sign it
    signed = txn.sign(pk)

    # Ship it
    txid = client.send_transaction(signed)

    # Wait for the result so we can return the app id
    return wait_for_confirmation(client, txid, 4)


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
