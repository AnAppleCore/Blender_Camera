import numpy as np
import torch

px = 12
py = 24
f = 3
intrinsic = np.array([
            [f,  0., px],
            [0., f,  py],
            [0., 0., 1.],
        ])
    
print(intrinsic)
print(intrinsic.shape)
print(intrinsic.dtype)

def look_at_to_c2w(C: torch.Tensor, p: torch.Tensor, up=(0.1, 0.1, 1.0)):
    # from C to look at p, the up direction is z+
    up = torch.nn.functional.normalize(torch.tensor(up), dim=0)
    L = (p - C)
    s = torch.cross(L, up)
    u = torch.cross(s, L)
    R = torch.nn.functional.normalize(torch.stack([s, u, L]), dim=1).T
    ret = torch.zeros((4, 4))
    ret[:3, :3] = R
    ret[:3, 3] = C
    ret[3, 3] = 1.0
    return ret