# WebSSH - 在线SSH终端

该项目为Python_WebSSH半成品，核心功能已实现，但未对明显或潜在的问题进行精修

## 简介

一个基于Python Flask和WebSocket的Web SSH应用，支持多SSH连接管理和专业的虚拟终端仿真。

## 功能特点

- ✅ **WebSocket通信** - 实时双向通信，低延迟
- ✅ **多SSH连接管理** - 支持同时管理多个SSH连接
- ✅ **专业虚拟终端** - 使用xterm.js实现专业级终端仿真
- ✅ **ANSI支持** - 自动处理ANSI转义序列
- ✅ **随机SSH ID** - 每个SSH连接分配唯一随机ID
- ✅ **连接切换** - 可在多个SSH连接间自由切换
- ✅ **统一端口** - WebSocket和Flask使用同一端口
- ✅ **实时输出** - 命令执行结果实时显示
- ✅ **终端自适应** - 支持终端大小调整
- ✅ **连接状态监控** - 实时监控连接状态

## 安装要求
## 开发环境：Python3.8
```bash
pip install -r requirements.txt
```

## 快速开始

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **启动服务**
```bash
python app.py
```

3. **访问应用**
打开浏览器访问: `http://localhost:5000`

## 使用方法

### 创建SSH连接

1. 在左侧面板填写SSH连接信息：
   - 主机地址 (如: localhost, 192.168.1.100)
   - 端口 (默认: 22)
   - 用户名
   - 密码或私钥

2. 点击"连接"按钮建立SSH连接

### 管理多个连接

- 支持同时创建多个SSH连接
- 点击左侧连接列表可切换当前活动连接
- 每个连接都有唯一的随机ID

### 终端操作

- 在终端中直接输入命令
- 支持所有标准终端操作（Ctrl+C, Ctrl+D等）
- 支持ANSI颜色代码和特殊字符
- 可调整终端大小

### 断开连接

- 点击"断开"按钮断开当前连接
- 支持单独断开某个连接
- 页面关闭时自动清理所有连接

## 技术架构

### 后端
- **Flask** - Web框架
- **Flask-SocketIO** - WebSocket支持
- **Paramiko** - SSH客户端库
- **Eventlet** - 异步服务器

### 前端
- **xterm.js** - 专业虚拟终端
- **Socket.IO** - WebSocket客户端
- **Bootstrap 5** - UI框架

### 核心组件

1. **SSH管理器 (ssh_manager.py)**
   - 管理多个SSH连接
   - 处理连接生命周期
   - 线程安全的连接池

2. **Flask应用 (app.py)**
   - WebSocket事件处理
   - SSH连接路由
   - 前后端通信协调

3. **前端界面 (templates/index.html)**
   - xterm.js终端集成
   - 连接管理界面
   - 实时通信处理

## 配置选项

### 应用配置
```python
# 在app.py中修改
app.config['SECRET_KEY'] = 'your-secret-key'
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### SSH配置
```python
# 连接超时设置
self.client.connect(timeout=10)

# 终端类型和大小
self.shell = self.client.invoke_shell(term='xterm', width=80, height=24)
```

## 安全建议

1. **使用HTTPS** - 生产环境建议使用HTTPS
2. **认证机制** - 添加用户认证系统
3. **访问控制** - 限制SSH连接范围
4. **日志监控** - 启用详细日志记录
5. **连接加密** - 确保SSH连接使用强加密

## 故障排除

### 连接失败
- 检查SSH服务是否运行
- 验证用户名和密码
- 确认防火墙设置
- 查看控制台日志

### WebSocket连接问题
- 检查浏览器控制台
- 确认端口未被占用
- 验证网络连接

### 终端显示异常
- 刷新页面重试
- 检查xterm.js版本兼容性
- 验证ANSI代码处理

## 扩展功能

- [ ] 文件传输支持 (SFTP)
- [ ] 会话录制和回放
- [ ] 多用户支持
- [ ] 命令历史记录
- [ ] 终端主题自定义
- [ ] 快捷键支持
- [ ] 连接书签
- [ ] 批量命令执行

## 许可证

MIT License

## 作者

G_G_B0ND/Mosi(2098175794@qq.com)
