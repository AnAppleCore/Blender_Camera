import numpy as np

def mtx2str(array):
    s = ''
    lines = array.tolist()
    for line in lines:
        for number in line:
            s += f"{number:.8f} "
        s += '\n'
    return s

with open('test.txt', 'w') as f:
    f.write(mtx2str(np.random.randn(4, 4)*1000))