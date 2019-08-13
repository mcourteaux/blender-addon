import bpy


def set_object_selected(obj, selected=True, set_active=False):
    obj.hide_select = False
    if bpy.app.version < (2, 80):
        obj.select = selected
    else:
        obj.select_set(selected)
    if set_active:
        if bpy.app.version < (2, 80):
            bpy.context.scene.objects.active = obj
        else:
            bpy.context.view_layer.objects.active = obj

def set_object_hidden(obj, hidden=True):
    try:
        obj.hide = hidden
    except AttributeError:
        obj.hide_viewport = hidden

def move_to_collection(obj, collection):
    if bpy.app.version < (2, 80):
        return
    collection.objects.link(lightfield)

