# -*- coding: utf-8 -*-
"""
parser
------
解析“My Clippings.txt”文档内容，获取书籍名称、标注时间、位置、内容等属性，
并存储至数据库中。
"""
import os
import re
import hashlib
import json
from collections import defaultdict
from config import UPLOAD_FOLDER, JSONFILE_FOLDER


# 定义可以对文本进行解析的类
class ClipsParser(object):
    def __init__(self, filename):
        self.__full_filename = os.path.join(UPLOAD_FOLDER, filename)
        self.__filename = filename

    __SPLIT_LINE = '==========\n'
    __USELESS_PREFIX = '\ufeff'

    def __getclips(self):
        """读取'My Clippings.txt'文件，解析并将‘标注’存入列表中。
        """
        # 因为 My Clippings.txt 不是unicode编码，打开时需要设置编码方式
        with open(self.__full_filename, 'r', encoding='utf-8') as f:
            clips = f.read()
        return [c for c in clips.split(self.__SPLIT_LINE) if c]

    def __parseclips(self, clips):
        """将所有的标注解析至一个字典中，字典schema如下：
        {
            bookname: {
                index: {
                    'type': value,
                    'pos': value,
                    'time': value,
                    'content': value
                },
                ...
            },
            ...
        }
        """
        book_clips = defaultdict(dict)
        for num, clip in enumerate(clips):
            clip = [n for n in clip.split('\n') if n]
            # clip对应的书籍名称
            bookname = clip[0].lstrip(self.__USELESS_PREFIX).strip()
            # 使用md5值作为每个clip的独特id
            index_md5 = hashlib.md5()
            index_md5.update(str(clip).encode('utf-8'))
            index = index_md5.hexdigest()
            # 获取clip的类型、标注位置和标注时间
            attrs = re.match(
                r'.*您在(.{1}\s[0-9-]+\s.{1})?.*?(#[0-9-]+)?.?的(.*)?\s\|\s添加于\s(.*)$',
                clip[1])
            # 由于“标注位置”的具体形式有三种，所以这里需要进行判断
            if attrs.group(1):
                if attrs.group(2):
                    pos = attrs.group(1) + '(' + attrs.group(2) + ')'
                else:
                    pos = attrs.group(1)
                clip_type = attrs.group(3)
                time = attrs.group(4)
            else:
                pos = attrs.group(2)
                clip_type = attrs.group(3)
                time = attrs.group(4)
            # clip对应的具体内容
            try:
                content = clip[2]
            except:
                content = None

            book_clip = {'type': clip_type, 'pos': pos,
                         'time': time, 'content': content}

            book_clips[bookname].update({index: book_clip})

        return book_clips

    def parse(self):
        clips = self.__getclips()
        book_clips = self.__parseclips(clips)
        # 保存json格式文件作为备份。
        jsonname = self.__filename.split('.')[0] + '.json'
        jsonfile = os.path.join(JSONFILE_FOLDER, jsonname)
        with open(jsonfile, 'w') as f:
            json.dump(book_clips, f)
        return book_clips


# Testing
if __name__ == '__main__':
    cp = ClipsParser(filename)
    clips = cp.parse()
