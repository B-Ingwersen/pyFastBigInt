# Overview
This is a small python library (really just a file to copy/paste) for making division, base10 string conversion, and integer square root faster for large integers (10000+ digits). The main advantage of this library is that it is written in pure python (no other packages required, no extra C code behind the scenes). **If you need actual high performance big integer computations, use a real optimized library (e.g. `gmpy2`) instead!!!** However, if you need an quick dirty way to speed up some big int operations in python, here you go:

Python Operation | pyFastBigInt equivalent | Approximate speedup for 1 million digit int
---|---|---
`divmod` | `fastBigIntDivMod` | ~10x
`str` | `fastBigIntStrBase10` | ~10x
`math.isqrt` | `fastBigIntFloorSqrt` | ~5x

For small integers, the builtin python methods will be faster as they call straight into the C implementations of these operations. The python versions have complexity O(n^2), however, whereas pyFastBigInt implementations match the complexity of python's integer multiplication, which is O(n^(3/2)) on CPython as of this writing, and therefore run asymptotically for large integers. Again, dedicated libraries like GMP use better algorithms and optimization and run much much faster.

# Background

Python's big integers are honestly pretty great; ints will pretty seamlessly change internal representations once they exceed the processor word size, and you as a programmer never have to worry about it. However, the python interpreter was not intended to be a high performance big integer library, and understandably the CPython implementation favors simplicity and correctness over heavy optimization.

CPython's addition and subtraction are pretty fast as there are pretty limited ways to optimize them, and their time complexity scales linearly anyway. Multiplication actually uses the Karatsuba algorithm for large integers as it's fairly simple to implement and improves time complexity to O(n^(3/2)) instead of the naive O(n^2) schoolbook method (note there are algorithms with much better asmyptotic behavior, but they are also significantly more complex to implement). The real wart in python's big int functions is division; the implementation used is O(n^2), which really blows up for big integers. Other functions that can be implemented with division, namely base 10 conversion (which happens every time you need to `repr` or `str` an int) and integer square root, also share this quadratic time complexity. To see the relative time of operaitons try this in a python REPL:

```
a = 10**4000000     # probably takes a second
b = a + a           # happens almost instantly
c = a * a           # takes a few seconds
d = str(a)          # grab some popcorn...
```

# How pyFastBigInt Works

The library is really just an optimized division/modulo function with the other functions built on top of it. A big integer division is broken down into 2 half sized divisions and 2 half sized multiplications; the end result is that a division takes about twice as long as an equivalently sized multiplication, but has the same O(n^(3/2)) time complexity. Base 10 string conversion boils down to a bunch of divisions by powers of 10, and the square root function uses Newton's method (where the bottleneck operation is again division). For an in-depth overview of how each function works, check out the comments in the source code (it's not that complicated; the entire file is a bit over 300 lines with comments). For relatively small inputs (less than 10000 to 20000 binary digits depending on the function) the code will just bail out and use the builtin python version. The performance for small values is a bit worse than the builtin python code due to interpreter overhead, and the type/value checking that must be performed in python instead of being baked into the interpreter.

# Performance

Run the test script `test.py` to see how well pyFastBigInt performs on your system. Below are some results from a mid-range laptop running python 3.10:

## **`divmod(num,den)` vs `pyFastBigInt.fastBigIntDivMod(num,den)`:**
| num.bit_length()      | den.bit_length()      | builtin time (s)      | pyFastBigInt time (s) |
|-----------------------|-----------------------|-----------------------|-----------------------|
|                  9143 |                  4570 |           0.000045538 |           0.000042677 |
|                 18285 |                  9140 |           0.000149727 |           0.000151157 |
|                 36569 |                 18279 |           0.000580311 |           0.000468969 |
|                 73137 |                 36557 |           0.002404451 |           0.001362801 |
|                146273 |                 73113 |           0.008540869 |           0.003398895 |
|                292546 |                146225 |           0.037352800 |           0.009331942 |
|                585091 |                292449 |           0.126118422 |           0.027524471 |
|               1170182 |                584897 |           0.499316692 |           0.068757534 |
|               2340364 |               1169794 |           2.001011133 |           0.200214624 |
|               4680727 |               2339587 |           8.000934124 |           0.596878767 |

## **`str(val)` vs `pyFastBigInt.fastBigIntStrBase10(val)`**:
| val.bit_length()      | builtin time (s)      | pyFastBigInt time (s) |
|-----------------------|-----------------------|-----------------------|
|                  9143 |           0.000118494 |           0.000303984 |
|                 18285 |           0.000587940 |           0.000856876 |
|                 36569 |           0.001779795 |           0.002362728 |
|                 73137 |           0.007544518 |           0.004445076 |
|                146273 |           0.030168295 |           0.010666847 |
|                292546 |           0.104351044 |           0.027253866 |
|                585091 |           0.407540083 |           0.076032877 |
|               1170182 |           1.640812159 |           0.219280481 |
|               2340364 |           6.446513176 |           0.644243956 |
|               4680727 |          25.845999002 |           1.860534430 |

## **`math.isqrt(val)` vs `pyFastBigInt.fastBigIntFloorSqrt(val)`**:

| val.bit_length()      | builtin time (s)      | pyFastBigInt time (s) |
|-----------------------|-----------------------|-----------------------|
|                  3403 |           0.000015259 |           0.000035524 |
|                  6805 |           0.000041962 |           0.000083208 |
|                 13608 |           0.000112295 |           0.000200987 |
|                 27215 |           0.000368118 |           0.000551462 |
|                 54428 |           0.001168728 |           0.001153946 |
|                108854 |           0.003855944 |           0.003254175 |
|                217707 |           0.015810013 |           0.011430979 |
|                435413 |           0.064618349 |           0.025315523 |
|                870825 |           0.203779936 |           0.070108891 |
|               1741649 |           0.783149481 |           0.208540201 |
|               3483296 |           3.098951817 |           0.609769583 |
|               6966590 |          12.219447136 |           1.806480169 |

