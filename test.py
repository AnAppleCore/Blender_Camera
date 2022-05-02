import numpy as np
from typing import Tuple
import bpy 


def track(
    cam_location: Tuple[float],
    target_location: Tuple[float],
):
    cam_location = np.array(cam_location)
    target_location = np.array(target_location)
    relative = target_location-cam_location
    x, y, z = relative
    for i in [x, y, z]:
        if i == 0:
            i += 1e-5
    rotation = np.zeros(3)
    l = np.linalg.norm(relative, ord=2)
    rotation[0] = np.rad2deg(np.arccos(-z / l))
    rotation[2] = np.rad2deg(np.arctan(-x / y))
    if y < 0. :
        rotation[2] += 180
    return np.deg2rad(rotation)


def set_location(loc_pt, loc):
    loc_pt.x, loc_pt.y, loc_pt.z = loc


def set_rotation(rot_pt, rot):
    for i in range(3):
        rot_pt[i] = rot[i]


def random(scale=30):
    l1 = (np.random.rand(3)-0.5)*scale
    l2 = (np.random.rand(3)-0.5)*scale
    return l1, l2


for _ in range(20):

    l1, l2 = random()
    r = track(l1, l2)
    cam = bpy.data.objects['Camera']
    cube = bpy.data.objects['Cube']
    cam_loc = cam.location
    cube_loc = cube.location
    cam_rot = cam.rotation_euler
    set_location(cam_loc, l1)
    set_location(cube_loc, l2)
    set_rotation(cam_rot, r)
    bpy.context.view_layer.update()

    with open('D:\Mesh\Blender_Camera\Record.txt', 'a') as f:
        f.write('camera set to: '+str(l1)+'\n')
        f.write('target set to: '+str(l2)+'\n')
        f.write('camera rot to: '+str(r)+'\n')
        f.write(str(cam.matrix_world)+'\n')
        f.write(str(cam.location)+'\n')
        f.write(str(cam.rotation_euler)+'\n')
        f.write(f"{'--'*40}\n")

# import torch
# def look_at_to_c2w(C: torch.Tensor, p: torch.Tensor, up=(0.1, 0.1, 1.0)):
#     # from C to look at p, the up direction is z+
#     up = torch.nn.functional.normalize(torch.tensor(up), dim=0)
#     L = (p - C)
#     s = torch.cross(L, up)
#     u = torch.cross(s, L)
#     R = torch.nn.functional.normalize(torch.stack([s, u, L]), dim=1).T
#     ret = torch.zeros((4, 4))
#     ret[:3, :3] = R
#     ret[:3, 3] = C
#     ret[3, 3] = 1.0
#     return ret