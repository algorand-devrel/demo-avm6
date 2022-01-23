import os

from pyteal import *
from pytealutils.inline import InlineAssembly
from pytealutils.strings import itoa, rest

# This may be provided as a constant in pyteal, for now just hardcode
prefix = Bytes("base16", "151f7c75")

iters =  570
reup_bytes = ""

@Subroutine(TealType.uint64)
def compute():
    """compute will do some interesting computery thing and gasup as needed"""
    i = ScratchVar()

    init = i.store(Int(0))
    cond = i.load() < Int(iters)
    iter = i.store(i.load() + Int(1))

    x = ScratchVar()

    return Seq(
        x.store(Int(0)),
        For(init, cond, iter).Do(
            Seq(
                x.store(x.load() + Int(10)),
                If(i.load() % Int(10) == Int(0), check_gasup(Int(250))),
            )
        ),
       Log(Itob(Global.opcode_budget())),
       # Log(Itob(x.load())),
        Int(1),
    )


@Subroutine(TealType.none)
def check_gasup(min: TealType.uint64):
    """check_gasup takes a min value, if the current opcode budget remaining is less than that, make app call to gas up"""
    return If(
        Global.opcode_budget() < min,
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.on_completion: OnComplete.DeleteApplication,
                    TxnField.approval_program: Bytes(reup_bytes),
                    TxnField.clear_state_program: Bytes(reup_bytes),
                    TxnField.fee: Int(0),
                }
            ),
            InnerTxnBuilder.Submit(),
            Log(Itob(Global.opcode_budget())),
        ),
    )


def approval():
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
        [Txn.on_completion() == OnComplete.NoOp, Return(compute())],
    )


def clear():
    return Approve()


def get_reup():
    return compileTeal(
        Txn.on_completion() == OnComplete.DeleteApplication,
        mode=Mode.Application,
        version=6,
    )


def get_approval(reup):
    global reup_bytes
    reup_bytes = reup

    return compileTeal(approval(), mode=Mode.Application, version=6)


def get_clear():
    return compileTeal(clear(), mode=Mode.Application, version=5)


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(get_approval())

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(get_clear())
