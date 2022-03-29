from warnings import catch_warnings
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
    # Create acct
    addr, pk = get_accounts()[0]
    print("Using {}".format(addr))

    # Read in the json contract description and create a Contract object
    c = get_contract_from_json()

    fund_proxy_app, funded_app_id = 0, 0

    try:
        # Create app
        fund_proxy_app = create_app(
            client, addr, pk, get_approval=get_approval, get_clear=get_clear
        )
        fund_app_addr = logic.get_application_address(fund_proxy_app)
        print(
            "Created Funding App with id: {} and address: {}".format(
                fund_proxy_app, fund_app_addr
            )
        )
        # get tx suggested params
        sp = client.suggested_params()

        # Fund to proxy app
        proxy_fund_tx = PaymentTxn(addr, sp, fund_app_addr, int(1e5))
        txid = client.send_transaction(proxy_fund_tx.sign(pk))
        wait_for_confirmation(client, txid, 1)

        # set the fee to 4x min fee, user will cover all fee
        sp.fee = sp.min_fee * 4

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

        app_create_txn = client.pending_transaction_info(result.tx_ids[0])
        app_fund_txn = client.pending_transaction_info(result.tx_ids[-1])

        funded_app_id = app_create_txn["application-index"]
        print("Created new application: {}".format(funded_app_id))
        print(
            "Funded app with inner transaction with inner transaction: {}".format(
                app_fund_txn["inner-txns"][0]["txn"]
            )
        )

    except Exception as e:
        print("Failzore: {}".format(e.with_traceback()))

    finally:
        delete_app(client, fund_proxy_app, addr, pk)
        print("Deleted {}".format(fund_proxy_app))
        delete_app(client, funded_app_id, addr, pk)
        print("Deleted {}".format(funded_app_id))


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
