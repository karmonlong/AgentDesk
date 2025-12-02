import os
import subprocess
import time
import signal
import sys

def get_pids_on_port(port):
    """获取占用指定端口的进程ID列表"""
    try:
        # 使用 lsof -t -i :port 获取 PID
        result = subprocess.check_output(f"lsof -t -i :{port}", shell=True)
        pids = [int(pid) for pid in result.decode().split()]
        return pids
    except subprocess.CalledProcessError:
        return []

def kill_processes(pids):
    """强制结束进程"""
    for pid in pids:
        try:
            print(f"🛑 正在结束进程 {pid}...")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"❌ 结束进程 {pid} 失败: {e}")

def start_service():
    """启动服务"""
    print("🚀 正在启动服务 (make dev)...")
    print("="*50)
    try:
        # 使用 subprocess.run 执行命令，这样可以直接在终端看到输出
        subprocess.run("make dev", shell=True)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")

def main():
    port = 8000
    print(f"🔍 检查端口 {port}...")
    
    pids = get_pids_on_port(port)
    
    if pids:
        print(f"⚠️  发现占用端口的进程: {pids}")
        kill_processes(pids)
        # 等待端口释放
        time.sleep(1)
        print("✅ 端口已释放")
    else:
        print(f"✅ 端口 {port} 空闲")
    
    start_service()

if __name__ == "__main__":
    main()
