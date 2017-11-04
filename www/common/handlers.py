#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'yancheng'


'''
	url handlers
	注：Python从3.5版本开始为asyncio提供了async和await的新语法，替换以前的@asyncio.coroutine 和 yield from；
'''

import re, time, json, logging, hashlib, base64, asyncio

from common import markdown2
from aiohttp import web

from common.coroweb import get, post
from common.apis import APIValueError, APIResourceNotFoundError, Page

from model import UsersModel, BlogsModel, CommentsModel, CategoryModel
from config.config import configs

from common.orm import select



COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await UsersModel.Users.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

#============================用户浏览页===================================
async def getBlogList(category_id='', ym='', page='1'):
    page_index = get_page_index(page)
    if category_id!='':
        num = await BlogsModel.Blogs.findNumber('count(id)', 'category_id=?', [category_id])
    elif ym!='':
        num = await BlogsModel.Blogs.findNumber('count(id)', 'from_unixtime(created_at,"%%Y-%%m")=?', [ym])
    else:
        num = await BlogsModel.Blogs.findNumber('count(id)')

    page = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        if category_id!='':
            blogs = await BlogsModel.Blogs.findAll('category_id=?',[category_id], orderBy='created_at desc', limit=(page.offset, page.limit))
        elif ym!='':
            blogs = await BlogsModel.Blogs.findAll('from_unixtime(created_at,"%%Y-%%m")=?', [ym], orderBy='created_at desc', limit=(page.offset, page.limit))
        else:
            sql = 'select Blogs.*, count(Comments.blog_id) as comments_num from Blogs LEFT JOIN Comments ON Blogs.id = Comments.blog_id where Blogs.category_id=?  GROUP BY Blogs.id ORDER BY Blogs.created_at DESC LIMIT ?,?';
            blogs = await select(sql,[1, page.offset, page.limit]);
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }


#首页文章列表
@get('/')
async def index(*, page='1'):
    filterBlogs = await getBlogList(page=page);
    filterBlogs['searchTitle'] = "全部";
    return filterBlogs;

#首页按归档日期查看
@get('/blogs/date/{ym}')
async def index_date(*, ym='', page='1'):
    filterBlogs = await getBlogList(ym=ym, page=page);
    filterBlogs['searchTitle'] = ym;
    return filterBlogs;

#首页按分类查看
@get('/blogs/category/{id}')
async def index_category(*, page='1', id=0, name=''):
    filterBlogs = await getBlogList(category_id=id, page=page);
    categoryinfo = await CategoryModel.Category.find(id)
    filterBlogs['searchTitle'] = categoryinfo.name;
    return filterBlogs;

#注册页面
@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

#登录界面
@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }

#用户退出界面
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

#====================================后端API==================================
#用户认证
@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await UsersModel.Users.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

#用户注册
@post('/api/users')
async def api_register_user(*, email, name, passwd):
    #这里注意*号后面必须是关键字传参
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await UsersModel.Users.findAll('email=?', [email])
    if len(users) > 0:
        raise APIValueError('email', 'Email is already in use.')
    uid = UsersModel.next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = UsersModel.Users(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='/static/img/user.png?cache=%s' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

#获取文章列表
@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await BlogsModel.Blogs.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await BlogsModel.Blogs.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for b in blogs:
        categoryinfo = await CategoryModel.Category.find(b.category_id)
        b.category_name = categoryinfo.name if categoryinfo!=None else ''

    return dict(page=p, blogs=blogs)

#创建文章
@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = BlogsModel.Blogs(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog

#修改文章
@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content,category_id):
    check_admin(request)
    blog = await BlogsModel.Blogs.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    blog.category_id = int(category_id)
    await blog.update()
    return blog

#获取单篇文章
@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await BlogsModel.Blogs.find(id)
    return blog

#删除单篇文章
@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)
    blog = await BlogsModel.Blogs.find(id)
    await blog.remove();
    return dict(id=id)


#获取用户列表
@get('/api/users')
async def api_users(*, page='1'):
    page_index = get_page_index(page)
    num = await UsersModel.Users.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await UsersModel.Users.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, users=users)

#获取评论列表数据
@get('/api/comments')
async def api_comments(*, page='1'):
    page_index = get_page_index(page)
    num = await CommentsModel.Comments.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await CommentsModel.Comments.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

#提交评论
@post('/api/blogs/{id}/comments')
async def api_comments_blog(id, request, *, content):
    check_admin(request)
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    
    blog = await BlogsModel.Blogs.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')

    comment = CommentsModel.Comments(blog_id=id, user_id=request.__user__.id, user_name=request.__user__.name, content=content.strip(), user_image=request.__user__.image)
    await comment.save()
    return comment

#删除评论
@post('/api/comments/{id}/delete')
async def api_delete_comments(request, *, id):
    check_admin(request)
    comments = await CommentsModel.Comments.find(id)
    if comments is None:
        raise APIResourceNotFoundError('Comment')
    await comments.remove();
    return dict(id=id)

#获取分类列表
@get('/api/category')
async def api_category():
    category = await CategoryModel.Category.findAll(orderBy='orders asc')
    for c in category:
        userinfo = await UsersModel.Users.find(c.user_id)
        c.user_name = userinfo.name

    return dict(category=category)

#添加分类
@post('/api/category')
async def api_create_category(request, *, name, orders):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', '分类名称不能为空！')
    if not str(orders).strip():
        raise APIValueError('orders', '分类顺序不能为空！')

    category_exists = await CategoryModel.Category.findAll('name=?', [name])
    if len(category_exists) > 0:
        raise APIValueError('name', '该分类已存在！')

    category = CategoryModel.Category(name=name, orders=orders, user_id=request.__user__.id, path_id='/')
    last_insertid = await category.save()

    category.id = last_insertid
    category.user_name = request.__user__.name
    category.actionType = 'create'
    return category

#修改分类
@post('/api/category/{id}')
async def api_update_category(id, request, *, name, orders):
    check_admin(request)
    category = await CategoryModel.Category.find(id)
    if not name or not name.strip():
        raise APIValueError('name', '分类名称不能为空！')
    if not str(orders).strip():
        raise APIValueError('orders', '分类顺序不能为空！')

    category_exists = await CategoryModel.Category.findAll('name=? and id !=?', [name, id])
    if len(category_exists) > 0:
        raise APIValueError('name', '该分类已存在！')

    category.name = name.strip()
    category.orders = orders
    category.user_name = request.__user__.name
    await category.update()
    category.actionType = 'update'
    return category


#删除分类
@post('/api/category/{id}/delete')
async def api_delete_comments(request, *, id):
    check_admin(request)
    category = await CategoryModel.Category.find(id)
    if category is None:
        raise APIResourceNotFoundError('Category')
    await category.remove();
    return dict(id=id)


#获取每月归档日志
@get('/api/reportMonthBlogs')
async def api_reportMonthBlogs():
    reportBlogs = {}
    blogs = await BlogsModel.Blogs.findAll(orderBy='created_at desc')
    for b in blogs:
        yearMon = time.strftime("%Y-%m", time.localtime(b.created_at))
        reportBlogs[yearMon] = reportBlogs.get(yearMon, 0) + 1

    return reportBlogs
#===============================管理页面=======================

#文章详情页
@get('/manage/blogs')
async def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }

#创建文章
@get('/manage/blogs/create')
async def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }

#修改文章
@get('/manage/blogs/edit')
async def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % id
    }

#用户列表页
@get('/manage/users')
async def manage_users(*, page='1'):
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }

#评论列表
@get('/manage/comments')
async def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }

#查看文章评论
@get('/blog/{id}')
async def blog(*, id):
    blog = await BlogsModel.Blogs.find(id)
    #更新阅读数
    blog.read_total += 1
    await blog.update()

    comments = await CommentsModel.Comments.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

#查看分类列表
@get('/manage/category')
async def manage_category():
    return {
        '__template__': 'manage_category.html'
    }