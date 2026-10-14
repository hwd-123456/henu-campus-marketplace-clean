# 登录测试指南

本文说明如何在本地启动“河大同享”前后端，并进入登录后的用户界面。

## 1. 环境要求

- Node.js 18 或更高版本（推荐 Node.js 20 LTS）
- Python 3.12 或更高版本
- MongoDB 7/8 或 MongoDB Atlas（可选）

没有 MongoDB 时，页面和登录流程仍可用于演示；后端重启后，临时用户数据不会保留。

## 2. 获取项目

在终端中执行：

```powershell
git clone https://github.com/hwd-123456/henu-campus-marketplace-clean.git
cd henu-campus-marketplace-clean
```

如果已经下载过项目，只需要进入项目根目录。项目根目录必须同时包含 `package.json`、`frontend` 和 `backend`。

## 3. 安装依赖

```powershell
npm install
npm run install:frontend
```

创建后端 Python 环境：

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

如果电脑有多个 Python 版本，可以用 Python 3.12 的完整路径执行上面的 `-m venv` 命令。创建成功后，必须能看到 `backend/.venv/Scripts/python.exe`。

macOS/Linux：

```bash
python3 -m venv backend/.venv
./backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

## 4. 启动后端

打开第一个终端，进入项目根目录：

```powershell
npm run dev:backend
```

看到 Uvicorn 启动信息后，打开下面地址检查后端：

<http://localhost:8000/api/v1/health>

页面应返回 `"status": "healthy"`。

## 5. 启动前端

打开第二个终端，同样进入项目根目录：

```powershell
npm run dev:frontend
```

然后打开：

<http://localhost:3334/login>

也可以使用一条命令同时启动前后端：

```powershell
npm run dev
```

前提是已经完成第 3 步的 Python 虚拟环境创建。

## 6. 登录测试

在登录窗口输入邮箱和密码。首次使用某个邮箱登录时，后端会自动创建测试用户（连接 MongoDB 时会保存到数据库）。

| 测试用户 | 邮箱 | 密码 |
| --- | --- | --- |
| 测试用户 1 | `test01@henu.edu.cn` | `Test1234!` |
| 测试用户 2 | `test02@henu.edu.cn` | `Test1234!` |
| 测试用户 3 | `test03@henu.edu.cn` | `Test1234!` |
| 测试用户 4 | `test04@henu.edu.cn` | `Test1234!` |
| 测试用户 5 | `test05@henu.edu.cn` | `Test1234!` |

登录成功后会跳转到 `/home`，顶部出现 `Sign Out`。登录后可以测试商品、购物车、订单、专业书单和站内沟通。

## 7. 常见问题

### `npm` 找不到 `package.json`

当前终端不在项目根目录。先执行：

```powershell
cd path\to\henu-campus-marketplace-clean
```

再运行 npm 命令。

### 找不到 `backend/.venv/Scripts/python.exe`

说明虚拟环境还没有创建成功。重新执行：

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 页面能打开，但登录失败

确认后端终端仍在运行，并访问：

<http://localhost:8000/api/v1/health>

如果无法访问，先启动 `npm run dev:backend`。前端默认请求地址是 `http://localhost:8000`。

### `py -3.12` 提示找不到运行时

这通常是 Python Launcher 没有登记该版本。可以改用：

```powershell
python -m venv backend\.venv
```

只要 `python --version` 显示 Python 3.12 或更高版本即可。

### 端口被占用

关闭占用 3334 或 8000 端口的旧进程，再重新启动前后端。不要在项目目录外执行启动命令。
