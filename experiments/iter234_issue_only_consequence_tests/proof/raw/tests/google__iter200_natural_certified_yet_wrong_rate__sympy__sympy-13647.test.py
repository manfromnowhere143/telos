import sympy as sm

def main():
    try:
        M = sm.eye(6)
        V = 2 * sm.ones(6, 2)
        m_list = M.tolist()
        v_list = V.tolist()
        
        # Test col_insert middle (the specific issue reported)
        expected_col_3 = [m_list[i][:3] + v_list[i] + m_list[i][3:] for i in range(6)]
        if M.col_insert(3, V).tolist() != expected_col_3:
            print(f"RESULT={('FAIL', 'col_insert(3) incorrect')!r}")
            return
            
        # Test col_insert start
        expected_col_0 = [v_list[i] + m_list[i] for i in range(6)]
        if M.col_insert(0, V).tolist() != expected_col_0:
            print(f"RESULT={('FAIL', 'col_insert(0) incorrect')!r}")
            return

        # Test col_insert end
        expected_col_6 = [m_list[i] + v_list[i] for i in range(6)]
        if M.col_insert(6, V).tolist() != expected_col_6:
            print(f"RESULT={('FAIL', 'col_insert(6) incorrect')!r}")
            return
            
        # Test row_insert middle (ensure row operations were not similarly broken)
        U = 2 * sm.ones(2, 6)
        u_list = U.tolist()
        
        expected_row_3 = m_list[:3] + u_list + m_list[3:]
        if M.row_insert(3, U).tolist() != expected_row_3:
            print(f"RESULT={('FAIL', 'row_insert(3) incorrect')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")
    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
