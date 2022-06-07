import os
import json

from pyteal import *

router = Router(
    "c2c",
    BareCallActions(
        no_op=OnCompleteAction.create_only(Approve()),
        clear_state=OnCompleteAction.always(Reject()),
        delete_application=OnCompleteAction.always(
            Return(Txn.sender() == Global.creator_address())
        ),
    ),
)

# This is called from the other application, just echos some stats
@router.method
def echo(*, output: abi.String) -> Expr:
    """Echo echos out blah"""
    return output.set(
        Concat(
            Bytes("In app id "),
            Itob(Txn.application_id()),
            Bytes(" which was called by app id "),
            Itob(Global.caller_app_id()),
        )
    )


# TODO: Ben can change this. Make it better.
emeth = list(filter(lambda m: m.name == "echo", router.methods))
selector = Bytes(emeth[0].get_selector())

# This method is called from off chain, it dispatches a call to the first argument treated as an application id
@router.method
def call(app: abi.Application, *, output: abi.String) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                # access the actual id specified by the 2nd app arg
                TxnField.application_id: app.deref(),
                # Pass the selector as the first arg to trigger the `echo` method
                TxnField.application_args: [selector],
                # Set fee to 0 so caller has to cover it
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        (s := abi.String()).decode(
            Suffix(
                # Get the 'return value' from the logs of the last inner txn
                InnerTxn.logs[0],
                Int(
                    4
                ),  # TODO: last_log should give us the real last logged message, not in pyteal yet
            ),  # Trim off return (4 bytes) Trim off string length (2 bytes)
        ),
        output.set(s),
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
