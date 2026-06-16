import winreg
import subprocess
import sys
import os
import ctypes

CYAN   = "\033[96m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
WHITE  = "\033[97m"
RESET  = "\033[0m"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def ok(msg):
    print(f"  {GREEN}[BERHASIL]{RESET} {msg}")

def fail(msg):
    print(f"  {RED}[GAGAL]{RESET}   {msg}")

def skip(msg):
    print(f"  {YELLOW}[SKIP]{RESET}    {msg}")

def delete_value(hive, path, name):
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        ok(f"{name}")
    except FileNotFoundError:
        skip(f"{name} (tidak ada)")
    except Exception as e:
        fail(f"{name}: {e}")

def delete_key_recursive(hive, path):
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_ALL_ACCESS)
        while True:
            try:
                subkey = winreg.EnumKey(key, 0)
                delete_key_recursive(hive, path + "\\" + subkey)
            except OSError:
                break
        winreg.CloseKey(key)
        winreg.DeleteKey(hive, path)
        ok(f"{path.split(chr(92))[-1]}")
    except FileNotFoundError:
        skip(f"{path.split(chr(92))[-1]} (tidak ada)")
    except Exception as e:
        fail(f"{path}: {e}")

def run():
    os.system("cls")
    os.system("color")
    print(f"{CYAN}{'='*55}")
    print(f"   FIX WINDOWS POLICY")
    print(f"{'='*55}{RESET}\n")

    print(f"{WHITE}[1/9] HKCU Explorer Policies...{RESET}")
    for v in ["NoDesktop","NoTrayItemsDisplay","NoTaskbar","NoRun",
              "RestrictRun","NoControlPanel","NoFileMenu","NoFind",
              "NoSetFolders","NoSetTaskbar","NoClose","NoLogoff",
              "NoViewContextMenu","NoThumbnailCache","NoDrives",
              "NoNetworkConnections","NoStartMenuMorePrograms",
              "NoStartMenuSubFolders","NoRecentDocsMenu","NoSMHelp",
              "NoWindowsUpdate","DisallowRun"]:
        delete_value(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", v)

    print(f"\n{WHITE}[2/9] HKCU System Policies...{RESET}")
    for v in ["DisableTaskMgr","DisableCMD","DisableRegistryTools",
              "NoDispCPL","NoDispBackgroundPage","NoDispScrSavPage","NoSecCPL"]:
        delete_value(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Policies\System", v)

    print(f"\n{WHITE}[3/9] HKLM Explorer Policies...{RESET}")
    for v in ["NoDesktop","NoTrayItemsDisplay","NoTaskbar","NoRun",
              "RestrictRun","NoControlPanel","NoClose","NoLogoff",
              "NoDrives","HidePowerOptions","DisallowRun"]:
        delete_value(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", v)

    print(f"\n{WHITE}[4/9] HKLM System Policies...{RESET}")
    for v in ["DisableTaskMgr","DisableCMD","DisableRegistryTools","DisableShutdownButton"]:
        delete_value(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", v)

    print(f"\n{WHITE}[5/9] DisallowRun & RestrictRun lists...{RESET}")
    for hive, path in [
        (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun"),
        (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\RestrictRun"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\RestrictRun"),
    ]:
        delete_key_recursive(hive, path)

    print(f"\n{WHITE}[6/9] AppLocker & SRP...{RESET}")
    delete_key_recursive(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\SrpV2")
    delete_key_recursive(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Safer")

    print(f"\n{WHITE}[7/9] Personalization & Explorer GPO...{RESET}")
    for hive, path in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Personalization"),
        (winreg.HKEY_CURRENT_USER,  r"Software\Policies\Microsoft\Windows\Personalization"),
        (winreg.HKEY_CURRENT_USER,  r"Software\Policies\Microsoft\Windows\Explorer"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Explorer"),
        (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Policies\System"),
        (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Group Policy Objects"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Group Policy Objects"),
    ]:
        delete_key_recursive(hive, path)

    print(f"\n{WHITE}[8/9] File GroupPolicy .pol...{RESET}")
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    for pol in [
        os.path.join(sysroot, r"System32\GroupPolicy\Machine\Registry.pol"),
        os.path.join(sysroot, r"System32\GroupPolicy\User\Registry.pol"),
    ]:
        if os.path.exists(pol):
            try:
                os.remove(pol)
                ok(os.path.basename(pol))
            except Exception as e:
                fail(f"{os.path.basename(pol)}: {e}")
        else:
            skip(f"{os.path.basename(pol)} (tidak ada)")

    print(f"\n{WHITE}[9/9] Tambah user gamer ke Administrators...{RESET}")
    result = subprocess.run(["net","localgroup","Administrators","gamer","/add"],
                            capture_output=True, text=True)
    if result.returncode == 0:
        ok("gamer ditambahkan ke Administrators")
    else:
        skip(f"gamer: {result.stdout.strip() or result.stderr.strip()}")

    print(f"\n{WHITE}Menjalankan gpupdate...{RESET}")
    r = subprocess.run(["gpupdate","/force"], capture_output=True, text=True)
    ok("gpupdate") if r.returncode == 0 else fail("gpupdate")

    print(f"\n{WHITE}Restart Explorer...{RESET}")
    subprocess.run(["taskkill","/f","/im","explorer.exe"], capture_output=True)
    subprocess.Popen(["explorer.exe"])
    ok("Explorer di-restart")

    print(f"\n{CYAN}{'='*55}")
    print(f"   SELESAI! Restart PC untuk efek penuh.")
    print(f"{'='*55}{RESET}")
    input("\nTekan Enter untuk keluar...")

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()
    run()
              
