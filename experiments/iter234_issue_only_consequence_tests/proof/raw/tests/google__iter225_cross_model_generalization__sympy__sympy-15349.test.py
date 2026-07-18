import sympy
from sympy import symbols, cos, sin, Matrix, zeros, trigsimp
from sympy.algebras.quaternion import Quaternion

def main():
    try:
        x = symbols('x')
        q = Quaternion(cos(x/2), sin(x/2), 0, 0)
        R = q.to_rotation_matrix()
        
        # A valid rotation matrix must have a determinant of 1.
        # The buggy version yielded a symmetric matrix with determinant cos(x)^2 - sin(x)^2 = cos(2x).
        det = trigsimp(R.det())
        if det != 1:
            print(f"RESULT={('FAIL', f'Determinant is {det}, expected 1')!r}")
            return
            
        # The rotation matrix for a quaternion rotation about the x-axis.
        # One of the sin(x) elements should be negative, unlike the bug's output.
        expected = Matrix([
            [1, 0, 0],
            [0, cos(x), -sin(x)],
            [0, sin(x), cos(x)]
        ])
        
        diff = (R - expected).applyfunc(trigsimp)
        if diff != zeros(3, 3):
            print(f"RESULT={('FAIL', 'Incorrect rotation matrix elements')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
