import os

from pyteal import *
from pytealutils.inline import InlineAssembly
from pytealutils.strings import itoa, rest

# This may be provided as a constant in pyteal, for now just hardcode
prefix = Bytes("base16", "151f7c75")

iters = 15
reup_bytes = ""


@Subroutine(TealType.uint64)
def compute():
    """compute will use the large opcode budget to do something cool, idk what tho"""
    return Seq(
        Pop(max_gas()),
        # Do something interesting with the thicc budget
        # should be >173k ops available if we called with 15 total app call txns that all gassed up
        Log(Itob(Global.opcode_budget())),
        Int(1),
    )


@Subroutine(TealType.uint64)
def max_gas():
    """Call gasup the max number of times for a single application"""
    return Seq(
        InnerTxnBuilder.Begin(),
        *[Seq(gasup_txn(), InnerTxnBuilder.Next()) for _ in range(15)],
        gasup_txn(),
        InnerTxnBuilder.Submit(),
        Int(1)
    )


@Subroutine(TealType.none)
def gasup_txn():
    return InnerTxnBuilder.SetFields(
        {
            TxnField.type_enum: TxnType.ApplicationCall,
            TxnField.on_completion: OnComplete.DeleteApplication,
            TxnField.approval_program: Bytes(reup_bytes),
            TxnField.clear_state_program: Bytes(reup_bytes),
            TxnField.fee: Int(0),
        }
    )


@Subroutine(TealType.none)
def check_gasup(min: TealType.uint64):
    """check_gasup takes a min value, if the current opcode budget remaining is less than that, make app call to gas up"""
    return If(
        Global.opcode_budget() < min,
        Seq(InnerTxnBuilder.Begin(), gasup_txn(), InnerTxnBuilder.Submit()),
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
        [
            Txn.on_completion() == OnComplete.NoOp,
            Return(If(Txn.application_args.length() > Int(0), compute(), max_gas())),
        ],
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

    with open(os.path.join(path, "reup.teal"), "w") as f:
        f.write(get_reup())
