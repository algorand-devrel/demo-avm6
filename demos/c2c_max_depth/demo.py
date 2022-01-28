from concurrent.futures import wait
from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
import base64

from .app import get_approval, get_clear
from ..utils import get_accounts

client = algod.AlgodClient("a" * 64, "http://localhost:4001")


def demo():
    # Create acct
    addr, pk = get_accounts()[0]
    print("Using {}".format(addr))

    # Read in the json contract description and create a Contract object
    try:

        # Read in approval teal source && compile
        app_result = client.compile(get_approval())
        app_bytes = base64.b64decode(app_result["result"])

        # Read in clear teal source && compile
        clear_result = client.compile(get_clear())
        clear_bytes = base64.b64decode(clear_result["result"])

        # Get suggested params from network
        sp = client.suggested_params()

        schema = StateSchema(0, 0)
        create_txn = ApplicationCreateTxn(
            addr, sp, OnComplete.NoOpOC, app_bytes, clear_bytes, schema, schema
        ).sign(pk)

        # Ship it
        txid = client.send_transaction(create_txn)

        # Wait for the result so we can return the app id
        result = wait_for_confirmation(client, txid, 4)
        app_id = result["application-index"]
        app_addr = logic.get_application_address(app_id)

        depth = 8

        # Get suggested params from network
        sp = client.suggested_params()

        # Pay the app addr
        pay_txn = PaymentTxn(addr, sp, app_addr, int(1e9))

        # Call it
        call_txn = ApplicationCallTxn(
            addr, sp, app_id, OnComplete.DeleteApplicationOC, app_args=[depth]
        )

        # Cover $depth inner app creates, pays, calls + this call
        call_txn.fee *= (depth * 3) + 1

        stxn = [tx.sign(pk) for tx in assign_group_id([pay_txn, call_txn])]
        ids = [tx.get_txid() for tx in stxn]

        client.send_transactions(stxn)
        results = [wait_for_confirmation(client, txid, 2) for txid in ids]

        # Print the logs from all the inners
        print_logs_recursive(results)

    except Exception as e:
        print("Fail :( {}".format(e.with_traceback()))


def print_logs_recursive(results, nested_level: int = 0):
    for res in results:
        if "logs" in res:
            for l in [base64.b64decode(log) for log in res["logs"]]:
                print("At level {}: {}".format(nested_level, l.hex()))
        if "inner-txns" in res:
            print_logs_recursive(res["inner-txns"], nested_level + 1)


if __name__ == "__main__":
    demo()
