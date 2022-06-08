import os
import json

from pyteal import *

router = Router(
    "c2c",
    BareCallActions(
        no_op=OnCompleteAction.create_only(Approve()),
        clear_state=OnCompleteAction.never(),
        delete_application=OnCompleteAction.always(
            Return(Txn.sender() == Global.creator_address())
        ),
    ),
)

# This is called from the other application, just echos some stats
@router.method
def thing(
    axfer: abi.AssetTransferTransaction,
    app: abi.Application,
    val: abi.Uint64,
    acct: abi.Account,
    stuff: abi.Tuple2[abi.Address, abi.String],
    *,
    output: abi.String,
) -> Expr:
    """Super useless method"""
    return Seq(
        Assert(axfer.get().asset_receiver() == Global.current_application_address()),
        Assert(app.application_id() == Global.caller_app_id()),
        Assert(val.get()>Int(0)),
        Assert(acct.address() == Global.caller_app_address()),
        stuff[0].use(lambda a: Assert(Len(a.get())==Int(32))),
        output.set(
            Concat(
                Bytes("In app id "),
                Itob(Txn.application_id()),
                Bytes(" which was called by app id "),
                Itob(Global.caller_app_id()),
            )
        )
    )


## TODO: Make this better.
thingmethod = list(filter(lambda m: m.name == "thing", router.methods)).pop()
signature = thingmethod.get_signature()
selector = Bytes(thingmethod.get_selector())


@router.method
def bootstrap(asset: abi.Asset):
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset.asset_id(),
            TxnField.asset_amount: Int(0),
            TxnField.asset_receiver: Global.current_application_address(),
        }),
        InnerTxnBuilder.Submit()
    )

# This method is called from off chain, it dispatches a call to the first argument treated as an application id
@router.method
def call(axfer: abi.AssetTransferTransaction, asset: abi.Asset, app: abi.Application, app_acct: abi.Account, *, output: abi.String) -> Expr:
    return Seq(
        (val := abi.Uint64()).set(axfer.get().asset_amount()),
        (addr := abi.Address()).set(Txn.sender()),
        (s := abi.String()).set(Txn.note()),
        (stuff := abi.make(abi.Tuple2[abi.Address, abi.String])).set(addr, s),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.MethodCall(
            # App id
            app.application_id(),
            signature,
            [
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: asset.asset_id(),
                    TxnField.asset_amount: axfer.get().asset_amount(),
                    TxnField.asset_receiver: app_acct.address(),
                    TxnField.fee: Int(0),
                },
                Global.current_application_id(),
                val,
                Global.current_application_address(),
                stuff,
            ],
        ),
        InnerTxnBuilder.SetFields({TxnField.fee: Int(0)}),
        InnerTxnBuilder.Submit(),
        output.decode(Suffix(InnerTxn.last_log(), Int(4))),
    )


approval, clear, contract = router.compile_program(
    version=6, optimize=OptimizeOptions(scratch_slots=True)
)


def get_approval():
    return approval


def get_clear():
    return clear


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(approval)

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(clear)

    with open(os.path.join(path, "contract.json"), "w") as f:
        f.write(json.dumps(contract.dictify()))
