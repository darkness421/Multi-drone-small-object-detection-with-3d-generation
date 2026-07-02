#!/usr/bin/env python3
"""Minimal Vulkan device enumeration without vulkaninfo.

This avoids installing packages on shared servers while still checking whether
Isaac/Kit should be able to see NVIDIA Vulkan devices.
"""

from __future__ import annotations

import ctypes
import os
import sys


VK_SUCCESS = 0
VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO = 1
VK_MAX_PHYSICAL_DEVICE_NAME_SIZE = 256
VK_UUID_SIZE = 16
VK_LUID_SIZE = 8


class VkInstanceCreateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),
        ("pNext", ctypes.c_void_p),
        ("flags", ctypes.c_uint32),
        ("pApplicationInfo", ctypes.c_void_p),
        ("enabledLayerCount", ctypes.c_uint32),
        ("ppEnabledLayerNames", ctypes.c_void_p),
        ("enabledExtensionCount", ctypes.c_uint32),
        ("ppEnabledExtensionNames", ctypes.c_void_p),
    ]


class VkPhysicalDeviceLimits(ctypes.Structure):
    _fields_ = [("_", ctypes.c_byte * 504)]


class VkPhysicalDeviceSparseProperties(ctypes.Structure):
    _fields_ = [("_", ctypes.c_byte * 20)]


class VkPhysicalDeviceProperties(ctypes.Structure):
    _fields_ = [
        ("apiVersion", ctypes.c_uint32),
        ("driverVersion", ctypes.c_uint32),
        ("vendorID", ctypes.c_uint32),
        ("deviceID", ctypes.c_uint32),
        ("deviceType", ctypes.c_uint32),
        ("deviceName", ctypes.c_char * VK_MAX_PHYSICAL_DEVICE_NAME_SIZE),
        ("pipelineCacheUUID", ctypes.c_uint8 * VK_UUID_SIZE),
        ("limits", VkPhysicalDeviceLimits),
        ("sparseProperties", VkPhysicalDeviceSparseProperties),
    ]


DEVICE_TYPES = {
    0: "OTHER",
    1: "INTEGRATED_GPU",
    2: "DISCRETE_GPU",
    3: "VIRTUAL_GPU",
    4: "CPU",
}


def version_tuple(version: int) -> tuple[int, int, int]:
    return (version >> 22, (version >> 12) & 0x3FF, version & 0xFFF)


def main() -> int:
    print(f"DISPLAY={os.environ.get('DISPLAY', '')}")
    print(f"XAUTHORITY={os.environ.get('XAUTHORITY', '')}")
    print(f"VK_ICD_FILENAMES={os.environ.get('VK_ICD_FILENAMES', '')}")
    print(f"VK_LAYER_PATH={os.environ.get('VK_LAYER_PATH', '')}")

    try:
        vulkan = ctypes.CDLL("libvulkan.so.1")
    except OSError as exc:
        print(f"ERROR: failed to load libvulkan.so.1: {exc}", file=sys.stderr)
        return 2

    create_info = VkInstanceCreateInfo(
        VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        None,
        0,
        None,
        0,
        None,
        0,
        None,
    )
    instance = ctypes.c_void_p()

    vk_create_instance = vulkan.vkCreateInstance
    vk_create_instance.argtypes = [
        ctypes.POINTER(VkInstanceCreateInfo),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    vk_create_instance.restype = ctypes.c_int32

    rc = vk_create_instance(ctypes.byref(create_info), None, ctypes.byref(instance))
    if rc != VK_SUCCESS:
        print(f"ERROR: vkCreateInstance failed rc={rc}", file=sys.stderr)
        return 3

    try:
        vk_enum = vulkan.vkEnumeratePhysicalDevices
        vk_enum.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
        vk_enum.restype = ctypes.c_int32

        count = ctypes.c_uint32(0)
        rc = vk_enum(instance, ctypes.byref(count), None)
        if rc != VK_SUCCESS:
            print(f"ERROR: vkEnumeratePhysicalDevices count failed rc={rc}", file=sys.stderr)
            return 4

        devices = (ctypes.c_void_p * count.value)()
        rc = vk_enum(instance, ctypes.byref(count), ctypes.cast(devices, ctypes.c_void_p))
        if rc != VK_SUCCESS:
            print(f"ERROR: vkEnumeratePhysicalDevices list failed rc={rc}", file=sys.stderr)
            return 5

        vk_props = vulkan.vkGetPhysicalDeviceProperties
        vk_props.argtypes = [ctypes.c_void_p, ctypes.POINTER(VkPhysicalDeviceProperties)]
        vk_props.restype = None

        print(f"VULKAN_DEVICE_COUNT={count.value}")
        for idx, dev in enumerate(devices[: count.value]):
            props = VkPhysicalDeviceProperties()
            vk_props(dev, ctypes.byref(props))
            name = props.deviceName.decode("utf-8", errors="replace").rstrip("\x00")
            api = ".".join(str(v) for v in version_tuple(props.apiVersion))
            dtype = DEVICE_TYPES.get(props.deviceType, str(props.deviceType))
            print(
                f"{idx}: name={name} type={dtype} "
                f"vendor=0x{props.vendorID:04x} device=0x{props.deviceID:04x} api={api}"
            )
    finally:
        if instance:
            vulkan.vkDestroyInstance.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            vulkan.vkDestroyInstance(instance, None)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
