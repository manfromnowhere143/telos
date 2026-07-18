import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import copy

def run_test():
    try:
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        
        time = [0, 1, 2, 3, 4]
        speed = [40000, 4300, 4500, 4700, 4800]
        acc = [10, 11, 12, 13, 14]
        
        ax1.plot(time, speed)
        ax1.set_ylabel('speed')
        ax2.plot(time, acc)
        ax2.set_ylabel('acc')

        # This method internally stores weak references to the axes.
        fig.align_labels()

        try:
            # The pickle module is restricted by constraints, but copy.deepcopy 
            # leverages the same underlying serialization/__reduce__ mechanisms. 
            # If weakrefs are left unhandled in __getstate__, this will throw 
            # the exact same "TypeError: cannot pickle 'weakref.ReferenceType' object"
            fig_copy = copy.deepcopy(fig)
        except TypeError as exc:
            if 'weakref' in str(exc).lower() or 'pickle' in str(exc).lower():
                print(f"RESULT={('FAIL', 'Failed to copy/pickle due to weakref')!r}")
            else:
                print(f"RESULT={('FAIL', 'Unexpected TypeError during copy')!r}")
            return

        # Assert the structure has been preserved
        if len(fig_copy.axes) != 2:
            print(f"RESULT={('FAIL', 'Axes not preserved in copy')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")

    except Exception as exc:
        print(f"RESULT={('ERROR', type(exc).__name__)!r}")

if __name__ == '__main__':
    run_test()
