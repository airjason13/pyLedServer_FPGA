import os

from flask_routes.routes_ops import get_sleep_mode_default, get_brightness_mode_default, get_target_city_default, \
    get_city_list, get_reboot_mode_default
from global_def import log, internal_media_folder, PlaylistFolder, play_type, ThumbnailFileFolder
from flask import render_template, send_from_directory
import hashlib
import glob
import json
from flask_wtf import Form
from wtforms import validators, RadioField, SubmitField, IntegerField, SelectField, StringField, TimeField, DateField, \
    DateTimeField
from main import app

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

mp4_extends = internal_media_folder + "/*.mp4"
jpeg_extends = internal_media_folder + "/*.jpeg"
jpg_extends = internal_media_folder + "/*.jpg"
png_extends = internal_media_folder + "/*.png"
webp_extends = internal_media_folder + '/*.webp'
playlist_extends = internal_media_folder + PlaylistFolder + "*.playlist"


def find_file_maps():
    maps = {}

    # log.debug("mp4_extends = %s", mp4_extends)
    # need to add png/jpg/jpeg
    for file_name in sorted(glob.glob(mp4_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name
    for file_name in sorted(glob.glob(jpg_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name
    for file_name in sorted(glob.glob(jpeg_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name
    for file_name in sorted(glob.glob(png_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name

    return maps


def get_file_list() -> list:
    file_list = []
    for fname in sorted(glob.glob(mp4_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)
    for fname in sorted(glob.glob(jpg_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)
    for fname in sorted(glob.glob(jpeg_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)
    for fname in sorted(glob.glob(png_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)

    return file_list

def get_single_file_default() -> str:
    try:
        with open(os.getcwd() + "/static/default_launch_type.dat", "r") as launch_type_config_file:
            tmp = launch_type_config_file.read()
            default_launch_type_int = int(tmp.split(":")[0])
            default_launch_type_params_str = tmp.split(":")[1]
            if default_launch_type_int == play_type.play_single:
                log.debug("get_single_file_default :"+ default_launch_type_params_str)
                return default_launch_type_params_str
            else:
                file_list = get_file_list()
                log.debug("file_list[0] :" + file_list[0])
                return file_list[0]
    except Exception as e:
        log.debug(e)
    file_list = get_file_list()
    return file_list[0]

def find_playlist_maps() -> map:
    playlist_nest_dict = {}
    for playlist_tmp in sorted(glob.glob(playlist_extends)):
        # log.debug("playlist_tmp = %s", playlist_tmp)
        if os.path.isfile(playlist_tmp):
            playlist_name_list = playlist_tmp.split("/")
            playlist_name = playlist_name_list[len(playlist_name_list) - 1]
            playlist_nest_dict[playlist_name] = {}
            f = open(playlist_tmp)
            lines = f.readlines()
            for line in lines:
                line = line.strip("\n")
                fname_url = line.split("/")
                fname = fname_url[len(fname_url) - 1]
                prefix_video_name = fname.split(".")[0]
                # log.debug("video_extension = %s", video_extension)
                preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
                # bug
                # if the fname is the same as item before, there is only one in nest!!!!!
                playlist_nest_dict[playlist_name][fname] = preview_file_name

    # print(playlist_nest_dict)

    return playlist_nest_dict


@app.route('/get_thumbnail/<filename>')
def route_get_thumbnail(filename):
    # log.debug("fname = %s", filename)
    return send_from_directory(internal_media_folder + ThumbnailFileFolder, filename, as_attachment=True)


class BrightnessAlgoForm(Form):

    style = {'class': 'ourClasses', 'style': 'font-size:24px;color:white', }
    brightness_mode_switcher = RadioField(

            label="Brightness Mode",
            id="brightness_mode_switcher",
            choices=[('Fix Mode', 'Fix Mode'),
                     ('Time Mode', 'Time Mode'),
                     ('ALS Mode', 'ALS Mode'),
                     ('Test Mode', 'Test Mode')],
            default=get_brightness_mode_default(),

            render_kw=style,

        )
    # style = {'class': 'ourClasses', 'style': 'font-size:24px;color:white', }
    sleep_mode_switcher = RadioField(
        "Sleep Mode",
        id="sleep_mode_switcher",
        choices=[('Disable', 'Disable'),
                 ('Enable', 'Enable'),
                 ],
        default=get_sleep_mode_default(),
        render_kw=style,

    )
    city_style = {'class': 'ourClasses', 'style': 'font-size:24px;color:black;size:320px;width:200px', }
    city_selectfiled = SelectField(
        "City",
        id="city_selected",
        # choices=get_city_hash_map(),
        choices=get_city_list(),
        default=get_target_city_default(),
        render_kw=city_style,
    )

    reboot_style = {'class': 'ourClasses', 'style': 'font-size:24px;color:black;size:320px;width:200px', }
    reboot_mode_switcher = RadioField(
        "Reboot Mode",
        id="reboot_mode_switcher",
        choices=[('Disable', 'Disable'),
                 ('Enable', 'Enable'),
                 ],
        default=get_reboot_mode_default(),
        render_kw=style,
    )


def refresh_template():
    maps = find_file_maps()
    playlist_nest_dict = find_playlist_maps()

    playlist_js_file = open("static/playlist.js", "w")
    playlist_json = json.dumps(playlist_nest_dict)
    playlist_js_file.write("var jsonstr = " + playlist_json)
    playlist_js_file.flush()
    playlist_js_file.truncate()
    playlist_js_file.close()

    return render_template("index.html", files=maps)


@app.route("/")
def index():
    log.debug("flask route index")
    return refresh_template()
