from pyFastBigInt import (
    fastBigIntDivMod,
    fastBigIntStrBase10,
    fastBigIntFloorSqrt
)
import time
import math # for math.isqrt

def tblPrintRow(elems, ljust=False, width=20):
    row = '|'
    for elem in elems:
        if isinstance(elem, float):
            elem = "{:.9f}".format(elem)
        else:
            elem = str(elem)

        if ljust:
            elem = elem.ljust(width-3)
        else:
            elem = elem.rjust(width-3)
        
        row += ' ' + elem + ' '
        row += '|'
    
    print(row)

def tblPrintDivider(nElems, width=20):
    print(('|' + '-' * (width-1)) * nElems + '|')

def divModTest():
    print("divmod(num,den) vs pyFastBigInt.fastBigIntDivMod(num,den):")
    print()
    tblPrintRow(["num.bit_length()", "den.bit_length()", "builtin time (s)",
        "pyFastBigInt time (s)"], ljust=True, width=24)
    tblPrintDivider(4, 24)

    for i in range(10, 20):
        num = 487**(2**i)
        den = 486**(2**(i-1))

        start = time.time()
        builtinQuotient, builtinRemainder = divmod(num, den)
        end = time.time()
        builtinTime = end - start

        start = time.time()
        customQuotient, customRemainder = fastBigIntDivMod(num, den)
        end = time.time()
        customTime = end - start

        assert(builtinQuotient == customQuotient)
        assert(builtinRemainder == customRemainder)

        tblPrintRow([num.bit_length(), den.bit_length(), builtinTime, customTime],
            width=24)

    print()

def strTest():
    print("str(val) vs pyFastBigInt.fastBigIntStrBase10(val):")
    print()
    tblPrintRow(["val.bit_length()", "builtin time (s)",
        "pyFastBigInt time (s)"], ljust=True, width=24)
    tblPrintDivider(3, 24)

    for i in range(10, 20):
        val = 487**(2**i)

        start = time.time()
        builtinStr = str(val)
        end = time.time()
        builtinTime = end - start

        start = time.time()
        customStr = fastBigIntStrBase10(val)
        end = time.time()
        customTime = end - start

        assert(builtinStr == customStr)

        tblPrintRow([val.bit_length(), builtinTime, customTime], width=24)

    print()

def sqrtTest():
    print("math.isqrt(val) vs pyFastBigInt.fastBigIntFloorSqrt(val):")
    print()
    tblPrintRow(["val.bit_length()", "builtin time (s)",
        "pyFastBigInt time (s)"], ljust=True, width=24)
    tblPrintDivider(3, 24)

    for i in range(10, 22):
        val = 2*(10**(2**i))

        start = time.time()
        builtinSqrt = math.isqrt(val)
        end = time.time()
        builtinTime = end-start

        start = time.time()
        customSqrt = fastBigIntFloorSqrt(val)
        end = time.time()
        customTime = end-start

        assert(builtinSqrt == customSqrt)
    
        tblPrintRow([val.bit_length(), builtinTime, customTime], width=24)

    print()

divModTest()
strTest()
sqrtTest()
