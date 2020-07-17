import requests
import sys

def reg(server_url):  # Request get
    print("Getting", server_url)
    res = requests.get(server_url)
    if res.status_code != 200:
        print('Unexpected server response from URL "%s":' % server_url)
        print('HTTP code:', res.status_code)
        print('Response body:', res.text)
        # exit(2)
    else:
        print('Server response:', res.text)
    print('whole res')
    print(res)
    print(repr(res))
    return res

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
    print("announce")
    req(server_url, player_key)

    # Make request to aliens API
    alien_url = 'https://icfpc2020-api.testkontur.ru/aliens/send'
    print('aliens send url', alien_url)
    print('sending ""')
    req(alien_url, "")
    print('sending "1101000"')
    req(alien_url, "1101000")
    print('sending "010"')
    req(alien_url, "010")
    print('sending "0"')
    req(alien_url, "0")
    print('sending "a"')
    req(alien_url, "a")
    print('sending "hello"')
    req(alien_url, "hello")

if __name__ == '__main__':
    main()
