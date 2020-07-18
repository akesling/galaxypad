import requests
import sys

server_url = "https://icfpc2020-api.testkontur.ru"
api_key = "8f96a989734a45688a78d530f60cce97"

from tree import Treeish
from vector import vector, unvector
from modulate import modulate, demodulate, Modulation


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


def send(tree: Treeish):
    data = modulate(tree).bits
    print("sending data", data)
    data = get_reply(data)
    print("got data", data)
    print("parsed vector", vector(demodulate(Modulation(data))))


def main():
    send(None)
    send(unvector([0]))


if __name__ == "__main__":
    main()
