import json

config_path = "config.json"
default_config = {
    "token": "bot_token",
    "password": "bot_password",
    "admins_id": ["admins_id"],
    "owners_id": ["owners_id"]
}

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

update = any(
    config.get(key) == default_config[key]
    for key in default_config)

if update:
    print("Привет! Давай настроим бота...")
    config["token"] = input("Введите токен бота: ").strip()
    config["password"] = input("Введите новый пароль бота: ").strip()
    while True:
        owners_input = input("Введите ID владельцев (12345, 45678, 67890): ").strip().split(",")
        try:
            config["owners_id"] = [int(owner.strip()) for owner in owners_input]
            break
        except ValueError:
            print("Ошибка: все ID должны быть целыми числами. Попробуйте снова.")

    while True:
        admins_input = input("Введите ID администраторов без ID владельцев (12345, 45678, 67890): ").strip().split(",")
        try:
            config["admins_id"] = list(set([int(admin.strip()) for admin in admins_input if admin.strip()] + config["owners_id"]))
            break
        except ValueError:
            print("Все ID должны быть целыми числами. Попробуйте снова.")

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print("Данные обновлены.\n")

token = config["token"]
password = config["password"]
admins_id = list(map(int, config["admins_id"]))
owners_id = list(map(int, config["owners_id"]))

