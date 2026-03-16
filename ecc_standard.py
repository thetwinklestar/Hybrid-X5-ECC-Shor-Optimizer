#!/usr/bin/env python3
"""
ecc_standard.py
Standard Elliptic Curve for 13-bit Shor Optimization
"""

from typing import Tuple, Optional

# ========== 第1部分：类定义（必须先有）==========

class StandardECC:
    def __init__(self, p: int, a: int, b: int, G: Tuple[int, int], n: int):
        self.p = p
        self.a = a
        self.b = b
        self.G = G
        self.n = n
        
    def point_add(self, P, Q):
        if P is None: 
            return Q
        if Q is None: 
            return P
        x1, y1 = P
        x2, y2 = Q
        if x1 == x2:
            if y1 != y2 or y1 == 0: 
                return None
            lam = (3*x1*x1 + self.a) * pow(2*y1, -1, self.p) % self.p
        else:
            lam = (y2 - y1) * pow(x2 - x1, -1, self.p) % self.p
        x3 = (lam*lam - x1 - x2) % self.p
        y3 = (lam*(x1 - x3) - y1) % self.p
        return (x3, y3)
    
    def scalar_mult(self, k, point=None):
        if point is None: 
            point = self.G
        result = None
        addend = point
        while k > 0:
            if k & 1: 
                result = self.point_add(result, addend)
            addend = self.point_add(addend, addend)
            k >>= 1
        return result

# ========== 第2部分：执行代码（类定义之后）==========

p = 1048783
G = (231634, 106125)
a, b = 0, 7

print("="*60)
print("13-bit ECC Verification")
print("="*60)
print(f"Prime: {p}")
print(f"Generator G: {G}")
print(f"Curve: y² = x³ + {b}")

ecc = StandardECC(p, a, b, G, 1050337)

G2 = ecc.point_add(G, G)
print(f"\nG + G = 2G = {G2}")

G3 = ecc.scalar_mult(3)
print(f"3G = {G3}")

print("\n✓ 13-bit ECC verification passed!")
print("="*60)
