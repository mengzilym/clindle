# 简介

Clindle (k**indle** **cli**ppings) 是一个管理Kindle标注/笔记/书签的网页应用。目前处于开发阶段。
后端使用Python编写，基于Flask框架+SQLite数据库，前端只是简单的HTML+CSS。

# 功能

- [x] 上传“My Clippings.txt”文档并进行解析，将解析后的内容存入json文件和SQLite数据库，json文件用作备份。
> 解析内容包括书籍名称、作者、标注类型（标注/笔记/书签）、标注时间、位置。
- [x] 以书籍列表的形式查看各书籍的标注情况，如示例图1所示
- [x] 查看单本书籍的标注内容，及对应的位置、标注时间，如示例图2所示
- [ ] 获取书籍封面：本来想通过亚马逊的Product Advertising API获取书籍信息，结果亚马逊商业联盟申请没通过 :( 打算通过直接解析搜索结果页获取书籍封面url
- [ ] 编辑笔记
- [ ] 以文本或图片形式分享标注/笔记
- [ ] 更改书籍列表的排序/显示方式

远期计划

- [ ] 实现用户管理
- [ ] 在线部署对外提供服务
- [ ] 对接微信小程序

# 使用

参照`requirements.txt`搭建Python环境并安装依赖包。

运行`clindle.py`：

```
>> python clindle.py
```

在根目录的“test-file”文件夹中有个供测试使用的“My clippings.txt”文件，访问`http://127.0.0.1:5000/`并上传文件。然后就可以浏览Kindle标注内容了。

# 示例截图

![截图1](https://raw.githubusercontent.com//mengzilym/clindle/master/static/images/screenshot1.jpg "图1")

![截图2](https://raw.githubusercontent.com//mengzilym/clindle/master/static/images/screenshot2.jpg "图2")
