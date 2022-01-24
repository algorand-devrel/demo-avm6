from hashlib import sha256
from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
from sandbox import get_accounts
import base64

from app import get_approval, get_clear, get_reup


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
    try:
        # Create app
        app_id = create_app(addr, pk)
        app_addr = logic.get_application_address(app_id)
        print("Created App with id: {}".format(app_id))

        # set the fee to 2x min fee, this allows the inner app call to proceed even though the app address is not funded
        sp = client.suggested_params()
        ptxn = PaymentTxn(addr, sp, app_addr, int(1e9))

        actxns = []
        for i in range(14):
            actxn2 = ApplicationCallTxn(
                addr, sp, app_id, OnComplete.NoOpOC, note=str(i).encode()
            )
            actxn2.fee = actxn2.fee * 17
            actxns.append(actxn2)

        
        tohash = "compute"
        times = 3500

        actxn = ApplicationCallTxn(
            addr, sp, app_id, OnComplete.NoOpOC, app_args=[tohash, times]
        )
        actxn.fee = actxn.fee * 17

        stxns = [txn.sign(pk) for txn in assign_group_id([ptxn, *actxns, actxn])]
        ids = [s.transaction.get_txid() for s in stxns]

        # drr = create_dryrun(client, stxns)
        # with open("gasup.msgp", "wb") as f:
        #    f.write(base64.b64decode(encoding.msgpack_encode(drr)))

        hash = tohash.encode()
        for _ in range(times):
            hash = sha256(hash).digest()

        print("Hash should be: {}".format(hash.hex()))

        client.send_transactions(stxns)
        # doesnt work
        results = [wait_for_confirmation(client, id, 4) for id in ids]
        print("Got: ")
        print_logs_recursive(results)
    except Exception as e:
        print("Fail :( {}".format(e.with_traceback()))
    finally:
        delete_app(app_id, addr, pk)


def print_logs_recursive(results):
    for res in results:
        if "logs" in res:
            for l in [base64.b64decode(log) for log in res["logs"]]:
                print(l.hex()),
                #print(int(l.hex(), 16))
        if "inner-txns" in res:
            print_logs_recursive(res["inner-txns"])


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
    result = wait_for_confirmation(client, txid, 4)


def create_app(addr, pk):
    global reup_bytes
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
        addr,
        sp,
        0,
        app_bytes,
        clear_bytes,
        schema,
        schema,
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
