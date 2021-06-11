import os
import sys

project_root = [path for path in sys.path if path.endswith("\\src")][0].replace("\\src", "")
resources_root = "res"
resources_test_data = "test-data"
resources_out = "out"
resources_out_audio = "audio"

print("project root set to: " + project_root)


def get_resources_out_path(path_ext="") -> str:
    return os.path.join(project_root, resources_root, resources_out, path_ext)


def get_resources_out_audio_path(path_ext="") -> str:
    return os.path.join(project_root, resources_root, resources_out, resources_out_audio, path_ext)


def get_resources_root_path(path_ext="") -> str:
    return os.path.join(project_root, resources_root, path_ext)


def get_resources_root_test_data_path(path_ext="") -> str:
    return os.path.join(project_root, resources_root, resources_test_data, path_ext)
