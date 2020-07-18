import requests
import sys

server_url = "https://icfpc2020-api.testkontur.ru"
api_key = "8f96a989734a45688a78d530f60cce97"

from parser import parse_partial, unparse


def get_reply(data):
    res = requests.post(
        server_url + "/aliens/send", params=dict(apiKey=api_key), data=data
    )
    if res.status_code != 200:
        print('Unexpected server response from URL "%s":' % server_url)
        print("HTTP code:", res.status_code)
        print("Response body:", res.text)
        raise ValueError("Server response:", res.text)
    return res.text


def send(data):
    print("sending data", data)
    data = get_reply(data)
    if data != '1101000':
        print("got data", data)
        value, remainder = parse_partial(data)
        print("parsed value", value)
        print("parsed remainder", remainder)

def main():
    send("")
    send(unparse([0, []]))


if __name__ == "__main__":
    main()
