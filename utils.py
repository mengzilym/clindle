import re
import sqlite3
from config import DATABASE
from pypinyin import lazy_pinyin


# 将‘标注’存储至数据库
def save2db(clips):
    """将解析得到的clips字典对象，保存到数据库中。
    每次重新上传'My Clippings.txt'时，重新创建数据库里的表。
    问题：如果要“获取封面”，可以考虑建立一个缓存文件夹，缓存之前已经获取到的封面图片
    """
    error = None
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    with open('schema.sql', 'r') as f:
        cur.executescript(f.read())

    def _sep_t_a(title):
        """将原始title中的作者姓名分离出来。
        此功能放在 kindle_parser.py 更好，但是考虑到还要调整 clips 字典的结构，
        就暂时懒得改了。
        """
        if not title.endswith(')'):
            author = None
        else:
            ptn = r'.*(\([^()]*\))$'
            PTN_L = r'\(.*?'
            PTN_R = r'.*?\)'
            for i in range(5):
                author_match = re.match(ptn, title)
                if author_match:
                    author = author_match.group(1)[1:-1]
                    title = title[:-len(author)-2]
                    break
                else:
                    ptn = ptn[:3] + PTN_L + ptn[3:-2] + PTN_R + ptn[-2:]
        return (title, author)

    def _titles():
        for title in clips.keys():
            yield _sep_t_a(title)

    try:
        # 将书籍名称存入Books表中
        cur.executemany('insert into Books(title, author) values(?, ?);',
                        _titles())
        # Insert values into Clips, Notes, Marks tables.
        for title, clipsofonebook in clips.items():
            title, _ = _sep_t_a(title)
            cur.execute('select id from Books where title = ?;', (title,))
            bookid = cur.fetchone()[0]
            notes = {}
            for clip in clipsofonebook.values():
                # save '标注' clips to Clips table.
                # warning: the 'content' of '标注' can be 'null' :<
                if clip['type'] == '标注':
                    cur.execute(
                        'insert into Clips values(null, ?, ?, ?, ?, ?);',
                        (clip['pos'], clip['index_pos'], clip['time'],
                         clip['content'], bookid))
                # save '书签' clips to Marks table.
                elif clip['type'] == '书签':
                    cur.execute(
                        'insert into Marks values(null, ?, ?, ?, ?);',
                        (clip['pos'], clip['index_pos'], clip['time'], bookid))
                else:
                    notes[clip['time']] = clip
            # save '笔记' clips to Notes table.
            if notes:
                for t, clip in notes.items():
                    cur.execute('select id from Clips where time = ?;', (t,))
                    clipid = cur.fetchone()[0]
                    cur.execute(
                        'insert into Notes values(null, ?, ?, ?, ?, ?);',
                        (clip['pos'], clip['time'], clip['content'],
                         bookid, clipid))
    except sqlite3.Error:
        conn.rollback()
        error = ('Failed to save data to database :(')
    conn.commit()
    conn.close()
    return error


# collation function
def collate_pinyin(t1, t2):
    """working with 'order by' in sql statement,
    making it possible to order by chinese characters.
    """
    py_t1 = ''.join(lazy_pinyin(t1))
    py_t2 = ''.join(lazy_pinyin(t2))
    if py_t1 == py_t2:
        return 0
    elif py_t1 < py_t2:
        return -1
    else:
        return 1
