import os

from pyteal import *
from pytealutils.inline import InlineAssembly

prefix = Bytes("")

call_selector = MethodSignature("call(application)string")
echo_selector = MethodSignature("echo(uint64)string")


def caller():
    return InlineAssembly("global CallerApplicationID", type=TealType.uint64)
    

@Subroutine(TealType.uint64)
def call():
    app_ref = Btoi(Txn.application_args[1])

    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.ApplicationCall,
            TxnField.application_id: Txn.applications[app_ref],
            TxnField.application_args: [echo_selector]
        }),
        InnerTxnBuilder.Submit(),
        Txn.logs[0]
    )


def echo():
    return Concat(
        Bytes("In app id: "),
        Itob(Txn.application_id()),
        Bytes("Called by: "),
        Itob(caller()),
    )



@Subroutine(TealType.uint64)
def ret_log(value: TealType.bytes):
    return Seq(Log(Concat(prefix, value)), Int(1))


def approval():

    handlers= [
        [
            Txn.application_args[0] == call_selector,
            ret_log(call()),
        ],[
            Txn.application_args[0] == echo_selector,
            ret_log(echo()),
        ]
    ]

    return Cond(
        *handlers,
        [Txn.application_id() == Int(0), Approve()],
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
