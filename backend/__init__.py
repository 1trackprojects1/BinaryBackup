import json


def get_database():
    with open("databases/database.json", 'r') as file:
        return json.load(file)


def get_permitted():
    return get_database()["Permitted"]


def get_token():
    return get_database()["Token"]
