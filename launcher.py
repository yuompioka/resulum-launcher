from kivy.uix.button import Button
from kivy.app import App
from kivy.uix.image import AsyncImage

from kivy.config import Config
Config.set('graphics', 'resizable', '0');
Config.set('graphics', 'width', '1280');
Config.set('graphics', 'height', '720');

from kivy.uix.floatlayout import FloatLayout
from kivy.core.text import LabelBase

from kivy.animation import Animation
from kivy.lang import Builder

import handler as Handler
import auth as Auth
import os, hashlib, functools, shutil, glob, json, time, zipfile
from urllib.request import urlopen as download
from threading import Thread
import minecraft_launcher_lib
import requests as req

def reset():
    import kivy.core.window as window
    from kivy.base import EventLoop
    if not EventLoop.event_listeners:
        from kivy.cache import Cache
        window.Window = window.core_select_lib('window', window.window_impl, True)
        Cache.print_usage()
        for cat in Cache._categories:
            Cache._objects[cat] = {}

def download_file(url, destination):
    page = download(url)
    with open(destination, 'wb') as fp:
        shutil.copyfileobj(page, fp, 512)

try:
    os.makedirs(os.path.expandvars("%APPDATA%\\.resulum-launcher-data"))
except:
    pass

download_file("http://yuoco.myogaya.jp:8123/root.kv", os.path.expandvars("%APPDATA%\\.resulum-launcher-data\\root.kv"))
download_file("http://yuoco.myogaya.jp:8123/icon.ico", os.path.expandvars("%APPDATA%\\.resulum-launcher-data\\icon.ico"))
Config.set('kivy','window_icon',os.path.expandvars("%APPDATA%\\.resulum-launcher-data\\icon.ico"));
#font_path = os.path.expandvars("%APPDATA%\\.resulum-launcher-data\\font.ttf")

from kivy.uix.textinput import TextInput

config = {"logged_in": False, "files_downloaded": 0, "game_launched": False, "settings_opened":False, "vmanager_opened":False, "directory": "{}".format(os.path.expandvars(r"%APPDATA%\.minecraft")), 
"play_btn_blocked": True, "ram": ['-Xmx4G', '-Xms4G'], "modpack_version": 1, "files_in_modpack": 6, "ram_hr":2}

updater_config = {"url":"http://yuoco.myogaya.jp:8123/", "file":"init.json"}

nickname = None
uuid = None
version = '1.16.5'

try:
    os.makedirs(config["directory"]+"\\mods")
except:
    pass

def md5sum(filename):
    with open(filename, 'rb') as f:
        hasher = hashlib.md5()
        for block in iter(functools.partial(f.read, 64 * (1 << 20)), b''):
            hasher.update(block)
    return hasher.hexdigest()

def editJSON(file, field, value):
    with open(file) as f:
        data = json.load(f)
        data[field] = value
        json.dump(data, open(file, "w"), indent = 4)

Builder.load_file(os.path.expandvars("%APPDATA%\\.resulum-launcher-data\\root.kv"))

class MaxLengthInput(TextInput):
    max_length = 16

    def insert_text(self, substring, from_undo=False):
        if len(self.text) > self.max_length:
            return False
        else:
            return super(MaxLengthInput, self).insert_text(substring, from_undo=from_undo)

