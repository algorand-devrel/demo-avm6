import os

# WARNING: This code has not been audited
# DO NOT USE IN PRODUCTION

from pyteal import *


@Subroutine(TealType.bytes)
def eth_ecdsa_recover(hash_value, signature):
    """
    Equivalent of OpenZeppelin ECDSA.recover for long 65-byte Ethereum signatures
    https://docs.openzeppelin.com/contracts/2.x/api/cryptography#ECDSA-recover-bytes32-bytes-
    Short 64-byte Ethereum signatures require some changes to the code

    Return a 20-byte Ethereum address

    Note: Unless compatibility with Ethereum or another system is necessary, we highly recommend using
    ed25519_verify instead of ecdsa on Algorand

    WARNING: This code has NOT been audited
    DO NOT USE IN PRODUCTION
    """
    opup = OpUp(OpUpMode.OnCall)  # we need more budget to be able to run

    r = Extract(signature, Int(0), Int(32))
    s = Extract(signature, Int(32), Int(32))
    # The recovery ID is shifted by 27 on Ethereum
    # For non-Ethereum signatures, remove the -27 on the line below
    v = Btoi(Extract(signature, Int(64), Int(1))) - Int(27)

    return Seq(
        Assert(Len(signature) == Int(65)),
        Assert(Len(hash_value) == Int(32)),
        opup.ensure_budget(Int(2500)),  # need 2000 for EcdsaRecover, adding a bit more for margin
        # The following two asserts are to prevent malleability
        # like in
        # https://github.com/OpenZeppelin/openzeppelin-contracts/blob/5fbf494511fd522b931f7f92e2df87d671ea8b0b/contracts/utils/cryptography/ECDSA.sol#L153
        Assert(BytesLe(s, Bytes("base16", "0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0"))),
        Assert(Or(v == Int(0), v == Int(1))),
        EcdsaRecover(EcdsaCurve.Secp256k1, hash_value, v, r, s).outputReducer(
            # Ethereum concatenate the x and y part of the public key
            # and then applies Keccak256 and take the last 20 bytes
            lambda x, y: Extract(Keccak256(Concat(x, y)), Int(12), Int(20))
        )
    )


def approval():
    """
    This smart contract, once created, has a single non-ABI-compliant noop method call
    that takes two application arguments:
      hash, signature
    and logs the result of the function ECDSA.recover(hash, signature)
    as written in OpenZeppelin
        https://docs.openzeppelin.com/contracts/2.x/api/cryptography#ECDSA-recover-bytes32-bytes-
    (65-byte signatures only)
    """
    return Cond(
        [Txn.application_id() == Int(0), Approve()],
        [
            Txn.on_completion() == OnComplete.DeleteApplication,
            Return(Txn.sender() == Global.creator_address()),
        ],
        [
            Txn.on_completion() == OnComplete.UpdateApplication,
            Return(Txn.sender() == Global.creator_address()),
        ],
        [Txn.on_completion() == OnComplete.CloseOut, Approve()],
        [Txn.on_completion() == OnComplete.OptIn, Approve()],
        [
            Txn.on_completion() == OnComplete.NoOp,
            Seq(
                Log(eth_ecdsa_recover(Txn.application_args[0], Txn.application_args[1])),
                Approve()
            )
        ],
    )


def clear():
    return Approve()


def get_approval():
    return compileTeal(approval(), mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(clear(), mode=Mode.Application, version=6)


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(get_approval())

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(get_clear())
