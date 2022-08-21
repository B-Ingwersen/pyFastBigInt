def fastBigIntDivMod(m, n):
    '''compute the quotient and module of m by n; functionally equivalent to the
    python divmod function for integer arguments, but internally uses more
    optimized division techniques for large integers. This is the "public"
    version of the function that performs type checking and handles the sign of
    the arguments; _divModPositiveArgs contains the core implementation'''

    if not isinstance(m, int) or not isinstance(n, int):
        raise TypeError("fastBigIntDivMod expected int arguments")
    
    q,r = _divModPositiveArgs(abs(m), abs(n))
    if m > 0 and n > 0:
        return q,r
    elif m < 0 and n < 0:
        return q,-r
    elif r == 0:
        return -q,r
    
    q = -(q + 1)
    if m > 0:
        return q,n+r
    else:
        return q,n-r

def fastBigIntStrBase10(n):
    '''Convert an integer to a base 10 string; functionally equivalent to
    calling str on an integer, but internally uses the fast divmod function to
    accelerate the conversion; this is the outer function that handles the sign
    of the argument and typechecking; the core logic is wrapped inside the call
    to _toBase10StringHelper'''

    if not isinstance(n, int):
        raise TypeError(f"fastBigIntStrBase10 expected int argument")

    if n == 0:
        return '0'
    elif n < 0:
        return '-' + fastBigIntStrBase10(-n)

    # generate a list of 10 ** (2*n) to use as divisors
    powers = [10]
    while powers[-1].bit_length() * 2 < n.bit_length():
        powers.append(powers[-1]*powers[-1])
    
    # perform the conversion and strip leading zeros
    chars = _toBase10StringHelper(n, powers, len(powers))
    for i,c in enumerate(chars):
        if c != '0':
            break
    
    return chars[i:]

def fastBigIntFloorSqrt(n):
    '''Compute the floor of the square root of n; this function performs input
    checking and then calls _floorSqrtPositiveInt which implements the core
    logic'''

    if not isinstance(n, int):
        raise TypeError(f"fastBigIntFloorSqrt expected int argument")
    if n < 0:
        raise ValueError(f"fastBigIntFloorSqrt domain error (less than zero)")

    return _floorSqrtPositiveInt(n)

