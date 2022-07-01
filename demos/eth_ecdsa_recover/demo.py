import sys
import traceback
import base64

from Cryptodome.Hash import keccak
from algosdk.future.transaction import *

from .app import get_approval, get_clear
from ..utils import get_accounts, create_app, delete_app

client = algod.AlgodClient("a" * 64, "http://localhost:4001")


def call_application_eth_ecdsa_recover(
        acct: tuple[any, str], app_id: int, message: bytes, signature: bytes
) -> bytes:
    """
    Call the application with hash, signature
    See comment of app.approval() to see what it does
    hash is Keccak256(message)
    """
    addr, pk = acct

    m = keccak.new(digest_bits=256)
    m.update(message)
    hash = m.digest()

    sp = client.suggested_params()

    actxn = ApplicationCallTxn(
        addr,
        sp,
        app_id,
        OnComplete.NoOpOC,
        app_args=[hash, signature]
    )

    # We increase the fee due to the opup mechanism
    # https://pyteal.readthedocs.io/en/stable/opup.html
    # the choice of the fee is hihgly non-optimal
    # The reader is tasked to figure out the right fee
    actxn.fee = actxn.fee * (256 + 1)

    # Group and sign
    stxn = actxn.sign(pk)
    txid = stxn.transaction.get_txid()

    # Ship it
    client.send_transaction(stxn)

    # Get back the logs
    results = [wait_for_confirmation(client, txid, 4)]
    return get_logs_recursive(results)[0]


def test_application_eth_ecdsa_recover(
        acct: tuple[any, str], app_id: int, message: bytes, signature: str, signer: str
):
    """
    Test the application app_id on a given message, signature, signer
    Check the logged value by the application matches the signer
    """
    addr = call_application_eth_ecdsa_recover(
        acct,
        app_id,
        message,
        bytes.fromhex(signature)
    )
    print("Address recovered (without checksum): {}".format(addr.hex()))
    print("Address expected  (with checksum):    {}".format(signer))
    if signer.lower() == addr.hex():  # need to lowercase to remove checksum
        print("  Success")
    else:
        print("  Fail")
    print()
    return addr


def demo():
    # Create acct
    acct = get_accounts()[1]
    addr, pk = acct
    print("Using account {}".format(addr))

    # Read in the json contract description and create a Contract object
    try:
        # Create app
        app_id = create_app(
            client, addr, pk, get_approval=get_approval, get_clear=get_clear
        )
        app_addr = logic.get_application_address(app_id)
        print("Created App with id: {} and address {}".format(app_id, app_addr))

        # Pay the app address so we can execute calls
        sp = client.suggested_params()
        ptxn = PaymentTxn(addr, sp, app_addr, int(1e9))
        stxn = ptxn.sign(pk)
        client.send_transaction(stxn)

        # Normally here we'd like to wait for this transaciton to take place
        # However, in a sandbox environment, this is not necessary
        # so we cheat to go faster
        # In real life, uncomment the two lines below

        # txid = stxn.transaction.get_txid()
        # wait_for_confirmation(client, txid, 4)

        # Now making the real calls

        # The hash and signature we want to check
        # taken directly from
        # https://github.com/OpenZeppelin/openzeppelin-contracts/blob/faf5820f0331c59c93b0dca3e08f3456c94d8982/test/utils/cryptography/ECDSA.test.js#L111

        # First one is v0 (recovery ID = 0/27)
        message = b"OpenZeppelin"
        signature = "5d99b6f7f6d1f73d1a26497f2b1c89b24c0993913f86e9a2d02cd69887d9c94f3c880358579d811b21dd1b7fd9bb01c1d81d10e69f0384e675c32b39643be8921b"
        signer = "2cc1166f6212628A0deEf2B33BEFB2187D35b86c"
        test_application_eth_ecdsa_recover(acct, app_id, message, signature, signer)

        # Second one is v1 (recovery ID = 1/28)
        message = b"OpenZeppelin"
        signature = "331fe75a821c982f9127538858900d87d3ec1f9f737338ad67cad133fa48feff48e6fa0c18abc62e42820f05943e47af3e9fbe306ce74d64094bdf1691ee53e01c"
        signer = "1E318623aB09Fe6de3C9b8672098464Aeda9100E"
        test_application_eth_ecdsa_recover(acct, app_id, message, signature, signer)

    except:
        print("Fail :(\n", file=sys.stderr)
        traceback.print_exc()
    finally:
        print("Cleaning up")
        delete_app(client, app_id, addr, pk)


def get_logs_recursive(results: list[any]):
    logs = []
    for res in results:
        if "logs" in res:
            for l in [base64.b64decode(log) for log in res["logs"]]:
                logs.append(l)
        if "inner-txns" in res:
            logs.extend(get_logs_recursive(res["inner-txns"]))

    return logs


if __name__ == "__main__":
    demo()
