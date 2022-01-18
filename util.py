from pyteal import (
    Int,
    Subroutine,
    TealType,
    Substring,
    Bytes,
    Len,
    Concat,
    If,
    GetByte,
    Exp,
)

ascii_offset = Int(48)  # Magic number to convert between ascii chars and integers


@Subroutine(TealType.uint64)
def ascii_to_int(arg: TealType.uint64):
    return arg - ascii_offset


@Subroutine(TealType.bytes)
def int_to_ascii(arg: TealType.uint64):
    # return arg + ascii_offset Just returns a uint64, cant convert to bytes type
    return Substring(Bytes("0123456789"), arg, arg + Int(1))


@Subroutine(TealType.uint64)
def atoi(a: TealType.bytes):
    return If(
        Len(a) > Int(0),
        (ascii_to_int(head(a)) * ilog10(Len(a) - Int(1)))
        + atoi(Substring(a, Int(1), Len(a))),
        Int(0),
    )


@Subroutine(TealType.bytes)
def itoa(i: TealType.uint64):
    return If(
        i == Int(0),
        Bytes("0"),
        Concat(
            If(i / Int(10) > Int(0), itoa(i / Int(10)), Bytes("")),
            int_to_ascii(i % Int(10)),
        ),
    )


@Subroutine(TealType.uint64)
def head(s: TealType.bytes):
    return GetByte(s, Int(0))


@Subroutine(TealType.bytes)
def tail(s: TealType.bytes):
    return Substring(s, Int(1), Len(s))


@Subroutine(TealType.bytes)
def suffix(a, len):
    return Substring(a, Len(a) - len, Len(a))


@Subroutine(TealType.uint64)
def ilog10(x: TealType.uint64):
    return Exp(Int(10), x)
