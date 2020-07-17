import requests
import sys

server_url = "https://icfpc2020-api.testkontur.ru"
player_key = "8f96a989734a45688a78d530f60cce97"


def get_reply(data):
    res = requests.post(
        server_url + "/aliens/send", params=dict(apiKey=player_key), data=data
    )
    if res.status_code != 200:
        print('Unexpected server response from URL "%s":' % server_url)
        print("HTTP code:", res.status_code)
        print("Response body:", res.text)
        raise ValueError("Server response:", res.text)
    return res.text


def main():
    data = ""
    for _ in range(5):
        print("sending data", data)
        data = get_reply(data)
        print("got data", data)


if __name__ == "__main__":
    main()
