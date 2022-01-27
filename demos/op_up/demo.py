from hashlib import sha256
from webbrowser import get
from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
import base64

from .app import get_approval, get_clear, get_reup
from ..utils import get_accounts, create_app, delete_app


client = algod.AlgodClient("a" * 64, "http://localhost:4001")

def demo():
    # Create acct
    addr, pk = get_accounts()[1]
    print("Using {}".format(addr))

    # Read in the json contract description and create a Contract object
    try:
        # Create app
        app_id = create_app(client, addr, pk, get_approval=get_approval, get_clear=get_clear)
        app_addr = logic.get_application_address(app_id)
        print("Created App with id: {} and address {}".format(app_id, app_addr))

        # Create dummy app we just use to call against for more ops
        second_app = create_app(client, addr, pk, get_approval=get_reup, get_clear=get_clear)
        print("Created Reup App with id: {}".format(second_app))

        sp = client.suggested_params()

        # The string we want to hash a bunch
        tohash = "compute"
        # How many times to hash
        times = 3500

        actxn = ApplicationCallTxn(
            addr,
            sp,
            app_id,
            OnComplete.NoOpOC,
            app_args=[tohash, times],
            foreign_apps=[second_app],
        )

        # We call 256 inners but also need to pay for this 1 outer
        actxn.fee = actxn.fee * (256 + 1) 

        # Pay the app address so we can execute calls
        ptxn = PaymentTxn(addr, sp, app_addr, int(1e9))

        # Group and sign
        stxns = [txn.sign(pk) for txn in assign_group_id([ptxn, actxn])]
        ids = [s.transaction.get_txid() for s in stxns]

        # Ship it
        client.send_transactions(stxns)

        # Check locally to see what we expect
        hash = tohash.encode()
        for _ in range(times):
            hash = sha256(hash).digest()
        print("Hash should be: {}".format(hash.hex()))

        results = [wait_for_confirmation(client, id, 4) for id in ids]
        print("Got: {}".format(get_logs_recursive(results)[0]))
        
    except Exception as e:
        print("Fail :( {}".format(e.with_traceback()))
    finally:
        print("Cleaning up")
        delete_app(client, app_id, addr, pk)
        delete_app(client, second_app, addr, pk)


def get_logs_recursive(results):
    logs = []
    for res in results:
        if "logs" in res:
            for l in [base64.b64decode(log) for log in res["logs"]]:
                logs.append(l.hex())
        if "inner-txns" in res:
            logs.extend(get_logs_recursive(res["inner-txns"]))

    return logs


if __name__ == "__main__":
    demo()
