import os
import json
import asyncio
import webbrowser
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.errors import FloodWaitError, PhoneNumberBannedError
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

# ========== UI ==========
def clear():
    os.system("clear" if os.name == "posix" else "cls")

def show_logo():
    clear()
    print("""
███╗   ██╗███████╗ ██████╗ ███╗   ██╗
████╗  ██║██╔════╝██╔═══██╗████╗  ██║
██╔██╗ ██║█████╗  ██║   ██║██╔██╗ ██║
██║╚██╗██║██╔══╝  ██║   ██║██║╚██╗██║
██║ ╚████║███████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
        ⚡ Method • Termux Tool by Ashif Rahman
""")
    print("━" * 35)
    print("1️⃣ Check Number")
    print("2️⃣ Join Channel")
    print("3️⃣ Exit")
    print("━" * 35)

# ========== Cooldown ==========
def is_in_cooldown():
    path = "cooldown/last_run.txt"
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        last_time_str = f.read().strip()
    try:
        last_time = datetime.fromisoformat(last_time_str)
        if datetime.now() - last_time < timedelta(minutes=5):
            return True
    except:
        pass
    return False

def set_cooldown():
    os.makedirs("cooldown", exist_ok=True)
    with open("cooldown/last_run.txt", "w") as f:
        f.write(datetime.now().isoformat())

# ========== Number Loader ==========
def load_numbers_from_file(limit=100):
    input_path = "input/numbers.txt"
    if not os.path.exists(input_path):
        print("❌ File not found: input/numbers.txt")
        return None, None
    with open(input_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
    numbers = ["+" + line for line in lines[:limit]]
    if not numbers:
        print("⚠️ No valid numbers found in input/numbers.txt")
        return None, None
    filename = os.path.splitext(os.path.basename(input_path))[0]
    return filename, numbers

# ========== API Config Loader ==========
def load_api_config(session_name):
    config_path = os.path.join("configs", f"{session_name}.json")
    if not os.path.exists(config_path):
        return None, None
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            return int(data.get("api_id")), data.get("api_hash")
    except:
        return None, None

# ========== Save Banned Sessions ==========
def save_banned_session(session_name, api_id, api_hash):
    with open("banned_sessions/banned_sessions.txt", "a") as f:
        f.write(session_name + "\n")
    with open("banned_sessions/api_details.txt", "a") as f:
        f.write(f"{session_name}: {api_id} | {api_hash}\n")

# ========== Process Single Session ==========
async def process_session(session_file, numbers, filename, results):
    session_name = session_file.replace(".session", "")
    api_id, api_hash = load_api_config(session_name)
    if not api_id:
        print(f"⚠️ Skipping session {session_name} (missing config)")
        return

    try:
        client = TelegramClient(f"sessions/{session_name}", api_id, api_hash)
        await client.start()

        for number in numbers:
            try:
                contact = InputPhoneContact(client_id=0, phone=number, first_name="Test", last_name="")
                result = await client(ImportContactsRequest([contact]))
                if result.users:
                    user = result.users[0]
                    if getattr(user, "deleted", False):
                        print(f"[🚫] {number} - Deleted (Banned)")
                        results.append(f"{number} - banned")
                    else:
                        print(f"[✅] {number}")
                        results.append(f"{number} - registered")
                else:
                    print(f"[❌] {number}")
                    results.append(f"{number} - not registered")
                await asyncio.sleep(1.5)
            except FloodWaitError as e:
                print(f"⏳ Flood wait: sleeping {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except PhoneNumberBannedError:
                print(f"🚫 Banned: {number}")
                results.append(f"{number} - banned")

        await client.disconnect()
    except Exception as e:
        print(f"❌ Error in session {session_name}: {e}")

# ========== Check Numbers ==========
async def check_numbers():
    if is_in_cooldown():
        print("⚠️ Please wait before next run. 5-minute cooldown in effect.")
        return

    filename, numbers = load_numbers_from_file()
    if not numbers:
        return

    session_files = [f for f in os.listdir("sessions") if f.endswith(".session")]
    if not session_files:
        print("⚠️ No session files found in sessions/ folder.")
        return

    chunks = [numbers[i::len(session_files)] for i in range(len(session_files))]
    results = []
    tasks = []
    for i, session in enumerate(session_files):
        tasks.append(process_session(session, chunks[i], filename, results))

    await asyncio.gather(*tasks)

    registered = [r for r in results if "- registered" in r]
    not_registered = [r for r in results if "- not registered" in r]
    banned = [r for r in results if "- banned" in r]

    footer = [
        "\n-------------------------------",
        f"Total Registered: {len(registered)}",
        f"Total Not Registered: {len(not_registered)}",
        f"Total Banned: {len(banned)}",
        "Powered by Neon Method Checker",
        "{",
        "  Need help? DM: https://t.me/NM_TG_CHECK | https://t.me/NeonMethod",
        "  Channel: https://t.me/NeonMethod",
        "}"
    ]

    os.makedirs("result", exist_ok=True)
    with open(f"result/registered.txt", "w") as f:
        f.write("\n".join(registered + footer))
    with open(f"result/not_registered.txt", "w") as f:
        f.write("\n".join(not_registered + footer))
    with open(f"result/banned.txt", "w") as f:
        f.write("\n".join(banned + footer))

    set_cooldown()

# ========== Channel Opener ==========
def join_channel(link):
    print("🔗 Opening Telegram Channel...")
    try:
        os.system(f'termux-open-url "{link}"')
    except:
        webbrowser.open(link)

# ========== Main Menu ==========
def main_menu():
    join_channel("https://t.me/NeonMethod")
    while True:
        show_logo()
        choice = input("🔰 Enter your choice (1/2/3): ").strip()
        if choice == "1":
            asyncio.run(check_numbers())
        elif choice == "2":
            join_channel("https://t.me/NeonMethod")
        elif choice == "3":
            print("👋 Exiting... Bye!")
            break
        else:
            print("❌ Invalid input.")
        input("\n🔁 Press Enter to return to menu...")

# ========== Start ==========
if __name__ == "__main__":
    os.makedirs("sessions", exist_ok=True)
    os.makedirs("configs", exist_ok=True)
    os.makedirs("input", exist_ok=True)
    os.makedirs("result", exist_ok=True)
    os.makedirs("banned_sessions", exist_ok=True)
    os.makedirs("cooldown", exist_ok=True)
    main_menu()