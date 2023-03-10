import subprocess
import time
import urllib.request
import urllib.parse
import urllib.error
import time

ip_file = "ip.txt"
cf_fast_ip_file = "result.csv"
test_ip_file = "test_ip.csv"
fast_ip = ''
fast_ip_list = []


def get_rules_number():
    output = subprocess.check_output(
        "iptables -t nat  -L --line-number | grep 'match-set cf_list dst'| awk '{print $1}'", shell=True)
    return output.decode("utf-8").strip()


# Telegram bot API endpoint
token = '6086007258:AAHemOeM9pzzwmw-c220Jm-oexNc5QZSzwE'
url = 'https://api.telegram.org/bot{}/sendMessage'.format(token)

# Target chat ID
chat_id = '801848149'


def send_message(text):
    date = bytes(urllib.parse.urlencode(
        {'chat_id': chat_id, 'text': text}), 'utf-8')
    # Send POST request to Telegram API endpoint
    try:
        urllib.request.urlopen(url, data=date
                               )
    except urllib.error.URLError as e:
        print(e.reason)


def modify_rules(cf_fast_ip: str) -> bool:
    number = get_rules_number()
    if number:
        return False
    subprocess.call(
        "iptables -t nat -R  OUTPUT {number} -p tcp -m set --match-set cf_list dst -j DNAT --to-destination {cf_fast_ip}".format(number=number, cf_fast_ip=cf_fast_ip), shell=True, stdin=None)
    return True


def delete_rules() -> bool:
    number = get_rules_number()
    if not number:
        return False
    subprocess.call(
        "iptables -t nat -D  OUTPUT {number}".format(number=number), shell=True, stdin=None)
    return True


def close_openclash():
    subprocess.call(
        "/etc/init.d/openclash stop", shell=True)
    time.sleep(1)


def open_openclash():
    subprocess.call(
        "/etc/init.d/openclash start", shell=True, stdin=None)
    time.sleep(2)


def add_rules(cf_fast_ip):
    number = get_rules_number()
    if number:
        return False
    subprocess.call(
        "iptables -t nat -A OUTPUT  -p tcp -m set --match-set cf_list dst -j DNAT --to-destination {cf_fast_ip}".format(cf_fast_ip=cf_fast_ip), shell=True, stdin=None)


def set_ip():
    subprocess.call(
        "ipset create cf_list hash:net hashsize 20000", shell=True, stdin=None)
    with open(ip_file, "r") as f:
        for ip in f.readlines():
            subprocess.call(
                "ipset -exist add cf_list {ip}".format(ip=ip), shell=True, stdin=None)


def get_fast_ip():
    global fast_ip_list
    delete_rules()
    print("关闭iptables规则")
    close_openclash()
    print("关闭openclash")
    subprocess.call(
        "./CloudflareST", shell=True)
    with open(cf_fast_ip_file, "r") as f:
        for res in f.readlines()[1:]:
            fast_ip_list.append(res.split(',')[0].strip())
    fast_ip = fast_ip_list[0]
    add_rules(fast_ip)
    open_openclash()

    return fast_ip

# 测试网速


def test_ip(fast_ip):
    subprocess.call(
        "./CloudflareST -ip {fast_ip} -o {test_ip_file}".format(fast_ip=fast_ip, test_ip_file=test_ip_file), shell=True)

# 定时对ip进行测试


def test_ip_timer():
    global fast_ip
    global fast_ip_list
    count = 0
    change_count = 0
    while True:
        time.sleep(60*5)
        status = 0
        for _ in range(4):
            proc = subprocess.Popen(
                ["ping", "-c", "1", "{fast_ip}".format(fast_ip=fast_ip)], stdin=None
            )
            # 获取状态码
            status = proc.wait()
            if status == 0:
                break
        if status == 0 and count < 250 and change_count < 6:
            count += 1
        elif change_count >= 6:
            fast_ip = get_fast_ip()
        else:
            fast_ip_list.remove(fast_ip)
            fast_ip = fast_ip_list[0]
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            send_message(now_time+' 更新cloudflare最快ip为：'+fast_ip)
            change_count += 1
            count = 0
        


def main():
    global fast_ip
    set_ip()
    fast_ip = get_fast_ip()
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    send_message(now_time+' 更新cloudflare最快ip为：'+fast_ip)
    test_ip_timer()


if __name__ == "__main__":
    main()
