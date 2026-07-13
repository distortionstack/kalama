# core/oracle.py
import socket

def listen_for_callback(port, timeout=30):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(1)
    s.settimeout(timeout)
    try:
        conn, addr = s.accept()      # ถ้ามีใครต่อเข้ามา = ยิงสำเร็จ!
        return {"success": True, "from": addr[0]}
    except socket.timeout:
        return {"success": False}    # 30 วิไม่มีใครมา = ยิงไม่เข้า
    finally:
        s.close()
