import requests
import sys

def main():
    server_url = sys.argv[1]
    player_key = sys.argv[2]
    print('ServerUrl: %s; PlayerKey: %s' % (server_url, player_key))

    for i in range(100000):
        res = requests.post(server_url, data=str(i))
        if res.status_code != 200:
            print('Unexpected server response:')
            print('HTTP code:', res.status_code)
            print('Response body:', res.text)
            exit(2)
        print('Server response:', res.text)

if __name__ == '__main__':
    main()
