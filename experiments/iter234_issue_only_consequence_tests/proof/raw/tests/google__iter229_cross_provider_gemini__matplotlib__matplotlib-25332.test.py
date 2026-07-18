import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import copy

def main():
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

        fig.align_labels() 

        try:
            # copy.deepcopy delegates to __getstate__/__reduce_ex__.
            # If the figure contains an unpicklable weakref after align_labels(), 
            # deepcopy will raise the exact same TypeError as pickle.dumps would.
            copy.deepcopy(fig)
        except TypeError as e:
            msg = str(e).lower()
            if "weakref" in msg or "pickle" in msg:
                print(f"RESULT={('FAIL', 'Unpicklable weakref found after align_labels')!r}")
            else:
                print(f"RESULT={('FAIL', f'TypeError on deepcopy: {e}')!r}")
            return
        except Exception as e:
            print(f"RESULT={('FAIL', f'Unexpected error on deepcopy: {e}')!r}")
            return
            
        print(f"RESULT={('PASS',)!r}")

    except Exception as e:
        print(f"RESULT={('ERROR', type(e).__name__)!r}")

if __name__ == "__main__":
    main()
