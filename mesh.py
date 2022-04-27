from logging import root
import pymeshlab
import numpy as np
import os, tqdm

root_folder = "D:/Mesh/scenes"
mesh_list_path = os.path.join(root_folder, "./mesh_list_small.txt")
output_mesh = os.path.join(root_folder, "scenes/small/scene.obj")
mesh_list = []
with open(mesh_list_path,'r') as f:
    for line in f:
        mesh_list.append(line.strip('\n'))
print(f"len(mesh_list): {len(mesh_list)}")

ms =  pymeshlab.MeshSet()
print(ms.number_meshes())

for i in tqdm.trange(len(mesh_list), ncols=80):
    ms.load_new_mesh(mesh_list[i])
print(ms.number_meshes())
ms.apply_filter('generate_by_merging_visible_meshes')
print(ms.number_meshes())
ms.save_current_mesh(output_mesh)
