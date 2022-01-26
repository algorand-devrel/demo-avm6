from warnings import catch_warnings
from algosdk import *
from algosdk.atomic_transaction_composer import *
from algosdk.abi import *
from algosdk.v2client import algod
from algosdk.future.transaction import *
import base64

from .app import get_approval, get_clear
from ..utils import get_accounts

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

    fund_proxy_app, funded_app_id = 0, 0

    try:
        # Create app
        fund_proxy_app = create_app(addr, pk)
        fund_app_addr = logic.get_application_address(fund_proxy_app)
        print("Created Funding App with id: {} and address: {}".format(fund_proxy_app, fund_app_addr))


        # set the fee to 2x min fee, this allows the inner app call to proceed even though the app address is not funded
        sp = client.suggested_params()
        sp.fee = sp.min_fee * 2

        # Create atc to handle method calling for us
        atc = AtomicTransactionComposer()

        signer = AccountTransactionSigner(pk)
        # Get app create for app we want to make
        atc.add_transaction(TransactionWithSigner(get_app_create_txn(addr), signer))
        # Add payment to pre-created app
        atc.add_transaction(
            TransactionWithSigner(PaymentTxn(addr, sp, fund_app_addr, int(1e8)), signer)
        )
        # add a method call to "fund" method
        atc.add_method_call(fund_proxy_app, get_method(c, "fund"), addr, sp, signer)

        # run the transaction and wait for the restuls
        result = atc.execute(client, 4)
        print(result)

        funded_app_id = client.pending_transaction_info(result.tx_ids[0])[
            "application-index"
        ]
        print("Created new application: {}".format(funded_app_id))
        print(
            "Funded it with inner transaction: {}".format(
                client.pending_transaction_info(result.tx_ids[-1])["inner-txns"][0][
                    "txn"
                ]
            )
        )
    except Exception as e:
        print("Failzore: {}".format(e.with_traceback()))
    finally:
        delete_app(fund_proxy_app, addr, pk)
        print("Deleted {}".format(fund_proxy_app))
        delete_app(funded_app_id, addr, pk)
        print("Deleted {}".format(funded_app_id))


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


def get_app_create_txn(addr):
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
    return ApplicationCreateTxn(addr, sp, 0, app_bytes, clear_bytes, schema, schema)


def create_app(addr, pk):
    # Get create transaction
    create_txn = get_app_create_txn(addr)

    # Sign it
    signed_txn = create_txn.sign(pk)

    # Ship it
    txid = client.send_transaction(signed_txn)

    # Wait for the result so we can return the app id
    result = wait_for_confirmation(client, txid, 4)

    return result["application-index"]


def get_contract_from_json():
    import os
    path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(path, "contract.json")) as f:
        js = f.read()

    return Contract.from_json(js)


if __name__ == "__main__":
    demo()