class Root(FloatLayout):
    def client_launch(self, username, uuid, version, directory, ram):
        self.writeToConsole("Запускаю клиент...")
        try:
            Handler.runMinecraft(username, uuid, version, directory, ram)
        except:
            self.writeToConsole("При запуске что-то пошло не так.")

    def callback_download(self, url, destination):
        self.download_file_class(url, destination)
        config["files_downloaded"] += 1

    def download_file_class(self, url, destination):
        page = download(url)
        with open(destination, 'wb') as fp:
            shutil.copyfileobj(page, fp, 512)
        self.writeToConsole(f"Загружаю {destination}...")

    def open_versions_folder(self):
        os.startfile(config["directory"]+"\\versions")

    def clear_mods(self):
        file_list = glob.glob(config["directory"] + "\\mods" + r"\*.jar")
        for file in file_list:
            os.remove(file)
        self.writeToConsole("Папка с модами очищена.")
    def checkForConfig(self):
        global nickname, version, uuid
        try:
            os.makedirs(config["directory"] + "\\.resulum-launcher")
        except:
            self.writeToConsole("Папка с конфигом найдена. Загружаю данные...")
        else:
            self.writeToConsole("Папка для сохранения конфигурации создана.")
            data = {"directory":config["directory"],"nickname":"Nickname","uuid":hashlib.md5('ResulumPlayer:Nickname'.encode("utf-8")).hexdigest(),"version":"1.16.5",
            "modpack_version":config["modpack_version"],"ram_hr":4}

            with open(config["directory"] + "\\.resulum-launcher\\" + 'config.json', 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True

        with open(config["directory"] + "\\.resulum-launcher\\config.json") as f:
            data = json.load(f)

        config["directory"] = data["directory"]
        config["modpack_version"] = data["modpack_version"]
        nickname = data["nickname"]
        uuid = data["uuid"]
        version = data["version"]
        ram = data["ram_hr"]
        self.writeToConsole(f"Загружено \nНикнейм:{nickname} \nUUID:{uuid} \nПоследняя использованная версия:{version}")
        self.ids.nickname_input.text = nickname
        self.ids.version_input.text = version
        self.ids.dir_input.text = data["directory"]
        self.ids.ram_input.text = str(ram)
        self.setRAM(ram)

    def set_version_btn(self, version):
        self.setVersion(version)
        self.ids.version_input.text = version

    def callback_download_fabric(self):
        global version
        if False:
            minecraft_launcher_lib.fabric.install_fabric(config["directory"], version)
        else:
            version_to_download = f"fabric-loader-{minecraft_launcher_lib.fabric.get_latest_loader_version()}-{version}"
            self.writeToConsole(f"Установить fabric с официального сайта не удалось, загружаю с сервера {version_to_download}")
            shutil.rmtree(os.path.expandvars(f"%APPDATA%\\.minecraft\\versions\\{version_to_download}"), ignore_errors=True)
            shutil.rmtree(os.path.expandvars(f"%APPDATA%\\.minecraft\\versions\\{version}"), ignore_errors=True)
            self.writeToConsole("Папка для версии создана, распаковываю архив...")
            os.makedirs(os.path.expandvars(f"%APPDATA%\\.minecraft\\versions\\{version_to_download}"))
            zip_path = os.path.expandvars(f"%APPDATA%\\.resulum-launcher-data\\{version_to_download}.zip")
            try:
                download_file(f"http://yuoco.myogaya.jp:8123/fabric/{version_to_download}.zip", zip_path)
            except:
                self.writeToConsole("Загрузка данной версии с сервера недоступна, установите fabric вручную.")
                return False
            with zipfile.ZipFile(zip_path,"r") as zip_ref:
                zip_ref.extractall(os.path.expandvars(f"%APPDATA%\\.minecraft\\versions"))

        self.ids.version_input.text = f"fabric-loader-{minecraft_launcher_lib.fabric.get_latest_loader_version()}-{version}"
        version =self.ids.version_input.text
        editJSON(config["directory"] + "\\.resulum-launcher\\config.json", "version", version)
        self.writeToConsole("Fabric Loader установлен.")

    def download_fabric(self):
        global version
        self.writeToConsole("Устанавливаю fabric...")
        if version == '1.16.5' or version == '1.16.4':
            t = Thread(target=self.callback_download_fabric)
            t.daemon = True
            t.start()
        else:
            self.writeToConsole("Установка fabric доступна только для версий 1.16.5-1.16.4")
            return True

    def setRAM(self, x):
        arg = "-Xmx{}G".format(x)
        arg2 = "-Xms{}G".format(x)
        config["ram"] = [arg, arg2]
        self.writeToConsole('Выделение памяти (RAM) {}'.format(config["ram"]))
        editJSON(config["directory"] + "\\.resulum-launcher\\config.json", "ram_hr", x)
        print(x)

    def animate_versions(self, widget, *args):
        if config["vmanager_opened"]:
            animate = Animation(pos=(widget.x + 200, widget.y),duration=.1)
            config["vmanager_opened"] = False
        else:
            animate = Animation(pos=(widget.x - 200, widget.y),duration=.1)
            config["vmanager_opened"] = True
        animate.start(widget)

    def animate_settings(self, widget, *args):
        if config["settings_opened"]:
            animate = Animation(pos=(widget.x, widget.y + 270),duration=.1)
            config["settings_opened"] = False
        else:
            animate = Animation(pos=(widget.x, widget.y - 270),duration=.1)
            config["settings_opened"] = True
        animate.start(widget)

    def animate_btn_on(self, widget, *args):
        print("Press animation")
        animate = Animation(opacity=.2,duration=.05)
        animate.start(widget)

    def animate_btn_off(self, widget, *args):
        print("Release animation")
        time.sleep(.5)
        animate = Animation(opacity=1,duration=.05)
        animate.start(widget)

    def writeToConsole(self, x):
        #print(self.ids.console.text)
        self.ids.console.text += '''
        '''+"{}".format(x)

    def setDirectory(self, x):
        config["directory"] = os.path.expandvars(x)
        self.writeToConsole('Директория Minecraft изменена на {}'.format(os.path.expandvars(x)))
        editJSON(config["directory"] + "\\.resulum-launcher\\config.json", "directory", os.path.expandvars(x))
        try:
            os.makedirs(config["directory"]+"\\mods")
        except:
            pass

    def setNickname(self, x):
        global nickname, uuid
        nickname = x
        print('nickname set {}'.format(x))
        try:
            uuid = hashlib.md5(f'ResulumPlayer:{x}'.encode("utf-8")).hexdigest()
            self.writeToConsole(f"UUID: {uuid}")
            editJSON(config["directory"] + "\\.resulum-launcher\\config.json", "nickname", x)
            editJSON(config["directory"] + "\\.resulum-launcher\\config.json", "uuid", uuid)
        except:
            self.writeToConsole("Невозможно получить UUID для данного никнейма, попробуйте другие варианты.")
    def setVersion(self, x):
        global version
        version = x
        editJSON(config["directory"] + "\\.resulum-launcher\\config.json", "version", x)

class Updater(Root):
    def launch(self):
        if config["game_launched"] == True:
            return True
        config["play_btn_blocked"] = True
        #self.writeToConsole('Запускаю клиент...')
        if 'fabric' not in version:
            self.writeToConsole("Похоже, вы запускаете не fabric версию клиента")
            config["play_btn_blocked"] = False
            self.animate_btn_off(self.ids.launch_image)
            return True
        if uuid != None:
            #self.animate_btn_on(self.ids.launch_image)
            config["play_btn_blocked"] = True
            t2 = Thread(target=self.client_launch, args=(nickname, uuid, version, config["directory"], config["ram"]))
            #t2 = Thread(target=Handler.runMinecraft, args=(uuid[0:16], uuid, version, config["directory"], config["ram"]))
            t2.daemon = True
            t2.start()
            config["game_launched"] = True
            #time.sleep(5)
            #Launcher().stop()
        else:
            self.writeToConsole("Для запуска клиента установите ник.")
            config["play_btn_blocked"] = False
            self.animate_btn_off(self.ids.launch_image)

    def btn_login(self):
        if config["logged_in"] == True:
            return True

        self.animate_btn_on(self.ids.login_image)
        t = Thread(target=self.login)
        t.daemon = True
        t.start()

    def login(self):
        global nickname
        if nickname == "" or self.ids.password_input.text == "":
            self.writeToConsole("Не введён пароль и/или никнейм.")
            self.animate_btn_off(self.ids.login_image)
            return False

        password_md5 = hashlib.md5(f"{self.ids.password_input.text}".encode("utf-8")).hexdigest()
        ip = req.get('https://checkip.amazonaws.com').text.strip()
        server_response = Auth.execute_post(f"auth {nickname} {password_md5} {ip}")

        if server_response == None:
            self.writeToConsole("Нет подключения к серверу авторизации.")
            self.animate_btn_off(self.ids.login_image)
            return False
        elif "LOGGED_IN" in server_response:
            self.writeToConsole("Успешная авторизация. Приятной игры!")
            config["logged_in"] = True
            config["play_btn_blocked"] = False
            self.animate_btn_off(self.ids.launch_image)
        else:
            self.writeToConsole(f"Ошибка авторизации: {server_response}")
            self.animate_btn_off(self.ids.login_image)
            return False

    def btn_launch(self):
        if config["game_launched"] == True:
            return True
        elif config["play_btn_blocked"] == True:
            return True

        config["play_btn_blocked"] = True
        self.animate_btn_on(self.ids.launch_image)
        t = Thread(target=self.lookup_for_updates)
        t.daemon = True
        t.start()

    def download_build(self):
        file_list = glob.glob(config["directory"] + "\\mods" + r"\*.jar")
        for file in file_list:
            os.remove(file)
        data_raw = req.get(updater_config["url"] + updater_config["file"])
        #print(data_raw.text, data_raw.status_code)
        data = data_raw.json()
        #shutil.rmtree(config["directory"]+"\\mods")
        #self.writeToConsole("Removed MODS folder")
        #os.makedirs(config["directory"]+"\\mods")
        mods = data["required_mods"]
        try:
            os.makedirs(config["directory"]+"\\mods")
        except:
            pass
        for mod_name in mods:
            options = mods[mod_name]
            if options[1] == '':
                self.writeToConsole("Отсутствует URL для загрузки мода")
                continue
            t = Thread(target=self.callback_download, args=(options[1], config["directory"] + "\\mods\\" + mod_name))
            t.daemon = True
            t.start()
            #self.writeToConsole("Загружаю {}".format(mod_name))
        while config["files_downloaded"] != config["files_in_modpack"]:
            continue
        self.writeToConsole("Модпак обновлён до последней версии {}".format(data["prod_version"]))
        editJSON(config["directory"] + "\\.resulum-launcher\\config.json", "modpack_version", data["prod_version"])
        config["play_btn_blocked"] = False
        self.animate_btn_off(self.ids.launch_image)

    def lookup_for_updates(self):
        try:
            data_raw = req.get(updater_config["url"] + updater_config["file"])
        except:
            self.writeToConsole("Нет соединения с сервером :с")
            config["play_btn_blocked"] = False
            self.animate_btn_off(self.ids.launch_image)
            return True
        print(data_raw.text)
        data = data_raw.json()
        latest_modpack_version = data["prod_version"]
        config["files_in_modpack"] = data["files_in_modpack"]

        self.writeToConsole("Найдены обновления.")
        self.run_update(data["required_mods"])

    def run_update(self, mods):
        mods_dir = os.path.expandvars(config["directory"] + r"\mods")
        files_count = 0
        #print(mods_dir)
        file_list = glob.glob(mods_dir + r"\*.jar")
        for file in file_list:
            for mod_name in mods:
                #print(mod_name, mods)
                #print("PATH: {}".format(config["directory"] + "\\mods\\" + mod_name))
                if config["directory"] + "\\mods\\" + mod_name == file:
                    options = mods.get(mod_name)
                    #print("DEBUG {} $$ {}".format(md5sum(file), options[0]))
                    if md5sum(file) != options[0]:
                        os.remove(file)
                        self.download_file_class(options[1], file)
                        #self.writeToConsole("Файл {} загружен в {}".format(mod_name, file))
                    else:
                        self.writeToConsole("MD5 хеш в порядке")
                    files_count += 1
        if files_count != config["files_in_modpack"]:
            self.writeToConsole("В папке не обнаружены все необходимые моды. Скачиваю сборку заново...")
            self.download_build()
        else:
            self.writeToConsole("Модпак проверен! Все моды на месте.")
            #config["play_btn_blocked"] = False
            #self.animate_btn_off(self.ids.launch_image)
            self.launch()

class Launcher(App):
    def build(self):
        #self.icon = 'icon.ico'
        self.title = 'Resulum РВПИ лаунчер'
        return Updater()

if __name__ == '__main__':
    reset()
    Launcher().run()
