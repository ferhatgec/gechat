# gechat protocol reference implementation (still work in progress, 
#                                           i don't take any responsibility from any problem that happened on your server 
#                                           because of the gechat reference implementation)
# ----
# gechat is text based protocol for messaging in real time; that supports
#  channels
#  privileges
#  message storing, history
#  localization
#  feedback
#  sync without breaking connections
#  etc. etc. in next updates.
# 
# there's no any end-to-end encryption yet.
#
# why not just implement irc server/client?
#  - developing something under the name irc gives us the responsibility of implementing irc server/client by rfc papers.
#    there can be simple implementations of irc but you need to call your implementation as 'simple'.
#  - there are more servers in irc, which is plus; but i prefer the flexibility of our tool. 
#  - gechat is cool name, simultaneously irc is not.
#
# MIT License
#
# Copyright (c) 2023 Ferhat Geçdoğan All Rights Reserved.
# Distributed under the terms of the MIT License.
#
#
import socket
import threading
import datetime
import sys

translation = []

if len(sys.argv) > 1:
    if sys.argv[1].lower() == 'turkish':
        with open('l10n/turkish/client.txt', 'r', encoding='utf8') as file_stream:
            for line in file_stream:
                translation.append(line.replace('\n', '').replace('\\n', '\n').replace('\\w', ' '))

if len(translation) == 0:
    with open('l10n/english/client.txt', 'r', encoding='utf8') as file_stream:
        for line in file_stream:
            translation.append(line.replace('\n', '').replace('\\n', '\n').replace('\\w', ' '))

if len(translation) < 16:
    print('localization files are missing. aborting current session.')
    exit(1)

print(translation[0])

gechat_server = input(translation[1])

while len(gechat_server) == 0:
    gechat_server = input(translation[1])

nickname = input(translation[2])

while len(nickname) == 0:
    print(translation[3])
    nickname = input(translation[2])

if gechat_server == 'localhost':
    gechat_server = '127.0.0.1'

port = input('port: ')

while len(port) == 0:
    port = input('port: ')

if str(port).lower() == 'gechat' \
    or str(port).lower() == 'default':
    port = 7538
else:
    port = abs(int(port))

if port > 65535:
    port = 7538

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((gechat_server, port)) # specific gechat port

socket_closed = False
login_successful = False

current_channel = ''
colorful_nickname = f'\x1b[0;34m{nickname}\x1b[0m'

