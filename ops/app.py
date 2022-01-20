import os
from pyteal import *
from pytealutils.strings import itoa

# This may be provided as a constant in pyteal, for now just hardcode
prefix = Bytes("base16", "151f7c75")

acct_param_selector = MethodSignature("acct_param(account)string")
budget_pad_selector = MethodSignature("pad()void")


@Subroutine(TealType.none)
def doit():

    # gitxn t f	        : field F of the Tth transaction in the last inner group submitted
    # gitxna t f i      : Ith value of the array field F from the Tth transaction in the last inner group submitted
    # gloadss	        : Bth scratch space value of the Ath transaction in the current group

    pass


@Subroutine(TealType.none)
def acct_param():
    # acct_params_get   : get AcctBalance, AcctMinBalance, AcctAuthAddr for a given account
    acct_ref = Btoi(Txn.application_args[1])
    return ret_log(
        Seq(
            aa := AccountParam.authAddr(acct_ref),
            mb := AccountParam.minBalance(acct_ref),
            b := AccountParam.balance(acct_ref),
            Concat(
                Bytes("Auth addr: '"),
                If(aa.hasValue(), aa.value(), Bytes("<None>")),
                Bytes("', Min balance: "),
                itoa(If(mb.hasValue(), mb.value() / Int(1000000), Int(0))),
                Bytes(", Balance: "),
                itoa(If(b.hasValue(), b.value() / Int(1000000), Int(0))),
            ),
        )
    )


# @Subroutine(TealType.none)
# def bsqrt():
#    # bsqrt             : The largest integer I such that I^2 <= A. A and I are interpreted as big-endian unsigned integers
#
#    pass

# Util to add length to string to make it abi compliant, will have better interface in pyteal
@Subroutine(TealType.bytes)
def string_encode(str: TealType.bytes):
    return Concat(Extract(Itob(Len(str)), Int(6), Int(2)), str)


# Util to log bytes with return prefix
@Subroutine(TealType.none)
def ret_log(value: TealType.bytes):
    return Log(Concat(prefix, string_encode(value)))


def approval():
    # Define our abi handlers, route based on method selector defined above
    handlers = [
        [
            Txn.application_args[0] == acct_param_selector,
            Return(Seq(acct_param(), Int(1))),
        ],
        [
            Txn.application_args[0] == budget_pad_selector,
            Approve(),
        ],
    ]

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
        *handlers,
    )


def clear():
    return Return(Int(1))


def get_approval():
    return compileTeal(approval(), mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(clear(), mode=Mode.Application, version=5)


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(get_approval())

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(get_clear())
