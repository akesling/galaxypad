import requests
import sys

def req(server_url, data):
    res = requests.post(server_url, data=str(i))
    if res.status_code != 200:
        print('Unexpected server response:')
        print('HTTP code:', res.status_code)
        print('Response body:', res.text)
        exit(2)
    print('Server response:', res.text)
    return res

def main():
    server_url = sys.argv[1]
    player_key = sys.argv[2]
    print('ServerUrl: %s; PlayerKey: %s' % (server_url, player_key))

    req(server_url, player_key)
    for i in range(100000):
        res = req(server_url, str(i))

if __name__ == '__main__':
    main()
