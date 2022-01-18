import os

from pyteal import *
from pytealutils.inline import InlineAssembly
from pytealutils.strings import itoa, rest

# This may be provided as a constant in pyteal, for now just hardcode
prefix = Bytes("base16", "151f7c75")

fund_selector = MethodSignature("fund()void")

# This method is called from off chain, it dispatches a call to the first argument treated as an application id
@Subroutine(TealType.none)
def fund():
    app_create, pay, pay_proxy = Gtxn[0], Gtxn[1], Gtxn[2]
    well_formed_fund = And(
        Global.group_size() == Int(3),

        app_create.type_enum() == TxnType.ApplicationCall,
        app_create.on_completion() == OnComplete.NoOp,
        app_create.application_id() == Int(0),

        pay.type_enum() == TxnType.Payment,
        pay.amount() > Int(100000), # min bal of 0.1A
        pay.close_remainder_to() == Global.zero_address(),

        pay_proxy.type_enum() == TxnType.ApplicationCall,
        pay_proxy.on_completion() == OnComplete.NoOp,
        pay_proxy.application_id() == Global.current_application_id()
    )

    created_addr = Sha512_256(Concat(Bytes("appID"), Itob(app_create.created_application_id())))

    return Seq(
        Assert(well_formed_fund),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.amount: pay.amount(),
            TxnField.receiver: created_addr,
            TxnField.fee: Int(0) # make caller pay
        }),
        InnerTxnBuilder.Submit(),
    )


def approval():
    # Define our abi handlers, route based on method selector defined above
    handlers= [
        [
            Txn.application_args[0] == fund_selector,
            Return(Seq(fund(), Int(1))),
        ]
    ]

    return Cond(
        [Txn.application_id() == Int(0), Approve()],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Txn.sender() == Global.creator_address())],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Txn.sender() == Global.creator_address())],
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
