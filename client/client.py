import requests

import argparse


###################################################################################################
# Input is not validated at all. The server should be robust enough to withstand weird input.
###################################################################################################


api_root      = 'http://127.0.0.1:5000/api'
api_bacon     = api_root + '/bacon-number'
api_arbitrary = api_root + '/actor-number'
api_new       = api_root + '/movie'
api_multi     = api_root + '/multiple-degrees'


def user_loop():
    print('Enter nothing for both options to exit.')
    root   = input('Enter root actor: ')
    target = input('Enter target actor: ')

    while root and target:
        r = requests.get(api_arbitrary, params={'root' : root, 'target' : target})
        print(r.text)

        print('Enter nothing for both options to exit.')
        root   = input('Enter root actor: ')
        target = input('Enter target actor: ')


def file_input(file: str):
    with open(file, 'r', encoding='utf8') as f:
        data = eval(f.read())

    for k, v in data.items():
        if k == 'bacon':
            r = requests.get(api_bacon, params={'actor' : v})
            print(r.text)

        elif k == 'degree':
            r = requests.get(api_arbitrary, params={'root' : v[0], 'target' : v[1]})
            print(r.text)

        elif k == 'new':
            r = requests.post(api_new, json=v)
            print(r.text)

        elif k == 'multi':
            r = requests.get(api_multi, json=v)
            print(r.text)


def main():
    parser = argparse.ArgumentParser(description='Either manually enter actors to find the degree of separation for, or feed in a list of API requests via a file.')
    parser.add_argument('-f', '--file', help='File containing a Python dict representing server requests, one per line. See client_examples.data.')

    args = parser.parse_args()

    if args.file:
        file_input(args.file)
        return

    user_loop()


if __name__ == '__main__':
    main()
