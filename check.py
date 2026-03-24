import socket
import subprocess
import platform
import urllib.request
import urllib.error

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, timeout=3)
        return result.stdout.decode('cp866', errors='ignore')
    except:
        return ""

def test_icmp(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    cmd = ["ping", param, "1", host]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def test_dns_txt(domain):
    out = run_cmd(f"nslookup -type=TXT {domain}")
    return "text =" in out or "v=spf1" in out

def test_web(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            return response.status == 200
    except:
        return False

def test_port(host, port, proto="tcp"):
    sock_type = socket.SOCK_STREAM if proto == "tcp" else socket.SOCK_DGRAM
    with socket.socket(socket.AF_INET, sock_type) as s:
        s.settimeout(2)
        try:
            if proto == "tcp":
                return s.connect_ex((host, port)) == 0
            else:
                s.sendto(b"\x1b" + 47 * b"\0", (host, port))
                return bool(s.recvfrom(1024))
        except:
            return False

def test_ipv6():
    if not socket.has_ipv6:
        return False
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        try:
            s.connect(('2001:4860:4860::8888', 53))
            return True
        except:
            return False

def main():
    results = {}

    print("--- СКАНЕР ДОСТУПНОСТИ СЕТИ ---")
    
    results["ICMP (Ping 8.8.8.8)"] = "ДОСТУПЕН" if test_icmp("8.8.8.8") else "НЕТ"
    
    try:
        ip = socket.gethostbyname("google.com")
        results["DNS Резолв (google.com)"] = f"РАБОТАЕТ ({ip})"
    except:
        results["DNS Резолв (google.com)"] = "НЕТ"

    results["DNS TXT записи (google.com)"] = "ПРОХОДЯТ" if test_dns_txt("google.com") else "НЕТ"
    
    results["HTTP (vk.com)"] = "ДОСТУПЕН" if test_web("https://vk.com") else "НЕТ"
    results["HTTP (google.com)"] = "ДОСТУПЕН" if test_web("https://google.com") else "НЕТ"
    
    results["UDP 443 (QUIC/H3)"] = "ОТКРЫТ" if test_port("8.8.8.8", 443, "udp") else "НЕТ"
    results["UDP 123 (NTP)"] = "ОТКРЫТ" if test_port("pool.ntp.org", 123, "udp") else "НЕТ"
    results["TCP 53 (DNS-over-TCP)"] = "ОТКРЫТ" if test_port("8.8.8.8", 53, "tcp") else "НЕТ"
    
    results["IPv6 Связность"] = "ЕСТЬ" if test_ipv6() else "НЕТ"

    print(f"{'ПАРАМЕТР':<30} | {'СТАТУС':<20}")
    print("-" * 55)
    for param, status in results.items():
        print(f"{param:<30} | {status:<20}")

if __name__ == "__main__":
    main()
    input("\nНажмите Enter для выхода...")