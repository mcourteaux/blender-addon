############################################################################
#  This file is part of the 4D Light Field Benchmark.                      #
#                                                                          #
#  This work is licensed under the Creative Commons                        #
#  Attribution-NonCommercial-ShareAlike 4.0 International License.         #
#  To view a copy of this license,                                         #
#  visit http://creativecommons.org/licenses/by-nc-sa/4.0/.                #
#                                                                          #
#  Authors: Katrin Honauer & Ole Johannsen                                 #
#  Contact: contact@lightfield-analysis.net                                #
#  Website: www.lightfield-analysis.net                                    #
#                                                                          #
#  This add-on is based upon work of Maximilian Diebold                    #
#                                                                          #
#  The 4D Light Field Benchmark was jointly created by the University of   #
#  Konstanz and the HCI at Heidelberg University. If you use any part of   #
#  the benchmark, please cite our paper "A dataset and evaluation          #
#  methodology for depth estimation on 4D light fields". Thanks!           #
#                                                                          #
#  @inproceedings{honauer2016benchmark,                                    #
#    title={A dataset and evaluation methodology for depth estimation on   #
#           4D light fields},                                              #
#    author={Honauer, Katrin and Johannsen, Ole and Kondermann, Daniel     #
#            and Goldluecke, Bastian},                                     #
#    booktitle={Asian Conference on Computer Vision},                      #
#    year={2016},                                                          #
#    organization={Springer}                                               #
#    }                                                                     #
#                                                                          #
############################################################################

bl_info = {
    'name': 'Light Field Renderer',
    'author': 'Ole Johannsen, Katrin Honauer',
    'description': 'Scripts to create a static light field setup',
    'version': (1, 1, 0),
    'blender': (2, 80, 0),
    'api': 36103,
    'location': 'View3D > Tool Shelf > 4D Light Field Renderer',
    'url': 'https://www.informatik.uni-konstanz.de/cvia/',
    'category': 'Render'
}

if "bpy" in locals():
    print("Force reloading the plugin.")
    import imp
    imp.reload(blender_utils)
    imp.reload(gui)
    imp.reload(lightfield_simulator)
    imp.reload(updates)
    imp.reload(import_export)
else:
    from . import blender_utils, gui, lightfield_simulator, updates, import_export

import bpy
from bpy.props import *

import datetime
import os


