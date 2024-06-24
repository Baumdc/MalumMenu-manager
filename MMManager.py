import os
import shutil
import requests
import zipfile
import subprocess
import tkinter as tk
from tkinter import messagebox
import winreg

# Function to find Among Us installation directory from the Windows registry
def find_among_us_installation():
    try:
        registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path)
        for i in range(winreg.QueryInfoKey(key)[0]):
            subkey_name = winreg.EnumKey(key, i)
            subkey = winreg.OpenKey(key, subkey_name)
            try:
                display_name = winreg.QueryValueEx(subkey, 'DisplayName')[0]
                if display_name == 'Among Us':
                    install_location = winreg.QueryValueEx(subkey, 'InstallLocation')[0]
                    among_us_exe = os.path.join(install_location, 'Among Us.exe')
                    if os.path.isfile(among_us_exe):
                        return install_location
            except FileNotFoundError:
                continue
    except Exception as e:
        print(f"An error occurred while searching the registry: {e}")
    return None

# Function to get the latest release version from GitHub
def get_latest_release_version():
    latest_release_url = 'https://github.com/scp222thj/MalumMenu/releases/latest'
    response = requests.get(latest_release_url, allow_redirects=False)
    
    # Extract the version from the redirect URL
    if 'Location' in response.headers:
        location = response.headers['Location']
        version = location.split('/')[-1]
        return version
    else:
        raise Exception("No release version found")

# Function to download the latest release
def download_release(version, output_path):
    download_url = f'https://github.com/scp222thj/MalumMenu/releases/download/{version}/MalumMenu-{version[1:]}.zip'
    response = requests.get(download_url, stream=True)
    with open(output_path, 'wb') as file:
        shutil.copyfileobj(response.raw, file)
    return output_path

