import os
import json
import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect
from ssh_manager import ssh_manager
import threading
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'webssh-secret-key-2024'
# 创建SocketIO实例，使用与Flask相同的端口
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
# 存储WebSocket连接与SSH连接的映射
websocket_connections = {}
connection_lock = threading.Lock()

@app.route('/')
def index():
    """主页路由"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """处理WebSocket连接"""
    session_id = request.sid
    logger.info(f"WebSocket连接建立: {session_id}")
    with connection_lock:
        websocket_connections[session_id] = {
            'ssh_connection': None,
            'current_ssh_id': None
        }
    emit('connected', {'message': 'WebSocket连接成功', 'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    session_id = request.sid
    logger.info(f"WebSocket连接断开: {session_id}")
    with connection_lock:
        if session_id in websocket_connections:
            conn_info = websocket_connections[session_id]
            if conn_info['ssh_connection']:
                ssh_manager.remove_connection(conn_info['ssh_connection'].id)
            del websocket_connections[session_id]

@socketio.on('create_ssh_connection')
def handle_create_ssh_connection(data):
    """创建SSH连接"""
    session_id = request.sid
    
    try:
        host = data.get('host', 'localhost')
        port = int(data.get('port', 22))
        username = data.get('username', 'root')
        password = data.get('password', '')
        private_key = data.get('private_key')
        logger.info(f"创建SSH连接: {host}:{port} for session {session_id}")
        # 创建SSH连接
        connection = ssh_manager.create_connection(
            host=host,
            port=port,
            username=username,
            password=password if password else None,
            private_key=private_key if private_key else None
        )
        # 设置输出回调
        def output_callback(data):
            socketio.emit('terminal_output', {
                'ssh_id': connection.id,
                'data': data
            }, room=session_id)
        connection.output_callback = output_callback
        # 连接到SSH服务器
        if connection.connect():
            with connection_lock:
                if session_id in websocket_connections:
                    websocket_connections[session_id]['ssh_connection'] = connection
                    websocket_connections[session_id]['current_ssh_id'] = connection.id
            emit('ssh_connected', {
                'success': True,
                'ssh_id': connection.id,
                'message': f'SSH连接成功: {username}@{host}:{port}'
            })
        else:
            ssh_manager.remove_connection(connection.id)
            emit('ssh_connected', {
                'success': False,
                'error': 'SSH连接失败，请检查连接信息'
            })
    except Exception as e:
        logger.error(f"创建SSH连接错误: {str(e)}")
        emit('ssh_connected', {
            'success': False,
            'error': f'SSH连接错误: {str(e)}'
        })

@socketio.on('switch_ssh_connection')
def handle_switch_ssh_connection(data):
    """切换SSH连接"""
    session_id = request.sid
    ssh_id = data.get('ssh_id')
    if not ssh_id:
        emit('error', {'message': '未提供SSH连接ID'})
        return
    connection = ssh_manager.get_connection(ssh_id)
    if not connection:
        emit('error', {'message': 'SSH连接不存在'})
        return
    with connection_lock:
        if session_id in websocket_connections:
            websocket_connections[session_id]['current_ssh_id'] = ssh_id
            websocket_connections[session_id]['ssh_connection'] = connection
    emit('ssh_switched', {
        'success': True,
        'ssh_id': ssh_id,
        'message': f'已切换到SSH连接: {ssh_id}'
    })

@socketio.on('terminal_input')
def handle_terminal_input(data):
    """处理终端输入"""
    session_id = request.sid
    with connection_lock:
        if session_id not in websocket_connections:
            emit('error', {'message': '会话不存在'})
            return
        conn_info = websocket_connections[session_id]
        connection = conn_info.get('ssh_connection')
        if not connection or not connection.connected:
            emit('error', {'message': 'SSH连接不存在或未连接'})
            return
    try:
        command = data.get('data', '')
        if command:
            success = connection.send_command(command)
            if not success:
                emit('error', {'message': '发送命令失败'})
    except Exception as e:
        logger.error(f"处理终端输入错误: {str(e)}")
        emit('error', {'message': f'处理输入错误: {str(e)}'})

@socketio.on('resize_terminal')
def handle_resize_terminal(data):
    """调整终端大小"""
    session_id = request.sid
    with connection_lock:
        if session_id not in websocket_connections:
            return
        conn_info = websocket_connections[session_id]
        connection = conn_info.get('ssh_connection')
        if not connection or not connection.connected:
            return
    try:
        width = int(data.get('cols', 80))
        height = int(data.get('rows', 24))
        connection.resize_terminal(width, height)
    except Exception as e:
        logger.error(f"调整终端大小错误: {str(e)}")

@socketio.on('list_connections')
def handle_list_connections():
    """列出所有SSH连接"""
    connections = ssh_manager.list_connections()
    connection_info = []
    for conn_id in connections:
        conn = ssh_manager.get_connection(conn_id)
        if conn:
            connection_info.append({
                'id': conn_id,
                'host': conn.host,
                'port': conn.port,
                'username': conn.username,
                'connected': conn.connected
            })
    emit('connections_list', {
        'connections': connection_info
    })


@socketio.on('disconnect_ssh')
def handle_disconnect_ssh(data):
    """断开SSH连接"""
    session_id = request.sid
    ssh_id = data.get('ssh_id')
    if ssh_id:
        success = ssh_manager.remove_connection(ssh_id)
        with connection_lock:
            if session_id in websocket_connections:
                conn_info = websocket_connections[session_id]
                if conn_info.get('current_ssh_id') == ssh_id:
                    websocket_connections[session_id]['ssh_connection'] = None
                    websocket_connections[session_id]['current_ssh_id'] = None
        emit('ssh_disconnected', {
            'success': success,
            'ssh_id': ssh_id,
            'message': 'SSH连接已断开' if success else '断开连接失败'
        })

def cleanup_connections():
    """定期清理不活跃的连接"""
    while True:
        try:
            inactive_connections = ssh_manager.cleanup_inactive_connections()
            if inactive_connections:
                logger.info(f"清理了 {len(inactive_connections)} 个不活跃连接")
            time.sleep(60)  # 每分钟检查一次
        except Exception as e:
            logger.error(f"清理连接错误: {str(e)}")

# 启动清理线程
cleanup_thread = threading.Thread(target=cleanup_connections)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    # 启动Flask-SocketIO服务器
    logger.info("启动WebSSH服务器...")
    socketio.run(app, 
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )
