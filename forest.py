import os
import sys
import bpy
import math
import numpy as np
from typing import Tuple

# IO format
io_folder = 'D:/Mesh/scenes/forest'
file_format = 'JPEG'
color_depth = '8'
color_mode = 'RGB'
resolution_x = 1280
resolution_y = 720
views = 40 # views per radius

# Camera config
cam_location = [40.748, -18.083, 15.867]
cam_rotation = [90., 0., 69.4]
lens = 35
sensor_width = 32
radius = [32., 40., 48., 56., 64.]
target_location = [0., 0., 5.]

# Light config
light_location = [15.499, -46.782, 29.921]
light_rotation = [68.6, 7.67, 15.3]
energy = 1


context = bpy.context
scene = bpy.context.scene
render = scene.render


class Light(object):
    def __init__(
        self,
        location: Tuple[float],
        rotation: Tuple[float],
        energy: int=20,
    ):
        super().__init__()
        self.light = bpy.data.lights['Sun']
        self.light.type = 'SUN'
        self.light.use_shadow = False
        self.light.specular_factor = 1.0
        self.light.energy = energy

        self.light = bpy.data.objects['Sun']
        self.location = self.light.location
        self.location.x, self.location.y, self.location.z = location
        self.light.rotation_mode = 'XYZ'
        for i in range(3):
            self.light.rotation_euler[i] = math.radians(rotation[i])


class Camera(object):
    def __init__(
        self,
        location: Tuple[float],
        rotation: Tuple[float],
        lens: int=35,
        sensor_width: int=32,
        # target_location: Tuple[int] = [0., 0., 5.],
    ):
        super().__init__()
        self.camera = bpy.data.objects['Camera']
        self.location = self.camera.location
        self.rotation = self.camera.rotation_euler
        self.camera.data.lens = lens
        self.camera.data.sensor_width = sensor_width

        self.set_camera(location, rotation)

    def set_camera(self, location, rotation):
        self.location.x, self.location.y, self.location.z = location
        self.camera.rotation_mode = 'XYZ'
        for i in range(3):
            self.rotation[i] = math.radians(rotation[i])
        return None
    
    def intrinsic(self):
        # camera 2 image transformation matrix
        f_mm = self.camera.data.lens
        sensor_size_mm = self.camera.data.sensor_width
        pixel_aspect_ratio = render.pixel_aspect_y / render.pixel_aspect_x
        pixel_size = sensor_size_mm / f_mm / resolution_x # 1 / px
        
        s_u = 1 / pixel_size
        s_v = 1 / pixel_size / pixel_aspect_ratio
        u_0 = resolution_x/2 - self.camera.data.shift_x*resolution_x
        v_0 = resolution_y/2 - self.camera.data.shift_y*resolution_x/pixel_aspect_ratio
        self.intrinsic_matrix = np.array([
            [s_u, 0, u_0],
            [0, s_v, v_0],
            [0,  0,  1  ],
        ], dtype=float)
        return self.intrinsic_matrix

    def extrinsic(self):
        # camera 2 world transformation matrix
        context.view_layer.update()
        self.extrinsic_matrix = np.array(self.camera.matrix_world, dtype=float)
        return self.extrinsic_matrix


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
    return rotation


def random_sphere(
    center: Tuple[float],
    radius: float,
):
    translation = np.random.rand(3)-0.5
    norm = np.linalg.norm(translation, ord=2)
    translation /= norm
    location = center+translation*radius
    return location


def mtx2str(array, digits=8):
    s = ''
    lines = array.tolist()
    for line in lines:
        for number in line:
            if digits==8:
                s += f"{number:.8f} "
            elif digits==2:
                s += f"{number:.2f} "
        s += '\n'
    return s

# Render setting
render.engine = "BLENDER_EEVEE"
render.image_settings.file_format = file_format
render.image_settings.color_depth = color_depth
render.image_settings.color_mode = color_mode
render.resolution_x = resolution_x
render.resolution_y = resolution_y
render.resolution_percentage = 100
render.film_transparent = False
scene.world.color = (1, 1, 1)

# Set up output
scene.use_nodes = True
context.view_layer.use_pass_normal = True
context.view_layer.use_pass_diffuse_color = True
context.view_layer.use_pass_object_index = True
tree = scene.node_tree
links = tree.links
# Clear default nodes
for n in tree.nodes:
    tree.nodes.remove(n)
render_layers = tree.nodes.new('CompositorNodeRLayers')
image_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
image_file_output.label = 'Image'
image_file_output.base_path = ''
links.new(render_layers.outputs['Image'], image_file_output.inputs[0])

# Light and camera
light = Light(light_location, light_rotation, energy)
cam = Camera(cam_location, cam_rotation, lens, sensor_width)
intrinsic = cam.intrinsic()

# Rendering
img_folder = os.path.join(io_folder, "blended_images/")
cam_folder = os.path.join(io_folder, "cams")
if not os.path.isdir(img_folder):
    os.mkdir(img_folder)
if not os.path.isdir(cam_folder):
    os.mkdir(cam_folder)
render.filepath = img_folder
for r in radius:
    for i in range(views):
        cam_location = random_sphere(target_location, r)
        cam_rotation = track(cam_location, target_location)
        cam.set_camera(cam_location, cam_rotation)
        extrinsic = cam.extrinsic()

        image_file_output.file_slots[0].path = render.filepath + f"{int(r):0>2d}-{i:0>3d}-"
        with open(os.path.join(cam_folder, f"{int(r):02d}-{i:0>3d}_cam.txt"), 'w') as f:
            f.write("extrinsic\n")
            f.write(mtx2str(extrinsic)+'\n\n')
            f.write("intrinsic\n")
            f.write(mtx2str(intrinsic, digits=2)+'\n\n')

        bpy.ops.render.render(write_still=True)