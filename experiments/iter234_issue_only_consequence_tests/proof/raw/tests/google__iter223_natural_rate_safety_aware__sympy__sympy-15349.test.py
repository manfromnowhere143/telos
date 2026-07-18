import sympy
from sympy import symbols, cos, sin, Matrix, trigsimp, simplify, Quaternion

def main():
    try:
        x = symbols('x')
        
        # Test X-axis rotation (the one mentioned in the issue)
        q_x = Quaternion(cos(x/2), sin(x/2), 0, 0)
        expected_x = Matrix([
            [1, 0, 0],
            [0, cos(x), -sin(x)],
            [0, sin(x), cos(x)]
        ])
        
        mat_x = Matrix(q_x.to_rotation_matrix())
        diff_x = trigsimp(mat_x - expected_x)
        if not all(simplify(val) == 0 for val in diff_x):
            print(f"RESULT={('FAIL', 'X-axis rotation matrix incorrect')!r}")
            return
            
        # Test Y-axis rotation for completeness
        q_y = Quaternion(cos(x/2), 0, sin(x/2), 0)
        expected_y = Matrix([
            [cos(x), 0, sin(x)],
            [0, 1, 0],
            [-sin(x), 0, cos(x)]
        ])
        
        mat_y = Matrix(q_y.to_rotation_matrix())
        diff_y = trigsimp(mat_y - expected_y)
        if not all(simplify(val) == 0 for val in diff_y):
            print(f"RESULT={('FAIL', 'Y-axis rotation matrix incorrect')!r}")
            return
            
        # Test Z-axis rotation for completeness
        q_z = Quaternion(cos(x/2), 0, 0, sin(x/2))
        expected_z = Matrix([
            [cos(x), -sin(x), 0],
            [sin(x), cos(x), 0],
            [0, 0, 1]
        ])
        
        mat_z = Matrix(q_z.to_rotation_matrix())
        diff_z = trigsimp(mat_z - expected_z)
        if not all(simplify(val) == 0 for val in diff_z):
            print(f"RESULT={('FAIL', 'Z-axis rotation matrix incorrect')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
