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
    print('ServerUrl: %s; PlayerKey: %s' % (server_url, player_key))

    alien_url = server_url + '/aliens/send'
    res = req(alien_url, '1101000')
#    res = req(alien_url, res.text)
#    res = req(alien_url, res.text)
#    res = req(alien_url, res.text)

if __name__ == '__main__':
    main()