def receive():
    global client, socket_closed, login_successful, colorful_nickname, current_channel

    while True:
        try:
            message = client.recv(8092).decode('utf-8').strip()

            if len(message) == 0:
                continue
            
            if message == '@Logout':
                client.close()
                socket_closed = True
                login_successful = False
                
                break
            elif message.startswith('@SameAddressInUse'):
                print(str(translation[15]))
                break
            elif message.startswith('@CurrentChannel'):
                current_channel = message[len('@CurrentChannel'):]
                continue
            elif message.startswith('@Help'):
                message = message[len('@Help'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@CurrentMembers'):
                message = message[len('@CurrentMembers'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@SearchInCurrentMembers'):
                message = message[len('@SearchInCurrentMembers'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@About'):
                message = message[len('@About'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@Announcements'):
                message = message[len('@Announcements'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@Rules'):
                message = message[len('@Rules'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@Error'):
                message = message[len('@Error'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@UserRoles'):
                message = message[len('@UserRoles'):]
                if '<role>@server</role>' in roles:
                    colorful_nickname = f'\x1b[1;91m{nickname}\x1b[0m'
                elif '<role>@admin</role>' in roles:
                    colorful_nickname = f'\x1b[0;91m{nickname}\x1b[0m'
                elif '<role>@moderator</role>' in roles:
                    colorful_nickname = f'\x1b[0;31m{nickname}\x1b[0m'
                
                continue
            elif message.startswith('@UserInfo'):
                message = message[len('@UserInfo'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@Language'):
                message = message[len('@Language'):]
                translation.clear()
                
                with open(f'l10n/{message}/client.txt', 'r', encoding='utf8') as file_stream:
                    for line in file_stream:
                        translation.append(line.replace('\n', '').replace('\\n', '\n').replace('\\w', ' '))

                continue
            elif message.startswith('@History'):
                message = message[len('@History'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@Feedback'):
                message = message[len('@Feedback'):].replace('<nl>', '\n')
                print(message)
                continue
            elif message.startswith('@Channels'):
                message = message[len('@Channels'):].replace('<nl>', '\n')
                print(message)
                continue
            
            if message == '@NickRequired':
                client.send(nickname.encode('utf-8'))

                try:
                    result = client.recv(8092).decode('utf-8').strip()
                    arguments = ''

                    if result == '@UsernameLengthExceeded':
                        print(translation[4])
                        client.close()
                        socket_closed = True
                        break
                    
                    if result == '@PasswordRequired':
                        password = input(str(translation[14]).replace('{nickname}', nickname))
                        client.send(password.encode('utf-8'))

                        try:
                            result = client.recv(8092).decode('utf-8')
                        
                            if ' ' in result:
                                data = result.split(' ', 1)
                                result = data[0]
                                arguments = str(data[1:])
                            
                            if result == '@PasswordLengthExceeded':
                                print(translation[5])
                                client.close()
                                socket_closed = True
                                return
                            elif result == '@ConnectionSuccessful':
                                print(translation[6])
                                login_successful = True

                                try:
                                    client.send('#Ping'.encode('utf-8'))
                                    roles = client.recv(8092).decode('utf-8')
                                except:
                                    continue
                            elif result == '@MemberBanInProgress':
                                if ('<reason>' in arguments) and ('</reason>' in arguments):
                                    print(str(translation[7])
                                          .replace('{nickname}', nickname)
                                          .replace('{reason}', arguments[arguments.find('<reason>') + len('<reason>') : arguments.find('</reason>')]))
                                    
                                client.close()
                                socket_closed = True
                                return
                            elif result == '@WrongPassword':
                                print(translation[8])
                                client.close()
                                socket_closed = True
                                return
                            else:
                                print(translation[9])
                                client.close()
                                socket_closed = True
                                return    
                        except:
                            continue
                    elif result == '@NewMemberPassword':
                        password = input(str(translation[10]).replace('{nickname}', nickname))

                        while len(password) == 0:
                            password = input(str(translation[10]).replace('{nickname}', nickname))
                        
                        client.send(password.encode('utf-8'))

                        try:
                            result = client.recv(8092).decode('utf-8')
                            
                            if result == '@NewMemberPasswordLengthExceeded':
                                print(translation[5])
                                client.close()
                                socket_closed = True
                                break
                    
                            if result == '@ConnectionSuccessful':
                                print(translation[6])
                                
                                login_successful = True

                                try:
                                    client.send('#Ping'.encode('utf-8'))
                                    roles = client.recv(8092).decode('utf-8')
                                        
                                except:
                                    continue
                        except:
                            continue
                    else:
                        print(translation[9])
                        client.close()
                        socket_closed = True
                        break
                except:
                    continue
            else:            
                date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                print(end=f'\x1b[K\n{message}\n{current_channel} {date} {colorful_nickname}: ')
                continue
        except:
            print(translation[13])
            client.close()
            socket_closed = True
            break


def write():
    global socket_closed, login_successful, current_channel
    
    while True:
        if socket_closed:
            print(translation[12])
            break

        if login_successful:
            date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            message = input(f'{current_channel} {date} {colorful_nickname}: ')

            if len(message) == 0:
                continue

            if len(message) >= 1 and message[0] == '#':
                message = message[1:].lower()

                if not socket_closed:
                    client.send(f'#{message}'.encode('utf-8'))

                continue

            if not socket_closed:
                client.send(str(message).encode('utf-8'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()