# global properties for the script, mainly for UI
class LFPropertyGroup(bpy.types.PropertyGroup):

    # camera parameters
    cube_camera = BoolProperty(
        name="cubemaps",
        default=False,
        update=updates.update_lightfield
    )
    focal_length = FloatProperty(
        name='f-Len[mm]',
        default=100,
        min=0,
        max=1000,
        description='Focal length of cameras [mm]',
        update=updates.update_lightfield
    )
    x_res = IntProperty(
        name='xRes[px]',
        default=512,
        min=1,
        max=10000,
        description='Image resolution in x direction [px]',
        update=updates.update_lightfield
    )
    y_res = IntProperty(
        name='yRes[px]',
        default=512,
        min=1,
        max=10000,
        description='Image resolution in y direction [px]',
        update=updates.update_lightfield
    )
    sensor_size = FloatProperty(
        name='sensorSize[mm]',
        default=35,
        min=1,
        max=1000,
        description='Sensor chip size in [mm]',
        update=updates.update_lightfield
    )
    sensor_fit = EnumProperty(
        name='sensorFitMethod',
        items = [
         ('AUTO', "Auto", " Fit to the sensor width or height depending on image resolution"),
         ('HORIZONTAL', "Horizontal", "HFit to the sensor width"),
         ('VERTICAL', "Vertical", "Fit to the sensor height"),
         ],
        default='AUTO'
    )
    fstop = FloatProperty(
        name='f-Stop',
        default=100,
        min=0,
        max=300,
        description='F-stop of cameras',
        update=updates.update_lightfield
    )

    # light field parameters
    num_cams_x = IntProperty(
        name='numCamsX',
        default=3,
        min=1,
        max=2000,
        description='Number of cameras in x direction',
        update=updates.update_number_of_cameras
    )
    num_cams_y = IntProperty(
        name='numCamsY',
        default=3,
        min=1,
        max=2000,
        description='Number of cameras in y direction',
        update=updates.update_number_of_cameras
    )
    baseline_mm = FloatProperty(
        name='baseline[mm]',
        default=50.0,
        min=0.01,
        max=15000,
        description='Distance between each pair of cameras in array in [mm]',
        update=updates.update_baseline
    )
    focus_dist = FloatProperty(
        name='focDist[m]',
        default=8,
        min=0,
        max=10000,
        description='Distance where cameras are focused at in [m], 0 = \infty ',
        update=updates.update_lightfield
    )
    depth_map_scale = FloatProperty(
        name='depthMapScale',
        default=10.0,
        description='Factor for the high resolution depth map export'
    )
    depth_maps = EnumProperty(
        name='depth maps',
        items = [
         ('NONE', "No Depth Maps", "Produces no depth maps."),
         ('CENTER', "Center Camera only", "Produces depth map for center camera only."),
         ('ALL', "All Depth Maps", "Produces depth map for all cameras."),
         ],
        default='NONE'
    )
    object_id_maps = EnumProperty(
        name='object id maps',
        items = [
         ('NONE', "No Object id Maps", "Produces no object id maps."),
         ('CENTER', "Center Camera only", "Produces depth map for center camera only."),
         ('ALL', "All Object id Maps", "Produces object id map for all cameras."),
         ],
        default='NONE'
    )
    sequence_start = IntProperty(
        name='start frame',
        default=0,
        description='The frame in the timeline where to start recording the LF movie'
    )
    sequence_end = IntProperty(
        name='end frame',
        default=0,
        description='The frame in the timeline where to stop recording the LF movie'
    )
    sequence_steps = IntProperty(
        name='frame steps',
        default=1,
        min=1,
        max=20,
        description='Step length from one to the next frame, i.e. to downsample the movie'
    )


    # file IO
    tgt_dir = StringProperty(
        name='',
        subtype='FILE_PATH',
        default=updates.get_default_target_directory(),
        description='Target directory for blender output',
        update=updates.update_target_directory
    )
    path_config_file = StringProperty(
        name='',
        subtype='FILE_PATH',
        default=updates.get_default_path_config_file(),
        description='File path for light field config file',
        update=updates.update_path_config_file
    )

    # meta information
    min_disp = FloatProperty(
        name='min_disp[px]',
        default=-2.0,
        min=-20.0,
        max=20.0,
        description='Min disparity of the scene in [px]',
    )
    max_disp = FloatProperty(
        name='max_disp[px]',
        default=2.0,
        min=-20.0,
        max=20.0,
        description='Max disparity the scene in [px]',
    )
    frustum_min_disp = FloatProperty(
        name='frustumMinDisp[px]',
        default=-2.0,
        min=-20.0,
        max=20.0,
        description='Min disparity of frustum in [px]',
        update=updates.update_lightfield
    )
    frustum_max_disp = FloatProperty(
        name='frustumMaxDisp[px]',
        default=2.0,
        min=-20.0,
        max=20.0,
        description='Max disparity of frustum in [px]',
        update=updates.update_lightfield
    )
    authors = StringProperty(
        name='',
        default='Katrin Honauer, Ole Johannsen, Daniel Kondermann, Bastian Goldluecke',
        description='Author(s) of the scene'
    )
    category = StringProperty(
        name='',
        default='test',
        description='Scene category, e.g. test, training, stratified'
    )
    scene = StringProperty(
        name='',
        default='scene_0',
        description='Name of the scene'
    )
    contact = StringProperty(
        name='',
        default='contact@lightfield-analysis.net',
        description='Contact information'
    )
    date = StringProperty(
        name='',
        default=str(datetime.date.today()),
        description='Creation date'
    )
    version = StringProperty(
        name='',
        default="v0",
        description='Version of the scene'
    )

    # Private variables to manage internal computations, no access from GUI interface
    baseline_x_m = FloatProperty(
        name='BaselineX',
        default=0.05,
    )
    baseline_y_m = FloatProperty(
        name='BaselineY',
        default=0.05,
    )
    cycles_seed = IntProperty(
        default=-1
    )
    setup_number = IntProperty(
        default=0
    )
    num_cams_x_hidden = IntProperty(
        default=0
    )
    num_cams_y_hidden = IntProperty(
        default=0
    )
    center_cam_x = FloatProperty(
        name='x',
        default=0.0,
        description='X position of center camera',
    )
    center_cam_y = FloatProperty(
        name='y',
        default=0.0,
        description='Y position of center camera',
    )
    center_cam_z = FloatProperty(
        name='z',
        default=0.0,
        description='Z position of center camera',
    )
    center_cam_rot_x = FloatProperty(
        name='x',
        default=3.141592654 / 2.0,
        description='Rotation of the center camera around the x axis',
    )
    center_cam_rot_y = FloatProperty(
        name='y',
        default=0.0,
        description='Rotation of the center camera around the y axis',
    )
    center_cam_rot_z = FloatProperty(
        name='z',
        default=-3.141592654 / 2.0,
        description='Rotation of the center camera around the z axis',
    )
    num_blades = FloatProperty(
        name='Blade Number',
        default=8,
        min=0,
        max=10000,
        description='Number of blades in aperture for polygonal bukeh (at least 3)',
        update=updates.update_lightfield
    )
    rotation = FloatProperty(
        name='Rotation [°]',
        default=8,
        min=0,
        max=10000,
        description='Rotation of blades in aperture [°]',
        update=updates.update_lightfield
    )

    def frustum_is_hidden(self):
        try:
            try:
                return self.get_frustum().hide
            except AttributeError:
                return self.get_frustum().hide_viewport
        except:
            return False

    def get_lightfield_cameras(self):
        cameras = []
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA' and obj.name.startswith("LF%s" % self.setup_number):
                cameras.append(obj)
        return cameras

    def get_center_camera(self):
        camera_name = self.get_camera_name((self.num_cams_y - 1) / 2, (self.num_cams_x - 1) / 2)
        try:
            camera = bpy.data.objects[camera_name]
        except KeyError:
            print("Could not find center camera: %s" % camera_name)
            return None

        return camera

    def get_frustum(self):
        return bpy.data.objects[self.get_frustum_name()]

    # scene object names
    def get_frustum_name(self):
        return "LF%s_Frustum" % self.setup_number

    def get_camera_name(self, i, j):
        return "LF%s_Cam%3.3i" % (self.setup_number, i*self.num_cams_x+j)

    def get_lightfield_name(self):
        return "LF%s" % self.setup_number

    @staticmethod
    def is_valid_directory(tgt_dir):
        if not os.path.isdir(bpy.path.abspath(tgt_dir)):
            print("Could not find directory: '%s'. Trying to create it..." % tgt_dir)
            try:
                os.makedirs(tgt_dir)
            except:
                print("Could not create directory: '%s'" % tgt_dir)
                return False
        return True


