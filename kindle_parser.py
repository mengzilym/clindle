# -*- coding: utf-8 -*-
"""
parser
------
解析“My Clippings.txt”文档内容，获取书籍名称、标注时间、位置、内容等属性，
并存储至数据库中。
"""
import hashlib
import json
import os
import re
from collections import defaultdict

from config import JSONFILE_FOLDER, UPLOAD_FOLDER


# 定义可以对文本进行解析的类
class ClipsParser(object):
    def __init__(self, filename):
        self.__full_filename = os.path.join(UPLOAD_FOLDER, filename)
        self.__filename = filename

    __SPLIT_LINE = '==========\n'
    __USELESS_PREFIX = '\ufeff'

    def _format_time(self, timestr):
        """format original kindle date&time:
        '2017年1月1日星期日 下午3:23:07' to 'YYYY-MM-DD HH:MM:SS'.
        """
        patn = re.compile(r'(\d*)年(\d*)月(\d*)日.*(.{1})午(\d*):(\d*):(\d*)')
        tiktok = patn.match(timestr)
        year = tiktok.group(1)
        timelist = [year] + \
            ['{:0>2}'.format(tiktok.group(i)) for i in (2, 3, 5, 6, 7)]
        if tiktok.group(4) == '下':
            if tiktok.group(5) != '12':
                timelist[3] = str(int(timelist[3]) + 12)
        timestring = '-'.join(timelist[:3]) + ' ' + ':'.join(timelist[-3:])
        return timestring

    def _format_pos(self, pos):
        """format original kindle position str to sortable number.
        There are 4 kinds of original position str:
        1: '#1-2'|'#1';
        2: '第 1 页(#1-2)'|'第 1 页(#1)'
        3: both 1 and 2;
        4: '第 1-2 页'|'第 1 页';
        """
        patn = re.compile(r'(?:.*#(\d+)-?(\d+)?)|(?:第(\d+)-?(\d+)?)')
        posptn = patn.match(pos.replace(' ', ''))
        if posptn.group(1):
            s_pos = posptn.group(1)
            e_pos = posptn.group(2)
        else:
            s_pos = posptn.group(3)
            e_pos = posptn.group(4)
        return (int(s_pos), int(e_pos)) if e_pos else (int(s_pos), int(s_pos))

    def _getclips(self):
        """读取'My Clippings.txt'文件，解析并将‘标注’存入列表中。
        """
        # 因为 My Clippings.txt 不是unicode编码，打开时需要设置编码方式
        with open(self.__full_filename, 'r', encoding='utf-8') as f:
            clips = f.read()
        return [c for c in clips.split(self.__SPLIT_LINE) if c]

    def _parseclips(self, clips):
        """将所有的标注解析至一个字典中，字典schema如下：
        {
            bookname: {
                index: {
                    'type': value,
                    'pos': value,
                    'start_pos': value,
                    'end_pos': value,
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
            attrs = re.match(r'.*您在(.{1}\s[0-9-]+\s.{1})?.*?(#[0-9-]+)?.?'
                             '的(.*)?\s\|\s添加于\s(.*)$', clip[1])
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
            # 标注、笔记对应的具体内容
            try:
                content = clip[2]
            except:
                content = None

            start_pos, end_pos = self._format_pos(pos)
            book_clip = {'type': clip_type, 'pos': pos,
                         'start_pos': start_pos, 'end_pos': end_pos,
                         'time': self._format_time(time), 'content': content}

            book_clips[bookname].update({index: book_clip})

        return book_clips

    def parse(self):
        clips = self._getclips()
        book_clips = self._parseclips(clips)
        # 保存json格式文件作为备份。
        jsonname = self.__filename.split('.')[0] + '.json'
        jsonfile = os.path.join(JSONFILE_FOLDER, jsonname)
        with open(jsonfile, 'w') as f:
            json.dump(book_clips, f)
        return book_clips


# Testing
if __name__ == '__main__':
    filename = '20170609_010107_My_Clippings.txt'
    cp = ClipsParser(filename)
    timestr1 = '2015年12月11日星期五 下午12:03:37'
    timestr2 = '2015年12月1日星期二 下午4:17:03'
    timestr3 = '2016年3月28日星期一 上午9:51:14'
    assert cp._format_time(timestr1) == '2015-12-11 12:03:37'
    assert cp._format_time(timestr2) == '2015-12-01 16:17:03'
    assert cp._format_time(timestr3) == '2016-03-28 09:51:14'
    pos1 = '#10190-10191'
    pos2 = '#6803'
    pos3 = '第799页(#11659-11661)'
    pos4 = '第32页(#456)'
    pos5 = '第34-35页'
    pos6 = '第45页'
    assert cp._format_pos(pos1) == (10190, 10191)
    assert cp._format_pos(pos2) == (6803, 6803)
    assert cp._format_pos(pos3) == (11659, 11661)
    assert cp._format_pos(pos4) == (456, 456)
    assert cp._format_pos(pos5) == (34, 35)
    assert cp._format_pos(pos6) == (45, 45)
    print('NO BUGS ON FORMATTING.')
    # clips = cp.parse()
