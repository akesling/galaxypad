import requests
import sys

def req(server_url, data):
    res = requests.post(server_url, data=data)
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

    alien_url = server_url + '/aliens/send'
    req(alien_url, player_key)
    req(alien_url, '1101000')
    req(alien_url, '1101000')
    res = req(alien_url, '1101000')
    res = req(alien_url, res)
    res = req(alien_url, res)

if __name__ == '__main__':
    main()
