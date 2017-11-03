python3web
===========================
Mainly used to learn python3, how to build a mini web framework and implement a simple personal blog!

## function list
* Article list / management
* Article details
* Article archives
* Article classification / management
* log in Register
* User Management
* Adaptive support for mobile terminals
    
## Development environment
centos6.5+python3.5.1+mysql5.7+vue2+uikit3
## Blog to build

1. Install the python extension module via pip, as follows:
  ```Python
  >pip3 install aiohttp
  >pip3 install aiomysql
  >pip3 install jinja2
  >pip3 install watchdog
  ```
2. Drop the code down to the development directory and execute the database sql statement.

3. Modify the connection data configuration `www/config/config_default.py` and `config_override.py`

4. Modify the server ip address（`www/app.py` turn up `create_server` Modify ip for the current server ip）

4. In the www directory `./pymonitor.py app.py`
5. View blog by browser!
   ![](https://github.com/yanchengdegithub/python3web/raw/master/www/other/py_blog_index.png)

> Note: If the database and the server can not be accessed may be due to iptables block!


