#!/usr/bin/env python

from timer import Timer


def fibonacci (N):
    if N==0: return 0
    elif N==1: return 1
    else: return fibonacci (N-1) + fibonacci(N-2)
    
    
if __name__ == '__main__':
    with Timer() as t:
        v = fibonacci(20)
    print ('%s ms' % t.msecs)
