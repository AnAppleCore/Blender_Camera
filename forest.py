import os
import sys
import bpy
import math
import numpy as np
from mathutils import Matrix
from typing import Tuple

io_folder = 'D:/Mesh/scenes/forest'
file_format = 'JPEG'
color_depth = '8'
color_mode = 'RGB'
resolution_x = 1280
resolution_y = 720
views = 5

cam_location = [40.748, -18.083, 15.867]
cam_rotation = [90., 0., 69.4]
lens = 35
sensor_width = 32
target_location = [0., 0., 5.]

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
        target_location: Tuple[int] = [0., 0., 5.],
    ):
        super().__init__()
        self.camera = bpy.data.objects['Camera']

        self.location = self.camera.location
        self.rotation = self.camera.rotation_euler

        self.location.x, self.location.y, self.location.z = location
        self.camera.rotation_mode = 'XYZ'
        for i in range(3):
            self.rotation[i] = math.radians(rotation[i])
        
        self.camera.data.lens = lens
        self.camera.data.sensor_width = sensor_width

        # set the target empty camera
        cam_constraint = self.camera.constraints.get('Track To')
        self.empty = bpy.data.objects.get('Empty')
        if cam_constraint is None:
            cam_constraint = self.camera.constraints.new(type='TRACK_TO')
            cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
            cam_constraint.up_axis = 'UP_Y'
            if self.empty is None:
                self.empty = bpy.data.objects.new("Empty", None)
                self.empty.location.x = target_location[0]
                self.empty.location.y = target_location[1]
                self.empty.location.z = target_location[2]
                self.camera.parent = self.empty
                scene.collection.objects.link(self.empty)
                context.view_layer.objects.active = self.empty
            else:
                for i in range(3):
                    self.empty.rotation_eular[i] = 0.0
            cam_constraint.target = self.empty
    
    def intrinsic(self):
        f_mm = self.camera.data.lens
        sensor_size_mm = self.camera.data.sensor_width
        pixel_aspect_ratio = render.pixel_aspect_y / render.pixel_aspect_x
        pixel_size = sensor_size_mm / f_mm / resolution_x # 1 / px
        
        s_u = 1 / pixel_size
        s_v = 1 / pixel_size / pixel_aspect_ratio
        u_0 = resolution_x/2 - self.camera.data.shift_x*resolution_x
        v_0 = resolution_y/2 - self.camera.data.shift_y*resolution_x/pixel_aspect_ratio
        K = Matrix((
            (s_u, 0,   u_0),
            (0,   s_v, v_0),
            (0,   0,   1  ),
        ))
        return K
    
    def extrinsic(self):
        return self.camera.matrix_world


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
render.filepath = os.path.join(io_folder, "blender_camera/")
stepsize = 360.0 / views
for i in range(views):
    step_angle = stepsize * i
    print(f"Rotation {step_angle}, {math.radians(step_angle)}")

    image_file_output.file_slots[0].path = render.filepath + f"image_{int(step_angle):0>3d}"
    print(cam.location, cam.rotation)
    print(cam.empty.location, cam.empty.rotation_euler)
    print(cam.extrinsic())
    # print(intrinsic)
    # bpy.ops.render.render(write_still=True)
    cam.empty.rotation_euler[2] += math.radians(stepsize)