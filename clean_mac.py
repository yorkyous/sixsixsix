# -* - coding: UTF-8 -* -  
#!/usr/bin/python
#python 2.7以上
# build_libs.py
# Build Libs codes

import io
import os,sys
import os.path
import shutil
import re
import hashlib
import zipfile
import json
import getpass
import datetime
import codecs
import traceback
import time
import math
from xml.dom.minidom import parse
import xml.dom.minidom
from collections import OrderedDict
import pdb
from optparse import OptionParser

_cur_path = os.path.dirname(os.path.realpath(__file__))
_cocos_path = os.path.join(_cur_path, "../..")
_home = os.environ['HOME']

# 需要清理的目录或文件列表
HOME_DEL_DIRS = [
    "Library/Developer/Xcode/DerivedData",
    "Library/Developer/Xcode/iOS DeviceSupport",   #目录下保留版本号最大的SDK其余删掉
    "Library/Developer/Xcode/Archives",
    "Library/Developer/CoreSimulator/Caches",
    "Library/Developer/CoreSimulator/Devices",

    "Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat",
    "Library/Containers/com.tencent.xinWeChat/Data/Library/Caches/com.tencent.xinWeChat",
    "Library/Containers/im.xinda.youdu.mac/Data/Library/Caches",
    "Library/Containers/com.youku.mac/Data/Library/Caches",
    "Library/Containers/com.youku.mac/Data/Playlog",
    "Library/Containers/com.youku.mac/Data/Documents/YTCORE_PLAYER_CACHE/using",
    "Library/Containers/com.tencent.qq/Data/Library/Caches",
    "Library/Containers/com.netease.163music/Data/Caches",
    "Library/Containers/com.taobao.Aliwangwang/Data/Library/Application Support/AliWangwang/80profiles",

    "Library/Caches" # 大小大于500MB的都删掉
]

# 需要忽略的文件或目录名
IGNOR_NAMES = [
    ".DS_Store"
]

# 截取文件名前面x.x的版本号字符串，并通过.分割成数值数组
def get_name_nums(name):
    index = name.find("(")
    name = name[:index]
    nums = []
    while len(name) > 0:
        index = name.find(".")
        if index < 0:
            nums.append(int(name))
            name = ""
        else:
            nums.append(int(name[:index]))
            name = name[index + 1:]
    return nums

# 对比2个数值数组，a>b返回1，a<b返回-1，a=b返回0
def compare_nums(a, b):
    # print("比较名字")
    # print(a)
    # print(b)
    if len(a) == 0 and len(b) == 0:
        return 0
    elif len(a) == 0:
        return -1
    elif len(b) == 0:
        return 1
    i = 0
    while i > -1:
        if a[i] > b[i]:
            return 1
        elif a[i] < b[i]:
            return -1
        elif i == len(a) and i == len(b):
            return 0
        elif i == len(a):
            return -1
        elif i == len(b):
            return 1
        else:
            i = i + 1

# 检测文件目录名是否为忽略的名字
def is_ignore(name):
    for item in IGNOR_NAMES:
        if name == item:
            return True
    return False

# 获取指定目录的大小
def get_path_size(path):
    size = 0.0
    if os.path.isfile(path):
        try:
            size = os.path.getsize(path)
        except:
            return 0.0

        else:
            return size
    try:
        items = os.listdir(path)
    except:
        return size
    else:
        for item in items:
            if is_ignore(item):
                continue
            fp = os.path.join(path, item)
            if os.path.isdir(fp):
                size = size + get_path_size(fp)
            else:
                try:
                    size = size + os.path.getsize(fp)
                except:
                    continue
                else:
                    continue
        return size

# 格式化文件大小数值成字符串，加入单位，保留小数点后2位
def format_size(size):
    if size == None or (not isinstance(size, float) and not isinstance(size, int)):
        return "0Bytes"

    space = 1000.0
    units = ["Bytes", "KB", "MB", "GB"]
    index = 0
    result = 0.0
    while index < len(units) - 1:
        result = size / (space ** (index + 1))
        if result < 1:
            result = index == 0 and int(size) or (size / (space ** index))
            break
        else:
            index = index + 1
            if result == 1:
                break

    # print(result)
    if math.floor(result) == result:
        result = int(result)

    if isinstance(result, float):
        return str.format("%.2f %s" % (result , units[index]))
    else:
        return str.format("%d %s" % (result, units[index]))

# 删除"iOS DeviceSupport"目录下的内容，只保留最后一个版本号
def del_deviceSupport(path):
    size = 0.0
    if not os.path.exists(path):
        return size
    try:
        items = os.listdir(path)
    except:
        return size
    else:
        max_file = ""

        # 找到版本号最大的文件名
        for item in items:
            if is_ignore(item):
                continue
            if len(max_file) == 0:
                max_file = item
                continue
            result = compare_nums(get_name_nums(max_file), get_name_nums(item))
            if result >= 0:
                continue
            else:
                max_file = item

        print("找到了最大的版本号文件名:" + max_file)
        for item in items:
            if is_ignore(item):
                continue
            fp = os.path.join(path, item)
            if item != max_file:
                size = size + del_dir(fp)
        return size

# 删除文件或目录
def del_dir(path, limite = None):
    size = 0.0
    if not os.path.exists(path):
        return size
    if os.path.isfile(path):
        tmpSize = get_path_size(path)
        if limite != None and tmpSize < limite:
            return size
        try:
            os.remove(path)
            # print("移除文件[%s]:%s" % (format_size(tmpSize), path))
        except:
            return size
        else:
            print("移除文件[%s]:%s" % (format_size(size), path))
            return tmpSize
    try:
        items = os.listdir(path)
    except:
        return size
    else:
        for item in items:
            if is_ignore(item):
                continue
            fp = os.path.join(path, item)
            tmpSize = get_path_size(fp)
            if limite != None and tmpSize < limite:
                continue
            if os.path.isdir(fp):
                try:
                    shutil.rmtree(fp)
                    # print("移除目录[%s]:%s" % (format_size(tmpSize), fp))
                except:
                    continue
                else:
                    size = size + tmpSize
                    print("移除目录[%s]:%s" % (format_size(tmpSize), fp))
            else:
                try:
                    os.remove(fp)
                    # print("移除文件[%s]:%s" % (format_size(tmpSize), fp))
                except:
                    continue
                else:
                    size = size + tmpSize
                    print("移除文件[%s]:%s" % (format_size(tmpSize), fp))
        return size

def main():
    total = 0.0
    for path in HOME_DEL_DIRS:
        fp = os.path.join(_home, path)
        index = path.rfind("/")
        if path == "Library/Caches":
            total = total + del_dir(fp, 500 * 1000 * 1000) #  1MB = 1000 * 1000 Bytes
            continue
        if index < 0:
            total = total + del_dir(fp)
            continue

        # print(path[index + 1:])
        if path[index + 1:] == "iOS DeviceSupport":
            total = total + del_deviceSupport(fp)
        else:
            total = total + del_dir(fp)

    print("清理文件总大小[%s]" % format_size(total))

if __name__ == '__main__':
    # parser = OptionParser()
    # parser.add_option("-b", "--bid", dest="bid", help='bundle_id，iOS的BundleID或者Android的包名')
    # (opts, args) = parser.parse_args()
    main()