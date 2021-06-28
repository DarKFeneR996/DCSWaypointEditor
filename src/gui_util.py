# maps UI text : internal type for airframe pulldown menus in the ui.
#
airframe_map = { "A-10C Warthog" : "warthog",
                 "AV-8B Harrier" : "harrier",
                 "F-14A/B Tomcat" : "tomcat",
                 "F-16C Viper" : "viper",
                 "F/A-18C Hornet" : "hornet",
                 "M-2000C Mirage" : "mirage"
}

# return list of supported airframes. second token (" " separated) of items is internal name.
#
def airframe_list():
    return list(airframe_map.keys())

# convert ui airframe text to internal airframe type.
#  
def airframe_ui_text_to_type(ui_text):
    type = airframe_map[ui_text]
    if type is None:
        type = "viper"
    return type

# convert interanl airframe type to text suitable for ui
#
def airframe_type_to_ui_text(type):
    hits = [k for k,v in airframe_map.items() if v == type]
    if (len(hits) == 0):
        hits = ["F-16C Viper"]
    return hits[0]