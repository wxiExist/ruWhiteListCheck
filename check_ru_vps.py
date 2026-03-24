import socket
import subprocess
import os
import urllib.request

def run_sysctl(param):
    try:
        result = subprocess.run(['sysctl', param], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "N/A"

def check_outbound(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3)
        try:
            s.connect((host, port))
            return True
        except:
            return False

def check_dns_recursion():
    try:
        socket.gethostbyname('google.com')
        return True
    except:
        return False

def test_web(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except:
        return False

def main():
    res = {}
    print("--- АНАЛИЗ RU-VPS КАК МОСТА (BRIDGE) ---")

    # 1. Проверка системных настроек для туннелирования
    # Для моста обязательно должен быть включен IP Forwarding
    res["IP Forwarding (IPv4)"] = "ВКЛЮЧЕН" if "1" in run_sysctl("net.ipv4.ip_forward") else "ВЫКЛЮЧЕН (нужно включить)"
    
    # 2. Проверка выхода "наружу" (Egress)
    # Если сервер в РФ, но сам ограничен белым списком, он бесполезен как мост
    res["Доступ к Google (HTTPS)"] = "ЕСТЬ" if test_web("https://google.com") else "НЕТ"
    res["Доступ к Cloudflare (1.1.1.1)"] = "ЕСТЬ" if check_outbound("1.1.1.1", 53) else "НЕТ"
    
    # 3. Проверка возможности занять "магические" порты
    # Сможет ли сервер слушать на порту 53 или 123 (нужны права root)
    def check_listen(port, proto):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM if proto == "tcp" else socket.SOCK_DGRAM)
            s.bind(('0.0.0.0', port))
            s.close()
            return "СВОБОДЕН"
        except PermissionError:
            return "ЗАНЯТ/ЗАПРЕЩЕН (нужен root)"
        except:
            return "ОШИБКА"

    res["Порт TCP 53 (для входящих)"] = check_listen(53, "tcp")
    res["Порт UDP 123 (для входящих)"] = check_listen(123, "udp")

    # 4. Определение внешнего IP и его типа
    try:
        ext_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
        res["Внешний IP сервера"] = ext_ip
    except:
        res["Внешний IP сервера"] = "Не удалось определить"

    # Печать отчета
    print(f"{'ПАРАМЕТР':<35} | {'СТАТУС':<25}")
    print("-" * 65)
    for k, v in res.items():
        print(f"{k:<35} | {v:<25}")

    # Анализ пригодности
    print("\n--- ЗАКЛЮЧЕНИЕ ---")
    if res["Доступ к Google (HTTPS)"] == "ЕСТЬ":
        print("[+] Сервер имеет выход в мир. Он может быть мостом.")
    else:
        print("[!] Сервер сам находится за белым списком. Как мост бесполезен.")

if __name__ == "__main__":
    main()