from __future__ import annotations
import math

class Vec3:
    def __init__(self, a: float, b: float, c: float):
        self.a = a
        self.b = b
        self.c = c
    
    def __str__(self) -> str:
        return f'({self.a}, {self.b}, {self.c})'

    def dot(self, vec: Vec3) -> Vec3:
        return Vec3(self.b * vec.c - self.c * vec.b, self.c * vec.a - self.a * vec.c, self.a * vec.b - self.b * vec.a)

    def mag(self) -> float:
        return math.sqrt(self.a**2 + self.b**2 + self.c**2)
    
    def __mul__(self, vec_or_scl: Vec3 | float) -> Vec3:
        if isinstance(vec_or_scl, Vec3):
            return self.dot(vec_or_scl)
        else:
            return Vec3(self.a * vec_or_scl, self.b * vec_or_scl, self.c * vec_or_scl)
    __rmul__ = __mul__
    
    def __add__(self, vec: Vec3) -> Vec3:
        if not isinstance(vec, Vec3): raise ValueError(f"Cannot add Vec3 to {type(vec)}")
        return Vec3(self.a + vec.a, self.b + vec.b, self.c + vec.c)
