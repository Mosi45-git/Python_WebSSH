import paramiko
import threading
import uuid
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSHConnection:
    def __init__(self, host, port, username, password=None, private_key=None):
        self.id = str(uuid.uuid4())
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.client = None
        self.shell = None
        self.connected = False
        self.lock = threading.Lock()
        self.output_thread = None
        self.running = False
        self.output_callback = None
        
    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.private_key:
                key = paramiko.RSAKey.from_private_key_file(self.private_key)
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=key,
                    timeout=10
                )
            else:
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            
            self.shell = self.client.invoke_shell(term='xterm', width=80, height=24)
            self.shell.settimeout(0.1)
            self.connected = True
            self.running = True
            
            # 启动输出线程
            self.output_thread = threading.Thread(target=self._read_output)
            self.output_thread.daemon = True
            self.output_thread.start()
            
            logger.info(f"SSH连接成功: {self.id}")
            return True
            
        except Exception as e:
            logger.error(f"SSH连接失败: {str(e)}")
            self.disconnect()
            return False
    
    def _read_output(self):
        """读取SSH输出并发送到WebSocket回调"""
        while self.running and self.connected:
            try:
                if self.shell and self.shell.recv_ready():
                    data = self.shell.recv(4096)
                    if data and self.output_callback:
                        self.output_callback(data.decode('utf-8', errors='replace'))
                else:
                    time.sleep(0.01)
            except Exception as e:
                if self.running:
                    logger.error(f"读取SSH输出错误: {str(e)}")
                break
    
    def send_command(self, command):
        """发送命令到SSH会话"""
        if self.connected and self.shell:
            try:
                self.shell.send(command.encode('utf-8'))
                return True
            except Exception as e:
                logger.error(f"发送命令失败: {str(e)}")
                return False
        return False
    
    def resize_terminal(self, width, height):
        """调整终端大小"""
        if self.connected and self.shell:
            try:
                self.shell.resize_pty(width, height)
                return True
            except Exception as e:
                logger.error(f"调整终端大小失败: {str(e)}")
                return False
        return False
    
    def disconnect(self):
        """断开SSH连接"""
        self.running = False
        self.connected = False
        
        if self.output_thread and self.output_thread.is_alive():
            self.output_thread.join(timeout=1)
        
        if self.shell:
            try:
                self.shell.close()
            except:
                pass
        
        if self.client:
            try:
                self.client.close()
            except:
                pass
        
        logger.info(f"SSH连接断开: {self.id}")
    
    def is_active(self):
        """检查连接是否活跃"""
        return self.connected and self.client and self.client.get_transport() and self.client.get_transport().is_active()


class SSHManager:
    def __init__(self):
        self.connections = {}
        self.lock = threading.Lock()
    
    def create_connection(self, host, port, username, password=None, private_key=None):
        """创建新的SSH连接"""
        connection = SSHConnection(host, port, username, password, private_key)
        
        with self.lock:
            self.connections[connection.id] = connection
        
        return connection
    
    def get_connection(self, connection_id):
        """获取SSH连接"""
        with self.lock:
            return self.connections.get(connection_id)
    
    def remove_connection(self, connection_id):
        """移除SSH连接"""
        with self.lock:
            connection = self.connections.get(connection_id)
            if connection:
                connection.disconnect()
                del self.connections[connection_id]
                return True
        return False
    
    def list_connections(self):
        """列出所有连接"""
        with self.lock:
            return list(self.connections.keys())
    
    def cleanup_inactive_connections(self):
        """清理不活跃的连接"""
        with self.lock:
            inactive_ids = []
            for conn_id, connection in self.connections.items():
                if not connection.is_active():
                    inactive_ids.append(conn_id)
            
            for conn_id in inactive_ids:
                connection = self.connections[conn_id]
                connection.disconnect()
                del self.connections[conn_id]
            
            return inactive_ids


# 全局SSH管理器实例
ssh_manager = SSHManager()