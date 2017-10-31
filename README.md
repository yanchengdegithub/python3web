python3web
===========================
主要用于学习python3，怎样搭建一个迷你web框架，并实现一个简单的个人博客！！！


## 功能列表
* 文章列表/管理
* 文章详情
* 文章归档
* 文章分类/管理
* 登录、注册
* 用户管理
* 自适应支持移动终端
    
## 开发环境
centos6.5+python3.5.1+mysql5.7+vue2+uikit3
## 准备好环境之后

1. 通过pip安装python扩展模块，如下：
  ```Python
  >pip3 install aiohttp
  >pip3 install aiomysql
  >pip3 install jinja2
  >pip3 install watchdog
  ```
2. 将代码down到开发目录，并执行数据库sql语句。

3. 修改连接数据配置www/config/config_default.py及config_override.py

4. 修改服务器ip地址（www/app.py找到create_server修改ip为当前服务器ip）

4. 在www目录下执行 ./pymonitor.py app.py
5. 通过浏览器查看博客！！！


> 注意：如果数据库及服务器无法访问可能是因为iptables的阻止！

