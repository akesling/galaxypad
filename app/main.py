import requests
import sys


def req(server_url, data):
    print('Sending "%s"' % data)
    res = requests.post(server_url, data=data)
    if res.status_code != 200:
        print('Unexpected server response from URL "%s":' % server_url)
        print('HTTP code:', res.status_code)
        print('Response body:', res.text)
        # exit(2)
    else:
        print('Server response:', res.text)
    return res

def main():
    server_url = sys.argv[1]
    player_key = sys.argv[2]
    print('Reading parameters from command line arguments')
    print(sys.argv)
    print('ServerUrl: %s; PlayerKey: %s' % (server_url, player_key))

    # Announce
    res = req(server_url, player_key)
    print(res)
    print(repr(res))

    # Make request to aliens API
    alien_url = server_url + '/aliens/send'
    print('aliens send url', alien_url)
    res = req(alien_url, '"1101000"')
    print(res)
    print(repr(res))

if __name__ == '__main__':
    main()
