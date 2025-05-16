# Flask SQLite 用户管理系统

这是一个使用 Flask 框架和 SQLite 数据库构建的简单用户管理系统，用于学习在 Flask 中使用 SQLite 数据库。

## 功能特点

- 用户注册和登录功能
- 个人信息管理
- 用户列表展示
- 用户信息增删改查

## 技术栈

- 后端：Flask
- 数据库：SQLite
- 前端：HTML5, CSS3, JavaScript

## 如何运行

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 启动应用

```bash
python app.py
```

3. 打开浏览器访问

```
http://localhost:5000
```

## 项目结构

```
flask_sqlite_demo/
├── app.py               # Flask 应用主文件
├── instance/            # SQLite 数据库存储目录
│   └── users.db         # 用户数据库
├── static/              # 静态文件
│   ├── css/             # CSS 样式文件
│   │   └── style.css    # 主样式文件
│   └── js/              # JavaScript 文件
│       └── script.js    # 主脚本文件
├── templates/           # HTML 模板文件
│   ├── base.html        # 基础模板
│   ├── index.html       # 首页
│   ├── login.html       # 登录页面
│   ├── register.html    # 注册页面
│   ├── dashboard.html   # 用户仪表盘
│   └── users.html       # 用户列表页面
└── requirements.txt     # 项目依赖
```

## 学习要点

- Flask 路由和视图函数
- SQLite 数据库连接和操作
- Flask 表单处理和验证
- 用户认证和会话管理
- Flask 模板系统
- 响应式前端设计 