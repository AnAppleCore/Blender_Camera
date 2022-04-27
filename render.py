import os 
import sys
import bpy
import math
import argparse
from typing import Tuple

parser = argparse.ArgumentParser(description='Blender Camera')

parser.add_argument('--root_folder', default='D:/Mesh/scenes/')
parser.add_argument('--scene', default='small')
parser.add_argument('--file_format', default='PNG')
parser.add_argument('--color_depth', default='8')
parser.add_argument('--color_mode', default='RGB')
parser.add_argument('-x', '--resolution_x', default=1280)
parser.add_argument('-y', '--resolution_y', default=720)

parser.add_argument('--no_load', action='store_true', default=False, help='whether clean and reload obj')
parser.add_argument('--location', default=[0., 0., 10.], help='camera location')
parser.add_argument('--rotation', default=[0., 0., 0.], help='camera rotation')
parser.add_argument('--fov', default=10, help='camera fov')

argv = sys.argv[sys.argv.index("--") + 1:]
args = parser.parse_args(argv)

context = bpy.context
scene = bpy.context.scene


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
        fov = 10,
    ):
        super().__init__()
        self.camera = bpy.data.objects['Camera']

        self.location = self.camera.location
        self.location.x, self.location.y, self.location.z = location
        self.camera.rotation_mode = 'XYZ'
        for i in range(3):
            self.camera.rotation_euler[i] = math.radians(rotation[i])
        self.camera.data.angle = math.radians(fov)


def main(args=None):

    # Render setting
    scene.render.image_settings.file_format = args.file_format
    scene.render.image_settings.color_depth = args.color_depth
    scene.render.image_settings.color_mode = args.color_mode
    scene.render.resolution_x = args.resolution_x
    scene.render.resolution_y = args.resolution_y
    scene.render.resolution_percentage = 100

    # Set up 3D model
    io_folder = os.path.join(args.root_folder, args.scene)
    delete_and_import(args.no_load, io_folder)

    # Set camera
    cam = Camera(args.location, args.rotation, args.fov).camera

    # Set output nodes
    scene.use_nodes = True
    tree = scene.node_tree
    links = tree.links
    # Clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)
    render_layers = tree.nodes.new('CompositorNodeRLayers')

    # Set output files
    image_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
    image_file_output.label = 'Image'
    links.new(render_layers.outputs['Image'], image_file_output.inputs[0])
    image_file_output.base_path = ''

    scene.render.filepath = os.path.join(io_folder, "blender_camera/")
    image_file_output.file_slots[0].path = scene.render.filepath + 'image_'

    bpy.ops.render.render()

if __name__ == '__main__':
    main(args)