# Function to unzip the downloaded release
def unzip_file(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def install_latest_release():
    try:
        version = get_latest_release_version()
        print(f"Latest release version: {version}")

        zip_path = download_release(version, 'latest_release.zip')
        print(f"Downloaded latest release to {zip_path}")

        extract_to = 'malum_menu'
        unzip_file(zip_path, extract_to)
        print(f"Extracted to {extract_to}")

        among_us_dir = find_among_us_installation()
        if among_us_dir:
            print(f"Found Among Us installation at: {among_us_dir}")
            copy_files_with_single_confirmation(extract_to, among_us_dir)
            print(f"Copied files to {among_us_dir}")
        else:
            print("Could not find Among Us installation directory automatically.")

        # Clean up
        os.remove(zip_path)
        shutil.rmtree(extract_to)
        print("Cleaned up temporary files.")

        messagebox.showinfo("Success", "Latest release installed successfully.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to copy files with a single overwrite confirmation
def copy_files_with_single_confirmation(src_dir, dst_dir):
    # Check if any files need to be overwritten
    files_to_overwrite = []
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dst_dir, item)
        if os.path.exists(d):
            files_to_overwrite.append(d)

    if files_to_overwrite:
        overwrite_all = messagebox.askyesno(
            "Fresh Install Confirmation",
            "You will have a fresh install of Malum Menu. Only your configuration will be kept. Are you sure you want to proceed?"
        )
        if overwrite_all:
            # Check for MalumMenu.cfg and move it to a safe location
            among_us_folder = find_among_us_installation()
            if among_us_folder:
                config_path = os.path.join(among_us_folder, "BepInEx", "config", "MalumMenu.cfg")
                if os.path.exists(config_path):
                    safe_location = os.path.join(among_us_folder, "MalumMenu.cfg.bak")
                    shutil.move(config_path, safe_location)
                    print(f"Moved MalumMenu.cfg to {safe_location}")

            # Delete existing mod and install fresh
            delete_mod(show_success_message=False)  # Skip success message
            install_latest_release()

            # Move MalumMenu.cfg back to its original location
            if os.path.exists(safe_location):
                config_folder = os.path.join(among_us_folder, "BepInEx", "config")
                if not os.path.exists(config_folder):
                    os.makedirs(config_folder)
                shutil.move(safe_location, os.path.join(config_folder, "MalumMenu.cfg"))
                print(f"Moved MalumMenu.cfg back to {config_folder}")
        else:
            return  # User chose not to overwrite any files

    # Proceed with copying files
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dst_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

# Function to check if Malum Menu is installed
def is_malum_menu_installed():
    among_us_folder = find_among_us_installation()
    if not among_us_folder:
        return False

    plugins_path = os.path.join(among_us_folder, "BepInEx", "plugins")
    dll_path = os.path.join(plugins_path, "MalumMenu.dll")
    return os.path.exists(dll_path)

# Function to update the DLL
def update_dll():
    if not is_malum_menu_installed():
        install_choice = messagebox.askyesno(
            "Malum Menu Not Installed",
            "Malum Menu is not installed. Do you want to install it now?"
        )
        if install_choice:
            install_latest_release()  # Install the latest release
            # After installation, update the DLL
            update_dll()
            return
        else:
            messagebox.showinfo("Cancelled", "Installation of Malum Menu has been cancelled.")
            return

    among_us_folder = find_among_us_installation()
    if not among_us_folder:
        messagebox.showerror("Error", "Among Us installation not found.")
        return

    plugins_path = os.path.join(among_us_folder, "BepInEx", "plugins")
    dll_destination_path = os.path.join(plugins_path, "MalumMenu.dll")
    
    url = "https://github.com/scp222thj/MalumMenu/archive/refs/heads/main.zip"    
    zip_path = "MalumMenu.zip"  # Define zip_path here

    with requests.get(url, stream=True) as r:
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("MalumMenu")

    among_us_folder = "MalumMenu/MalumMenu-main"
    subprocess.run(["dotnet", "build"], cwd=among_us_folder, check=True)

    dll_source_path = os.path.join(among_us_folder, "src", "bin", "Debug", "net6.0", "MalumMenu.dll")
    shutil.copy(dll_source_path, dll_destination_path)

    os.remove(zip_path)
    shutil.rmtree("MalumMenu")

    print("Operation completed successfully.")

    
# Function to toggle mod on/off
def toggle_mod():
    among_us_folder = find_among_us_installation()
    if not among_us_folder:
        messagebox.showerror("Error", "Among Us installation not found.")
        return

    backup_folder = os.path.join(among_us_folder, "mod_backup")
    mod_items = [
        "BepInEx",
        "dotnet",
        ".doorstop_version",
        "changelog.txt",
        "doorstop_config.ini",
        "steam_appid.txt",
        "winhttp.dll"
    ]

    # Ensure backup folder exists
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # Check if mod is currently on
    mod_on = all(os.path.exists(os.path.join(among_us_folder, item)) for item in mod_items)

    if mod_on:
        # Move mod items to backup folder
        for item in mod_items:
            source_item = os.path.join(among_us_folder, item)
            dest_item = os.path.join(backup_folder, item)
            if os.path.exists(source_item):
                shutil.move(source_item, dest_item)
        print("Mod turned off and files moved to backup folder.")
    else:
        # Move mod items back to Among Us folder
        for item in mod_items:
            source_item = os.path.join(backup_folder, item)
            dest_item = os.path.join(among_us_folder, item)
            if os.path.exists(source_item):
                shutil.move(source_item, dest_item)
        print("Mod turned on and files moved back to Among Us folder.")



# Function to delete mod and restore original Among Us installation
# Function to delete mod and restore original Among Us installation
def delete_mod(show_success_message=True):
    among_us_folder = find_among_us_installation()
    if not among_us_folder:
        messagebox.showerror("Error", "Among Us installation not found.")
        return

    mod_items = [
        "BepInEx",
        "dotnet",
        ".doorstop_version",
        "changelog.txt",
        "doorstop_config.ini",
        "steam_appid.txt",
        "winhttp.dll"
    ]

    confirm_delete = True  

    if confirm_delete:
        # Delete mod and restore original Among Us
        for item in mod_items:
            mod_path = os.path.join(among_us_folder, item)
            if os.path.isdir(mod_path):
                shutil.rmtree(mod_path)  # Remove mod directories
            elif os.path.isfile(mod_path):
                os.remove(mod_path)  # Remove mod files

        # Delete backup folder if it exists
        backup_folder = os.path.join(among_us_folder, "mod_backup")
        if os.path.exists(backup_folder):
            shutil.rmtree(backup_folder)

        if show_success_message:
            messagebox.showinfo("Success", "Malum Menu has been deleted and Among Us is now unmodded.")
        
        
# Tkinter interface
root = tk.Tk()
root.title("Malum Menu Manager")

frame = tk.Frame(root)
frame.pack(padx=20, pady=20)

install_release_button = tk.Button(frame, text="Install Latest Release", command=install_latest_release)
install_release_button.pack(pady=10)

update_dll_button = tk.Button(frame, text="Update DLL", command=update_dll)
update_dll_button.pack(pady=10)

toggle_mod_button = tk.Button(frame, text="Toggle Mod", command=toggle_mod)
toggle_mod_button.pack(pady=10)

delete_mod_button = tk.Button(frame, text="Delete Mod", command=delete_mod)
delete_mod_button.pack(pady=10)

root.mainloop()