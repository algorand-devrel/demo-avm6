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
    # Create acct
    addr, pk = get_accounts()[0]
    print("Using {}".format(addr))

    # Read in the json contract description and create a Contract object
    c = get_contract_from_json()

    try:
        # Create app
        app_id = create_app(addr, pk)
        print("Created App with id: {}".format(app_id))

        signer = AccountTransactionSigner(pk)

        # set the fee to 2x min fee, this allows the inner app call to proceed even though the app address is not funded
        sp = client.suggested_params()
        # Create atc to handle method calling for us
        atc = AtomicTransactionComposer()
        # add a method call to "call" method, pass the second app id so we can dispatch a call
        atc.add_method_call(
            app_id, get_method(c, "acct_param"), addr, sp, signer, method_args=[addr]
        )

        result = atc.dryrun(client)

        for i, res in enumerate(result.abi_results):
            print(
                "Result of '{}': {} (cost {})".format(
                    atc.method_dict[i].name, res.return_value, res.cost
                )
            )

    finally:
        delete_app(app_id, addr, pk)


def raise_rejected(txn):
    if "app-call-messages" in txn:
        if "REJECT" in txn["app-call-messages"]:
            raise Exception(txn["app-call-messages"][-1])


def get_stats_from_dryrun(dryrun_result):
    logs, cost, trace_len = [], [], []
    txn = dryrun_result["txns"][0]
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
