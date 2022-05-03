import os 
import sys
import bpy
import math
import argparse
from typing import Tuple

parser = argparse.ArgumentParser(description='Blender Camera')

parser.add_argument('--root_folder', default='D:/Mesh/scenes/')
parser.add_argument('--scene', default='small')
parser.add_argument('--no_load', action='store_true', default=False, help='whether clean and reload obj')

parser.add_argument('--file_format', default='PNG')
parser.add_argument('--color_depth', default='8')
parser.add_argument('--color_mode', default='RGBA')
parser.add_argument('-x', '--resolution_x', default=1280)
parser.add_argument('-y', '--resolution_y', default=720)
parser.add_argument('-v', '--views', default=5)
parser.add_argument('--scale', default=1.)
parser.add_argument('--remove_doubles', default=True)
parser.add_argument('--edge_split', default=True)

parser.add_argument('--location', default=[5., 5., -1.5], help='camera location')
parser.add_argument('--rotation', default=[180., 0., 0.], help='camera rotation')
parser.add_argument('--lens', default=10)
parser.add_argument('--sensor_width', default=5)

parser.add_argument('--sun_location', default=[0., 0., 10])
parser.add_argument('--sun_rotation', default=[180., 0., 0.])
parser.add_argument('--energy', default=20)

argv = sys.argv[sys.argv.index("--") + 1:]
args = parser.parse_args(argv)

context = bpy.context
scene = bpy.context.scene
render = scene.render


def delete_and_import(
    no_load = True,
    obj_folder = ""
):
    if not no_load:
        context.active_object.select_set(True)
        bpy.ops.object.delete()
        obj_path = os.path.join(obj_folder, "scene.obj")
        bpy.ops.import_scene.obj(filepath=obj_path)


class Camera(object):
    def __init__(
        self,
        location: Tuple[float],
        rotation: Tuple[float],
        lens: int=35,
        sensor_width: int=32,
    ):
        super().__init__()
        self.camera = bpy.data.objects['Camera']

        self.location = self.camera.location
        self.location.x, self.location.y, self.location.z = location
        self.camera.rotation_mode = 'XYZ'
        for i in range(3):
            self.camera.rotation_euler[i] = math.radians(rotation[i])
        
        self.camera.data.lens = lens
        self.camera.data.sensor_width = sensor_width

        cam_constraint = self.camera.constraints.new(type='TRACK_TO')
        cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        cam_constraint.up_axis = 'UP_Y'

        # set the target empty camera
        self.empty = bpy.data.objects.new("Empty", None)
        self.empty.location = (0, 0, 0)
        self.camera.parent = self.empty
        scene.collection.objects.link(self.empty)
        context.view_layer.objects.active = self.empty
        cam_constraint.target = self.empty


class Light(object):
    def __init__(
        self,
        location: Tuple[float],
        rotation: Tuple[float],
        energy: int=20,
    ):
        super().__init__()
        self.light = bpy.data.lights['Light']
        self.light.type = 'SUN'
        self.light.use_shadow = False
        self.light.specular_factor = 1.0
        self.light.energy = energy

        self.light = bpy.data.objects['Light']
        self.location = self.light.location
        self.location.x, self.location.y, self.location.z = location
        self.light.rotation_mode = 'XYZ'
        for i in range(3):
            self.light.rotation_euler[i] = math.radians(rotation[i])

        # Add another light from the opposite direction
        bpy.ops.object.light_add(type='SUN')
        self.light2 = bpy.data.lights['Sun']
        self.light2.use_shadow = False
        self.light2.specular_factor = 1.0
        self.light2.energy = energy * 0.08
        self.light2 = bpy.data.objects['Sun']
        self.light2.rotation_euler = self.light.rotation_euler
        self.light2.rotation_euler[0] += 180


def main(args=None):

    # Render setting
    render.engine = "BLENDER_EEVEE"
    render.image_settings.file_format = args.file_format
    render.image_settings.color_depth = args.color_depth
    render.image_settings.color_mode = args.color_mode
    render.resolution_x = args.resolution_x
    render.resolution_y = args.resolution_y
    render.resolution_percentage = 100
    render.film_transparent = True

    # Set up 3D model
    io_folder = os.path.join(args.root_folder, args.scene)
    delete_and_import(args.no_load, io_folder)

    # Set output nodes
    scene.use_nodes = True
    scene.view_layers["ViewLayer"].use_pass_normal = True
    scene.view_layers["ViewLayer"].use_pass_diffuse_color = True
    scene.view_layers["ViewLayer"].use_pass_object_index = True
    tree = scene.node_tree
    links = tree.links
    # Clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)
    render_layers = tree.nodes.new('CompositorNodeRLayers')

    # Set up output files
    image_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
    image_file_output.label = 'Image'
    image_file_output.base_path = ''
    links.new(render_layers.outputs['Image'], image_file_output.inputs[0])

    # Select object
    obj = bpy.context.selected_objects[0]
    # obj.rotation_euler[0] += 180
    context.view_layer.objects.active = obj
    for slot in obj.material_slots:
        node = slot.material.node_tree.nodes['Principled BSDF']
        node.inputs['Specular'].default_value = 0.05
    if args.scale != 1:
        bpy.ops.transform.resize(value=(args.scale,args.scale,args.scale))
        bpy.ops.object.transform_apply(scale=True)
    if args.remove_doubles:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
    if args.edge_split:
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        context.object.modifiers["EdgeSplit"].split_angle = 1.32645
        bpy.ops.object.modifier_apply(modifier="EdgeSplit")
    obj.pass_index = 1

    # Light
    light = Light(args.sun_location, args.sun_rotation, args.energy)

    # Set camera
    cam = Camera(args.location, args.rotation, args.lens, args.sensor_width)

    # Rendering
    render.filepath = os.path.join(io_folder, "blender_camera/")
    print(f"{'-'*15}Start Rendering{'-'*15}")
    stepsize = 360.0 / args.views
    for i in range(args.views):
        step_angle = stepsize * i
        print(f"Rotation {step_angle}, {math.radians(step_angle)}")

        image_file_output.file_slots[0].path = render.filepath + f"image_{int(step_angle):0>3d}"
        bpy.ops.render.render(write_still=True)
        cam.empty.rotation_euler[2] += math.radians(stepsize)

if __name__ == '__main__':
    main(args)
