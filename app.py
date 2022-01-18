import os

from pyteal import *
from pytealutils.inline import InlineAssembly
from pytealutils.strings import itoa, rest

prefix = Bytes("base16", "151f7c75")

call_selector = MethodSignature("call(application)string")
echo_selector = MethodSignature("echo(uint64)string")


def caller():
    return InlineAssembly("global CallerApplicationID", type=TealType.uint64)
    

@Subroutine(TealType.bytes)
def call():
    app_ref = Btoi(Txn.application_args[1])

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.ApplicationCall,
            TxnField.application_id: Txn.applications[app_ref],
            TxnField.application_args: [echo_selector],
            TxnField.fee: Int(0)
        }),
        InnerTxnBuilder.Submit(),
        rest(InnerTxn.logs[0], Int(6))
    )


@Subroutine(TealType.bytes)
def echo():
    return Concat(
        Bytes("In app id: "),
        itoa(Txn.application_id()),
        Bytes(" Called by: "),
        itoa(caller()),
    )



@Subroutine(TealType.bytes)
def string_encode(str: TealType.bytes):
    return Concat(Extract(Itob(Len(str)), Int(6), Int(2)), str)

@Subroutine(TealType.none)
def ret_log(value: TealType.bytes):
    return Log(Concat(prefix, string_encode(value)))


def approval():

    handlers= [
        [
            Txn.application_args[0] == call_selector,
            Return(Seq(ret_log(call()), Int(1))),
        ],[
            Txn.application_args[0] == echo_selector,
            Return(Seq(ret_log(echo()), Int(1))),
        ]
    ]

    return Cond(
        [Txn.application_id() == Int(0), Approve()],
        *handlers,
        [Txn.on_completion() == OnComplete.DeleteApplication, Reject()],
        [Txn.on_completion() == OnComplete.UpdateApplication, Reject()],
        [Txn.on_completion() == OnComplete.CloseOut, Approve()],
        [Txn.on_completion() == OnComplete.OptIn, Approve()],
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