def _divModPositiveArgs(m, n):
    '''The core function division/modulo; this assumes positive arguments, so use the top
    level fastBigIntDivMod for general purpose use.
    
    This function is deisgned to be optimal for m.bit_length() == 2 * n.bit_length(); if that
    is not the case, then it will pull off enough bits from the front of the operands to make
    that the case, estimate the result, correct, and iterate through more steps if needed.
    
    In the optimal case, if we let K=n.bit_length() and m.bit_length()==2*K, then the division
    is reduced into 2 K by (K/2) divisions and 2 (K/2) by (K/2) multiplications; while this
    appears to be quadratic it isn't necessarily - it depends on the complexity of the multiplication:
        
        For quadratic multiplication, division is quadratic and (2*K) by K division takes the same
        amount of time as a K by K multiplication
        
        For karatsuba multiplication (O(n^(3/2))) division is also (O(n^(3/2))), but a (2*K) by K
        division takes twice as long as a K by K multiplication
        
        For (O(n^N)) multiplication, division is also (O(n^N)), and a (2*K) by K division is
        1/(N-1) times as long as a K by K multiplication
    
    As you can see, the more efficient the multiplication algorithm, the more efficent the division,
    but the longer the division takes relative to the multiplication. Since python uses Karatsuba
    multiplication for large numbers, the acheived efficiency will be the 2nd case above (O(n^(3/2))).
    The native (and naive) python3 division algorithm for large integers is O(n^2), so this is a
    nice little improvement, and it shows for very large integers. However, this is still a lot
    worse than a dedicated big number library (i.e. GMP).
    
    For small values of n (currently less than 10000 bits) this function bails out to use the
    native python divmod method as the speed of native code will outpace the algorithmic benefits.
    '''
    
    m_len = m.bit_length()
    n_len = n.bit_length()

    if n.bit_length() < 10000:
        # bailout to native case
        
        return divmod(m, n)
    
    elif m_len < n_len:
        # If m has smaller log2 magnitude than n, we know m < n so we automatically
        # know that m // n == 0 and m % n == m
        
        return (0, m)

    elif m_len == n_len:
        # When they have the same log2 magnitude, there are really only two possibilities:
        #   n > m, see above case
        #   n <= m < 2*n, m // n is 1
        # Just in case I screwed up this logic, we do the simple thing and just keep reducing
        # the remainder by n until it's less than n; this while loop should never run more
        # than once though
        
        q = 0
        r = m

        while r >= n:
            r -= n
            q += 1
        
        return q, r
    
    elif m_len < 2 * n_len:
        # In this case, we know that m > n, but m is not large enough to satisfy the condition
        # we really want (m_len == 2 * n_len)
        # However, we can manufacture a division like that pretty easily: we take the difference
        # between the bit lengths (call it k) and then take 2*k digits from the front of m and
        # k digits from the front of n; call these m_hi and n_hi respectively; the remaining
        # digits on the bottom (m_lo and n_lo) will be identicial for both numbers
        #
        #   m_hi, n_hi  m_lo, n_lo
        #   |-k-||-k-|  (remaining digits)
        #   mmmmmmmmmm  mmmmmmmmmmmmm
        #        nnnnn  nnnnnnnnnnnnn
        #
        # The division of m_hi // n_hi will be a really good approximation of m // n (probably
        # 1 or 2 off at most -- I'm too lazy to work out the exact worst case error). Whatever
        # the error is, we then just correct the quotient up or down by 1 until the remainder
        # falls into the correct range (0 <= remainder < n).
        
        k = m_len - n_len
        excess_bits = n_len - k

        m_hi, m_lo = _splitHiLo(m, excess_bits)
        n_hi, n_lo = _splitHiLo(n, excess_bits)

        if n_hi == 0:
            print(m, n)

        q,r = _divModPositiveArgs(m_hi, n_hi)
        
        # r = m - n*q
        r = ((r << excess_bits) | m_lo) - n_lo * q

        while r < 0:
            r += n
            q -= 1
        while r >= n:
            r -= n
            q += 1

        return q,r
    
    elif m_len == 2 * n_len:
        # the ideal case
        # we split up the division into 2 half size divisions; for example
        # we'll consider the 16-bit by 8-bit division below:
        #
        #  m = aaaabbbbccccdddd
        #  n =         eeeeffff
        #
        # first, we want to calculate divmod(aaaabbbbcccc, eeeeffff); we can do
        # this by approximating the quotient with aaaabbbb/eeee and correcting
        # the result with an additions or subtraction as necessary. Then we can
        # concatonate the remainder with dddd and divide this by eeeeffff; since
        # this is another 12-bit by 8-bit division, we can do it the same way
        # again by approximating with an 8-bit by 4-bit division first and then
        # correcting. Finally, we take the 2nd remainder and concatonate the
        # quotients of the two computations for the overall result
        
        k = n_len
        kh_floor = k // 2
        kh_ceil = k - kh_floor

        m_hi, m_mid = _splitHiLo(m, k)
        m_mid, m_lo = _splitHiLo(m_mid, kh_ceil)
        n_hi, n_lo = _splitHiLo(n, kh_floor)

        q1, r1 = _divModPositiveArgs(m_hi, n_hi)

        # r1 = {m_hi, m_lo} - (q1 * n)
        r1 = ((r1 << kh_floor) | m_mid) - n_lo * q1

        while r1 < 0:
            r1 += n
            q1 -= 1
        while r1.bit_length() >= k:
            r1 -= n
            q1 += 1
        
        q2, r2 = _divModPositiveArgs(r1, n_hi)
        if k & 1:
            q2 <<= 1

        # r2 = (r1 << kh_ceil | m_lo) - n * q2
        r2 = ((r2 << kh_ceil) | m_lo) - n_lo * q2

        while r2 < 0:
            r2 += n
            q2 -= 1
        while r2 >= n:
            r2 -= n
            q2 += 1
        
        q = (q1 << kh_ceil) + q2

        return q,r2
    
    # the remaining case: m_len > 2 * n_len
    # At this point we essentially do traditional long division, except that
    # our base is going to be effectively 2**(n_len+1); if we way that k=n_len,
    # we repeatedly take 2*k bits off the front of m, divide it by n (which hits)
    # the optimal case, accumulate the quotient (each time right padded with zeros
    # the same number of remaining digits in m), and concatonate the remainder with
    # the remaining lower digits of m, then repeat. If you think about this it
    # reallly is just long division (Note: we keep track of bits processed which
    # essentially just shifts in the right padding bits of the quotient as we go;
    # I think this is a bit more efficient since right padding immediately creates
    # a big number which takes up a lot of memory)

    k = n.bit_length()
    q = 0
    r = m
    remainingBits = r.bit_length() - 2 * k
    while r > n:
        newRemainingBits = max(r.bit_length() - 2 * k, 0)
        bitsProcessed = remainingBits - newRemainingBits
        remainingBits = newRemainingBits

        q <<= bitsProcessed

        r_hi, r_lo = _splitHiLo(r, remainingBits)

        qi, r = _divModPositiveArgs(r_hi, n)
        r = (r << remainingBits) | r_lo

        q += qi

    q <<= remainingBits
    return q, r