#def register():
#    # register properties
#    bpy.utils.register_class(LFPropertyGroup)
#    bpy.types.Scene.LF = bpy.props.PointerProperty(type=LFPropertyGroup)
#    bpy.utils.register_module(__name__)
#
#
#def unregister():
#    bpy.utils.unregister_module(__name__)


def make_annotations(cls):
    """Converts class fields to annotations if running with Blender 2.8"""
    if bpy.app.version < (2, 80):
        return cls
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls

classes = (
        LFPropertyGroup,
        lightfield_simulator.OBJECT_OT_show_frustum,
        lightfield_simulator.OBJECT_OT_hide_frustum,
        lightfield_simulator.OBJECT_OT_update_lightfield,
        lightfield_simulator.OBJECT_OT_create_lightfield,
        lightfield_simulator.OBJECT_OT_delete_lightfield,
        lightfield_simulator.OBJECT_OT_render_lightfield,
        import_export.OBJECT_OT_save_lightfield,
        import_export.OBJECT_OT_load_lightfield,
        gui.VIEW3D_OT_lightfield_setup,
        )

def register():
    print("Force reloading the plugin.")
    import imp
    imp.reload(blender_utils)
    imp.reload(gui)
    imp.reload(lightfield_simulator)
    imp.reload(updates)
    imp.reload(import_export)
    print("Registering Lightfield Renderer...")
    for cls in classes:
        make_annotations(cls)
        bpy.utils.register_class(cls)
    bpy.types.Scene.LF = bpy.props.PointerProperty(type=LFPropertyGroup)

def unregister():  # note how unregistering is done in reverse
    del bpy.types.Scene.LF
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
