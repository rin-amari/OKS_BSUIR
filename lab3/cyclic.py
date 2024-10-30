from bitarray import bitarray


def cyclic(dividend, divisor):
    quotient = []
    remainder = []

    count_left = 0
    count_right = len(divisor)
    cur_dividend = dividend[count_left:count_right]

    while len(cur_dividend) == len(divisor) and count_left < len(dividend):
        while len(remainder):
            if remainder[0] == 0:
                remainder = remainder[1:]
                quotient.append(0)
                count_right += 1
            else:
                break
        if len(remainder) + count_right - count_left > len(divisor):
            count_left += len(divisor) - len(remainder)
            while len(remainder) + count_right - count_left > len(divisor):
                count_right -= 1
        cur_dividend = remainder + dividend[count_left:count_right]

        print(dividend[count_left:])
        print(remainder, cur_dividend)
        while cur_dividend[0] == 0:
            if len(remainder) > 0:
                remainder = remainder[1:]
                quotient.append(0)
                cur_dividend = remainder + dividend[count_left:count_right]
            else:
                quotient.append(0)
                count_left += 1
                count_right += 1
                cur_dividend = dividend[count_left:count_right]
        count_left = count_right

        quotient.append(1)
        remainder.clear()
        for i in range(len(cur_dividend)):
            if cur_dividend[i] == divisor[i]:
                remainder.append(0)
            else:
                remainder.append(1)
        remainder = remainder[1:]
        count_right += 1

    print("quotient:", quotient)
    print("remainder:", remainder)

    remainder_bit = bitarray()
    for i in range(len(remainder)-1):
        if remainder[i] == 0:
            remainder_bit.append(0)
        else:
            remainder_bit.append(1)
    return remainder_bit.tobytes()