def _toBase10StringHelper(n, powers, digitsLog2):
    '''calculate the decimal representation of n; powers must be the list of
    values of the form 10**(2**n) such that the largest value is at least the
    square root of n; digitsLog2 is the log 2 of the number of decimal digits to
    produce, and the result string will be left padded with ascii 0; note that
    it should satisfy n < 10**(2**digitsLog2).
    
    Theory of operation: we recursively break down the conversion problem by
    dividing by a large power of then, converting the quotient and remainder to
    decimal, and then concatenating the results; the powers list is provided so
    that we have precomputed values for the powers of 10 to divide by, and by
    being of powers of 2 number of digits, we can recursively split the problem
    in half; when we get to the point where the number is less than 20000 binary
    digits, we just use the python native str function as this is efficient for
    small integers'''

    if n.bit_length() < 20000:
        chars = str(n)

        # left pad with zeros to the expected number of digits; this way if we
        # are computing the rhs which will then be concatenated, we will produce
        # the correct amount of separating zeros
        return '0' * ((1 << digitsLog2) - len(chars)) + chars

    # split the number by a power of ten, concatenate the converted quotient
    # and remainder
    lhs, rhs = _divModPositiveArgs(n, powers[digitsLog2-1])
    return (_toBase10StringHelper(lhs, powers, digitsLog2-1) +
        _toBase10StringHelper(rhs, powers, digitsLog2-1))

def _floorSqrtPositiveInt(n):
    '''calculate the floor of the sqrt of an integer; this function expects a
    positive integer (use fastBigIntFloorSqrt if you wanttype & value checking).
    This basically uses Newton's method recursively; since Newton's method
    acheives exponentially more digits each iteration (in fact normally double
    the digits) we only use half the digits each iteration to approximate the
    square root, perform one iteration, and then correct up or down by one until
    we have the result exactly'''

    # for really small ints (128 or less) we just brute force it
    if n.bit_length() <= 1:
        return n
    elif n.bit_length() < 8:
        s = 1
        while (s+1)*(s+1) <= n:
            s += 1
        return s

    # calculate an approximation by using only half of the bits
    resultPadBits = n.bit_length() // 4
    padBits = 2 * resultPadBits
    approx = _floorSqrtPositiveInt(n >> padBits) << resultPadBits

    # refine the approximation with one iteration of newtons method
    approx = (approx + _divModPositiveArgs(n, approx)[0]) >> 1

    # add or subract 1 until the approximation is exact; this should only run
    # 1 or 2 correction iterations maxs
    actualSquare = approx * approx
    if actualSquare > n:
        approx -= 1
        actualSquare -= ((approx << 1) | 1)
        while actualSquare > n:
            approx -= 1
            actualSquare -= ((approx << 1) | 1)
    else:
        actualSquare += ((approx << 1) | 1)
        while actualSquare <= n:
            approx += 1
            actualSquare += ((approx << 1) | 1)       
    
    return approx

def _splitHiLo(num, bitIdx):
    '''helper function to split an integer into to ints at a particular bit
    index; this assumes num and bitIdx are ints'''

    hi = num >> bitIdx
    lo = num & ((1 << bitIdx) - 1)
    return hi, lo