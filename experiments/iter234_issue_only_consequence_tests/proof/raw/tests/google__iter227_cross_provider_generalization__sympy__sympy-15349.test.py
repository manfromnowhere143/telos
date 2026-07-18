from sympy import Quaternion, cos, sin, pi, symbols, trigsimp, Matrix

def run_test():
    x = symbols('x')
    
    # Construct quaternion for rotation around X-axis
    q = Quaternion(cos(x/2), sin(x/2), 0, 0)
    
    # Convert to rotation matrix and simplify as per the issue description
    M = trigsimp(q.to_rotation_matrix())
    
    # In the buggy output, the sine terms are symmetric:
    # M[1, 2] == sin(x) and M[2, 1] == sin(x)
    # They should be antisymmetric for a standard coordinate rotation
    if M[1, 2] == M[2, 1] and M[1, 2] != 0:
        return ('FAIL', 'Matrix off-diagonals are improperly symmetric (incorrect signs)')

    # Validate against known correct standard rotation matrix for X-axis
    expected = Matrix([
        [1, 0, 0],
        [0, cos(x), -sin(x)],
        [0, sin(x), cos(x)]
    ])
    
    # Check if they are symbolically identical or evaluate to the same matrix
    M_val = M.subs(x, pi/2)
    expected_val = expected.subs(x, pi/2)
    
    if M_val != expected_val:
        return ('FAIL', 'Evaluated X-axis rotation matrix is incorrect')

    return ('PASS',)

try:
    result = run_test()
    print(f"RESULT={result!r}")
except Exception as e:
    print(f"RESULT={('ERROR', type(e).__name__)!r}")
