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
import threading
import socket
import datetime
import wgsd
import os

from pathlib import Path

host = '127.0.0.1' # for testing localhost is by default. change it to specific ip or '0.0.0.0'
port = 7538 # reserved port for gechat protocol.

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

all_privileges = [
    ('@user', 2),
    ('@moderator', 3),
    ('@admin', 5),
    ('@server', 7)
]

users_path = 'users/'
channels_path = 'channels/'
history_path = 'history/'
default_channel = 'chatting'
server_settings = 'settings/server.wgsd'
feedback_file = f'{history_path}feedbacks.txt'

class ChannelData:
    def __init__(self,
                 name = '',
                 available_to_these_roles = [str],
                 banned_users = [str],
                 channel_id = '',
                 
                 wgsd_init: wgsd.wgsd = None):
        self.name = name
        self.available_to_these_roles = available_to_these_roles
        self.banned_users = banned_users
        self.channel_id = channel_id # permanent id for chat history. every message will be saved into channel_id.txt
        
        self.wgsd_init = wgsd_init

    def return_itself(self):
        return self

    def rewrite(self):
        for block in self.wgsd_init.nodes:
            for key in block.matched_datas:
                match key:
                    case 'name':
                        block.matched_datas[key] = self.name
                
                    case 'available_to_these_roles':
                        block.matched_datas[key] = ''
                    
                        for role in self.available_to_these_roles:
                            block.matched_datas[key] += role + ','
                    
                        if len(block.matched_datas[key]) > 0:
                            block.matched_datas[key] = block.matched_datas[key][:-1]

                    case 'banned_users':
                        block.matched_datas[key] = ''

                        for user in self.banned_users:
                            block.matched_datas[key] += user + ','
                    
                        if len(block.matched_datas[key]) > 0:
                            block.matched_datas[key] = block.matched_datas[key][:-1]

                    case 'channel_id':
                        block.matched_datas[key] = self.channel_id
        
        with open(f'{channels_path}{self.channel_id}.wgsd', 'w') as file_stream:
            lines = self.wgsd_init.generate()
            file_stream.write(lines)
    
class UserData:
    def __init__(self, 
                 nickname = '', 
                 old_nicknames = [], 

                 nick_change_limit = 1, 
                 
                 password = '',
                 old_passwords = [],

                 roles = [
                     '@user'
                 ],
                 
                 current_ip_address = '',

                 ip_addresses = [],
                 
                 _current_socket: socket = None,
                
                 ban_reason = '',
                 current_channel = '',
                 
                 about = '',
                 
                 wgsd_init: wgsd.wgsd = None,
                 
                 language = 'english'):
        self.nickname = nickname
        self.old_nicknames = old_nicknames # not in use for now
        self.nick_change_limit = nick_change_limit
        
        self.password = password
        self.old_passwords = old_passwords

        self.roles = roles

        self.current_ip_address = current_ip_address

        self.ip_addresses = ip_addresses # not in use for now.

        self._current_socket: socket = _current_socket

        self.ban_reason = ban_reason
        self.current_channel = current_channel

        self.about = about

        self.wgsd_init = wgsd_init
        self.language = language

        self.messages_per_minute = 0
        self.history_every_hour = 0
        self.feedback_every_hour = 0
        
        self.call_every_min()
        self.call_every_hour()

    def return_itself(self):
        return self
    
    def rewrite(self):
        for block in self.wgsd_init.nodes:
            for key in block.matched_datas:
                match key:
                    case 'username':
                        block.matched_datas[key] = self.nickname
                
                    case 'password':
                        block.matched_datas[key] = self.password

                    case 'about':
                        block.matched_datas[key] = self.about
                
                    case 'current_channel':
                        block.matched_datas[key] = self.current_channel

                    case 'language':
                        block.matched_datas[key] = self.language

                    case 'roles':
                        block.matched_datas[key] = ''
                    
                        for role in self.roles:
                            block.matched_datas[key] += role + ','
                    
                        if len(block.matched_datas[key]) > 0:
                            block.matched_datas[key] = block.matched_datas[key][:-1]
        
        with open(f'{users_path}{self.nickname}.wgsd', 'w', encoding='utf8') as file_stream:
            lines = self.wgsd_init.generate()
            file_stream.write(lines)

    def call_every_min(self, f_stop = threading.Event()):
        self.messages_per_minute = 0

        if not f_stop.is_set():
            threading.Timer(60, self.call_every_min, [f_stop]).start()

    def call_every_hour(self, f_stop = threading.Event()):
        self.history_every_hour = 0
        self.feedback_every_hour = 0

        if not f_stop.is_set():
            threading.Timer(3600, self.call_every_min, [f_stop]).start()

def kick(user: UserData):
    user._current_socket.send('@Logout'.encode('utf-8'))
    current_members.remove(user)

# a tiny modification has been made upon to the code. taken from stackoverflow: stackoverflow.com/a/13790289
def read_last_n_from_history(channel_id, lines = 100, _buffer = 8092):
    file_stream = open(f'{history_path}{channel_id}.txt', 'r', encoding='utf8')
    lines_found = []
    block_counter = -1

    while len(lines_found) < lines:
        try:
            file_stream.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:
            file_stream.seek(0)
            lines_found = file_stream.readlines()
            
            break

        lines_found = file_stream.readlines()
        block_counter -= 1

    return lines_found

database: [UserData] = []
channel_list: [ChannelData] = []
current_members: [UserData] = []

languages = dict()

settings = wgsd.wgsd()
settings.parse_file(server_settings)

def how_many_users_in_channels():
    _count = dict()

    for member in current_members:
        if member.current_channel in _count:
            _count[member.current_channel] += 1
        else:
            _count[member.current_channel] = 1

    return _count

for file in Path(channels_path).rglob('*.wgsd'):
    data = ''
    x = wgsd.wgsd()
    x.parse_file(file)

    y = ChannelData(name = x.find_key('_', 'name'),
                    available_to_these_roles = x.find_key('_', 'available_to_these_roles').split(','),
                    banned_users = x.find_key('_', 'banned_users').split(','),
                    channel_id = x.find_key('_', 'channel_id'),
                    wgsd_init = x).return_itself()
                        
    channel_list.append(y)
        
for file in Path(users_path).rglob('*'):
    data = ''
    x = wgsd.wgsd()
    x.parse_file(file)

    y = UserData(nickname = x.find_key('_', 'username'),
                    password = x.find_key('_', 'password'),
                    about = x.find_key('_', 'about'),
                    current_channel = x.find_key('_', 'current_channel'),
                    language = x.find_key('_', 'language'),
                    roles = x.find_key('_', 'roles').split(','),
                    wgsd_init = x).return_itself()
    
    database.append(y)

for file in Path('l10n/').rglob('server.txt'):
    data = []

    with open(file, 'r', encoding='utf8') as file_stream:
        for line in file_stream:
            data.append(line)

        languages[file.parts[len(file.parts) - 2]] = data

def broadcast(client: UserData, message: str, is_announcement = False, index = 0, repl_params: [str] = [], params: [str] = []):
    if client != None:
        client.messages_per_minute += 1
    
        if (not any(role in client.roles for role in ['@moderator', '@admin', '@server'])) and client.messages_per_minute >= settings.find_key('_', 'messages_per_minute'):
            client._current_socket.send((f'@Error{str(languages[client.language][25])}').encode('utf-8'))
            return
    else:
        return

    date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    if (len(client.nickname) == 0) or is_announcement:
        for _client in current_members:
            temp = languages[_client.language][index]

            for i in range(0, len(params)):
                temp = temp.replace(repl_params[i], params[i])
                
            _client._current_socket.send(('@CurrentChannel' + _client.current_channel).encode('utf-8'))
            _client._current_socket.send((f'{date} -> \x1b[0;32m{temp}\x1b[0m').encode('utf-8'))
    else:    
        client._current_socket.send(('@CurrentChannel' + client.current_channel).encode('utf-8'))
        
        for channel in channel_list:
            if channel.name == client.current_channel:
                with open(f'{history_path}{channel.channel_id}.txt', 'a', encoding='utf8') as file_stream:
                    file_stream.write(f'{date} {client.nickname}: {message}\n')

                break
        
        for _client in current_members:
            _client._current_socket.send(('@CurrentChannel' + _client.current_channel).encode('utf-8'))

            if (_client.nickname != client.nickname) and (_client.current_channel == client.current_channel):
                if '@server' in client.roles:
                    _client._current_socket.send((f'{_client.current_channel} {date} \x1b[1;91m{client.nickname}\x1b[0m: {message}').encode('utf-8'))
                elif '@admin' in client.roles:
                    _client._current_socket.send((f'{_client.current_channel} {date} \x1b[0;91m{client.nickname}\x1b[0m: {message}').encode('utf-8'))
                elif '@moderator' in client.roles:                    
                    _client._current_socket.send((f'{_client.current_channel} {date} \x1b[0;31m{client.nickname}\x1b[0m: {message}').encode('utf-8'))
                else:
                    _client._current_socket.send((f'{_client.current_channel} {date} \x1b[0;34m{client.nickname}\x1b[0m: {message}').encode('utf-8'))

current_command = '' 

def handle(client: UserData):
    global current_command

    while True:
        try:
            try:
                message = str(client._current_socket.recv(8092).decode('utf-8')).strip()
            except:
                continue

            client._current_socket.send(('@CurrentChannel' + client.current_channel).encode('utf-8'))
            
            if len(message) > 0:
                if message.startswith('#'): # client commands
                    message = message.lower()
                    command = ''
                    args = []

                    if ' ' in message:
                        commands = message.split(' ')
                        command = commands[0]
                        args = commands[1:]
                    else:
                        command = message
                    
                    match command.lower():
                        case '#logout':
                            kick(client)
                        
                        case '#help':
                            help_file = '\n'
                            
                            with open(f'l10n/{client.language}/data/help.txt', 'r', encoding='utf8') as file_stream:
                                for line in file_stream:
                                    help_file += line.replace('\n', '<nl>')
                            
                            client._current_socket.send(('@Help' + help_file).encode('utf-8'))
                            continue
                        
                        case '#kick':
                            if any(role in client.roles for role in ['@moderator', '@admin', '@server']):
                                if len(args) > 0:
                                    found = False
                                    for member in current_members:
                                        if member.nickname == str(args[0]).strip():
                                            found = True
                                            if '@server' in client.roles:
                                                kick(member)
                                                client._current_socket.send(str(languages[client.language][0]).replace('{member.nickname}', member.nickname).encode('utf-8'))
                                            else:
                                                if '@admin' in client.roles:
                                                    if not ('@admin' in member.roles):
                                                        kick(member)
                                                        client._current_socket.send(str(languages[client.language][0]).replace('{member.nickname}', member.nickname).encode('utf-8'))
                                                elif '@moderator' in client.roles:
                                                    if not ('@moderator' in member.roles):
                                                        kick(member)
                                                        client._current_socket.send(str(languages[client.language][0]).replace('{member.nickname}', member.nickname).encode('utf-8'))

                                            break
                                else:
                                    client._current_socket.send(str(languages[client.language][1]).encode('utf-8'))
                                    continue

                        case '#ban' \
                            | '#unban':
                            command_lowercase = str(command).lower().strip()

                            if any(role in client.roles for role in ['@moderator', '@admin', '@server']):
                                if len(args) >= 1:
                                    if len(args) == 1 and (command_lowercase == '#ban'):
                                        client._current_socket.send(str(languages[client.language][2]).encode('utf-8'))
                                        break
                                    
                                    found = False

                                    if command_lowercase == '#unban': # banned users have not any access to the current_members due to ban. 
                                        for member in database:
                                            if member.nickname == str(args[0]).strip():
                                                found = True
                                                if '@server' in client.roles:
                                                    for user in database:
                                                        if user.nickname == member.nickname:
                                                            user.ban_reason = ''
                                                            user.rewrite()

                                                            break

                                                    client._current_socket.send(str(languages[client.language][3]).replace('{user.nickname}', user.nickname).encode('utf-8'))
                                                else:
                                                    if '@admin' in client.roles:
                                                        if not ('@admin' in member.roles):
                                                            for user in database:
                                                                if user.nickname == member.nickname:
                                                                    user.ban_reason = ''
                                                                    user.rewrite()
                                                                    break
                                                            
                                                            client._current_socket.send(str(languages[client.language][3]).replace('{user.nickname}', user.nickname).encode('utf-8'))
                                                    elif '@moderator' in client.roles:
                                                        if not ('@moderator' in member.roles):
                                                            for user in database:
                                                                if user.nickname == member.nickname:
                                                                    user.ban_reason = ''
                                                                    user.rewrite()
                                                                    break
                                                                    
                                                            client._current_socket.send(str(languages[client.language][3]).replace('{user.nickname}', user.nickname).encode('utf-8'))

                                                break
                                    else:
                                        for member in current_members:
                                            if member.nickname == str(args[0]).strip():
                                                found = True
                                                if '@server' in client.roles:
                                                    for user in database:
                                                        if user.nickname == member.nickname:
                                                            user.ban_reason = str(' '.join(args[1:])).strip()
                                                            user.rewrite()
                                                            break
                                                    
                                                    kick(member)
                                                    client._current_socket.send(str(languages[client.language][4]).replace('{member.nickname}', member.nickname).encode('utf-8'))
                                                else:
                                                    if '@admin' in client.roles:
                                                        print(client.nickname, ' ', client.roles)
                                                        if not ('@admin' in member.roles):                                                        
                                                            print('yeaa')

                                                            for user in database:
                                                                if user.nickname == member.nickname:
                                                                    user.ban_reason = str(' '.join(args[1:])).strip()
                                                                    user.rewrite()
                                                                    break

                                                            kick(member)
                                                            client._current_socket.send(str(languages[client.language][4]).replace('{member.nickname}', member.nickname).encode('utf-8'))
                                                    elif '@moderator' in client.roles:
                                                        if not ('@moderator' in member.roles):
                                                            for user in database:
                                                                if user.nickname == member.nickname:
                                                                    user.ban_reason = str(' '.join(args[1:])).strip()
                                                                    user.rewrite()
                                                                    break
                                                        
                                                            kick(member)
                                                            client._current_socket.send(str(languages[client.language][4]).replace('{member.nickname}', member.nickname).encode('utf-8'))

                                                break
                                else:
                                    if command_lowercase == '#ban':
                                        client._current_socket.send(str(languages[client.language][5 if command_lowercase == '#ban' else 6]).replace('{member.nickname}', member.nickname).encode('utf-8'))

                                    continue

                        case '#givekick' \
                            | '#giveban' \
                            | '#givemoderator' \
                            | '#giveadmin' \
                            | '#takemoderator' \
                            | '#takeadmin':
                            command_lowercase = str(command.lower()).strip()

                            match command_lowercase:
                                case '#givemoderator':
                                    role_can_be_given_by = ['@admin', '@server']
                                    role = '@moderator'
                                
                                case '#giveadmin':
                                    role_can_be_given_by = ['@server']
                                    role = '@admin'

                                case '#takemoderator':
                                    role_can_be_given_by = ['@admin', '@server']
                                    role = '_admin'
                                
                                case '#takeadmin':
                                    role_can_be_given_by = ['@server']
                                    role = '_admin'

                            if any(role in client.roles for role in role_can_be_given_by):
                                if len(args) > 0:
                                    found = False
                                    for member in database:
                                        if member.nickname == str(args[0]).strip():
                                            found = True
                                            if '@server' in client.roles:
                                                if role.startswith('_'):
                                                    if (command_lowercase == '#takeadmin') or (command_lowercase == '#takemoderator'):
                                                        member.roles.remove(role.replace('_', '@'))
                                                        client._current_socket.send(str(languages[client.language][7])
                                                                                    .replace('{member.nickname}', member.nickname)
                                                                                    .replace('{role}', role)
                                                                                    .replace('{client.nickname}', client.nickname).encode('utf-8'))
                                                else:
                                                    member.roles.append(role)
                                                    client._current_socket.send(str(languages[client.language][8])
                                                                                    .replace('{member.nickname}', member.nickname)
                                                                                    .replace('{role}', role)
                                                                                    .replace('{client.nickname}', client.nickname).encode('utf-8'))
                                                member.rewrite()
                                            else:
                                                if '@admin' in client.roles:
                                                    if role.startswith('_'):
                                                        if command_lowercase == '#takemoderator':
                                                            member.roles.remove(role.replace('_', '@'))
                                                            client._current_socket.send(str(languages[client.language][7])
                                                                                    .replace('{member.nickname}', member.nickname)
                                                                                    .replace('{role}', role)
                                                                                    .replace('{client.nickname}', client.nickname).encode('utf-8'))
                                                    else:
                                                        if not ('@admin' in member.roles):
                                                            member.roles.append(role)
                                                            client._current_socket.send(str(languages[client.language][8])
                                                                                    .replace('{member.nickname}', member.nickname)
                                                                                    .replace('{role}', role)
                                                                                    .replace('{client.nickname}', client.nickname).encode('utf-8'))
                                                    member.rewrite()
                                                elif '@moderator' in client.roles: # moderators can't take @moderator role from another moderator.
                                                    if role.startswith('_'):
                                                        client._current_socket.send(str(languages[client.language][9])
                                                                                    .replace('{client.nickname}', client.nickname)
                                                                                    .replace('{role}', role)
                                                                                    .replace('{member.nickname}', member.nickname).encode('utf-8'))
                                                    else:
                                                        if not ('@moderator' in member.roles):
                                                            member.roles.append(role)
                                                            client._current_socket.send(str(languages[client.language][8])
                                                                                    .replace('{member.nickname}', member.nickname)
                                                                                    .replace('{role}', role)
                                                                                    .replace('{client.nickname}', client.nickname).encode('utf-8'))
                                                    
                                                        member.rewrite()

                                            break
                                else:
                                    client._current_socket.send(str(languages[client.language][10])
                                                                                    .replace('{command_lowercase}', command_lowercase)
                                                                                    .replace('{role}', role).encode('utf-8'))
                                    continue

                        case '#currentmembers': # only shows up to 5, to find someone; use #searchincurrentmembers
                            command_lowercase = command.lower()
                            users = str(languages[client.language][11]).replace('{len(current_members)}', str(len(current_members))) + '\n'
                            limit = 0
                            
                            for member in current_members:
                                if limit >= 5:
                                    break

                                if current_members[limit].current_channel == client.current_channel:
                                    users += current_members[limit].nickname + '\n'
                                    limit += 1
                            
                            users = users.replace('\n', '<nl>')

                            client._current_socket.send(('@CurrentMembers' + users).encode('utf-8'))

                        case '#searchincurrentmembers':
                            if len(args) == 0:
                                client._current_socket.send((f'@Error{str(languages[client.language][23])}').encode('utf-8'))
                            else:
                                user = str(args[0]).lower().strip()
                                users = str(languages[client.language][12]) + '\n'
                                total_length = 0

                                if len(args) > 0:
                                    for members in current_members:
                                        if (user in members.nickname) and (members.current_channel == client.current_channel):
                                            users += members.nickname.replace(user, f'\x1b[1;97m{user}\x1b[0m]\n')
                                            total_length += 1

                                users = users.replace('\n', '<nl>')
                                client._current_socket.send(str("@SearchInCurrentMembers" + str(total_length) + users).encode('utf-8'))

                        case '#changepassword':
                            if len(args) > 0:
                                password = str(args[0]).lower().strip()
                                client.password = password
                                
                                client.rewrite()
                                client._current_socket.send(str(languages[client.language][13])
                                                                                    .replace('{client.nickname}', client.nickname)
                                                                                    .replace('{client.password}', client.password).encode('utf-8'))
                            else:
                                client._current_socket.send(f'@Error{str(languages[client.language][14])}'.encode('utf-8'))
                        case '#servertime':
                            client._current_socket.send(datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S").encode('utf-8'))

                        case '#about':
                            about_file = ''

                            with open(f'l10n/{client.language}/data/about.txt', 'r', encoding='utf8') as file_stream:
                                for line in file_stream:
                                    about_file += line + '\n'

                            about_file = about_file.replace('\n', '<nl>')
                            client._current_socket.send(('@About' + about_file).encode('utf-8'))

                        case '#announcements':
                            announcements_file = ''

                            with open(f'l10n/{client.language}/data/announcements.txt', 'r', encoding='utf8') as file_stream:
                                for line in file_stream:
                                    announcements_file += line + '\n'
                            
                            announcements_file = announcements_file.replace('\n', '<nl>')
                            client._current_socket.send(('@Announcements' + announcements_file).encode('utf-8'))

                        case '#rules':
                            rules_file = ''

                            with open(f'l10n/{client.language}/data/rules.txt', 'r', encoding='utf8') as file_stream:
                                for line in file_stream:
                                    rules_file += line + '\n'
                            
                            rules_file = rules_file.replace('\n', '<nl>')
                            client._current_socket.send(('@Rules' + rules_file).encode('utf-8'))

                        case '#changechannel':
                            if len(args) == 0:
                                error_msg = str(languages[client.language][24])
                            else:
                                new_channel = str(args[0]).lower().strip()
                                error_msg = ''

                                for channel in channel_list:
                                    if channel.name == new_channel:
                                        if any(role in client.roles for role in channel.available_to_these_roles):
                                            if not (client.nickname in channel.banned_users):
                                                client.current_channel = new_channel
                                                client.rewrite()
                                            else:
                                                error_msg = str(languages[client.language][15]).replace('{channel.name}', channel.name)
                                        else:
                                            error_msg = str(languages[client.language][16])
                                        break
                            
                            if len(error_msg) > 0:
                                client._current_socket.send(('@Error' + error_msg).encode('utf-8'))
                            else:
                                client._current_socket.send(('@CurrentChannel' + client.current_channel).encode('utf-8'))

                        case '#changeabout':
                            if len(args) == 0:
                                client._current_socket.send((f'@Error{str(languages[client.language][22])}').encode('utf-8'))
                            else:
                                new_about_info = str(' '.join(args[0:])).lower().strip()
                                new_about_info = new_about_info.replace('\n', '<nl>')

                                client.about = new_about_info
                                client.rewrite()

                        case '#userinfo':
                            if len(args) == 0:
                                client._current_socket.send((f'@Error{str(languages[client.language][21])}').encode('utf-8'))
                            else:
                                user_nickname = str(args[0]).lower().strip()
                                user_info = ''
                                if client.nickname == user_nickname:                                
                                    _roles = ' '.join(client.roles).strip()
                                    user_info += f'{client.nickname}<nl>{client.about}<nl>{client.current_channel}<nl>{client.password}<nl>{client.language}<nl>{_roles}'
                                elif any(role in client.roles for role in ['@admin', '@server']): # admins and server managers have the direct access to the database; mods are not. 
                                    for user in database:
                                        if user.nickname == user_nickname:
                                            _roles = ' '.join(user.roles).strip()
                                            user_info += f'{user.nickname}<nl>{user.about}<nl>{user.current_channel}<nl>'
                                            
                                            if '@server' in client.roles:
                                                user_info += f'{user.password}<nl>{user.language}<nl>{_roles}'
                                            else:
                                                user_info += f'{user.language}<nl>{_roles}'
                                            
                                            break
                                else:
                                    for user in current_members:
                                        if user.nickname == user_nickname:
                                            _roles = ' '.join(user.roles).strip()
                                            user_info += f'{user.nickname}<nl>{user.about}<nl>{user.current_channel}<nl>{user.language}<nl>{_roles}'
                                            break
                            
                                if len(user_info) > 0:
                                    client._current_socket.send((f'@UserInfo{user_info}').encode('utf-8'))

                        case '#changelanguage':
                            if len(args) == 0:
                                client._current_socket.send((f'@Error{str(languages[client.language][17])}').encode('utf-8'))
                            else:
                                new_language = str(args[0]).lower().strip()

                                if Path(f'l10n/{new_language}/').exists():
                                    client.language = new_language
                                    client.rewrite()

                                    client._current_socket.send((f'@Language{new_language}').encode('utf-8'))
                                else:
                                    client._current_socket.send((f'@Error{str(languages[client.language][27])}').encode('utf-8'))
                        
                        case '#syncserver':
                            settings.clear()
                            settings.parse_file(server_settings)

                            if any(role in client.roles for role in ['@admin', '@server']):
                                for file in Path('l10n/').rglob('server.txt'):
                                    data = []

                                    with open(file, 'r', encoding='utf8') as file_stream:
                                        for line in file_stream:
                                            data.append(line)

                                        languages[file.parts[len(file.parts) - 2]] = data # overrides old translations and adds new ones.
             
                                channel_list.clear()

                                for file in Path(channels_path).rglob('*.wgsd'):
                                    data = ''
                                    x = wgsd.wgsd()
                                    x.parse_file(file)

                                    y = ChannelData(name = x.find_key('_', 'name'),
                                                    available_to_these_roles = x.find_key('_', 'available_to_these_roles').split(','),
                                                    banned_users = x.find_key('_', 'banned_users').split(','),
                                                    channel_id = x.find_key('_', 'channel_id'),
                                                    wgsd_init = x).return_itself()
                        
                                    channel_list.append(y)
                        
                        case '#history':
                            if (not any(role in client.roles for role in ['@moderator', '@admin', '@server'])) and client.history_every_hour >= settings.find_key('_', 'history_command_per_hour'):
                                client._current_socket.send((f'@Error{str(languages[client.language][28])}').encode('utf-8'))
                            else:
                                for channel in channel_list:
                                    if channel.name == client.current_channel:
                                        _history = ''.join(read_last_n_from_history(channel.channel_id)).replace('\n', '<nl>')
                                        client.history_every_hour += 1
                                        client._current_socket.send((f'@History{_history}').encode('utf-8'))
                                        break

                        case '#feedback':
                            if len(args) == 0:
                                client._current_socket.send((f'@Error{str(languages[client.language][30])}').encode('utf-8'))
                                continue

                            if (not any(role in client.roles for role in ['@moderator', '@admin', '@server'])) and client.history_every_hour >= settings.find_key('_', 'history_command_per_hour'):
                                client._current_socket.send((f'@Error{str(languages[client.language][29])}').encode('utf-8'))
                            else:
                                with open(feedback_file, 'a', encoding='utf8') as file_stream:
                                    date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                                    feedback = ' '.join(args).strip()
                                    file_stream.write(f'{date} {client.nickname}: {feedback}\n')
                                    client._current_socket.send((f'@Feedback{str(languages[client.language][31])}').encode('utf-8'))

                        case '#channels':
                            _channels = ''
                            _count = how_many_users_in_channels()

                            for channel in channel_list:
                                if channel.name in _count:
                                    _channels += f'{channel.name} ({_count[channel.name]})<nl>'
                                else:
                                    _channels += f'{channel.name} (0)<nl>'

                            client._current_socket.send((f'@Channels{_channels}').encode('utf-8'))
                else:
                    broadcast(client, message)
        except:
            print(f'something happened, removing the client {client.nickname} from the IP {client.current_ip_address}.')
            broadcast(client, '', True, 18, ['{client.nickname}'], [client.nickname])

            try:
                current_members.remove(client)
            except:
                print(f'can\'t remove {client.nickname} from the list.')

            client._current_socket.close()

            break

def receive():
    while True:
        client, address = server.accept()
        
        # asking for username, if it's not found in our database; user will receive new user ping.
        client.send('@NickRequired'.encode('utf-8'))

        nickname = client.recv(8092).decode('utf-8').lower()

        if len(nickname) > settings.find_key('_', 'nickname_length_limit') or (not nickname.isalnum()) or (' ' in nickname):
            client.send('@UsernameLengthExceeded'.encode('utf-8'))
            client.close()
            continue

        is_user_found_in_db = False
        user_data = UserData()

        for user in database:
            if (user.nickname == nickname) and not (nickname in current_members): # user found in our database and not logged in from another session.
                client.send('@PasswordRequired'.encode('utf-8'))
                is_user_found_in_db = True
                user_data = user
                break

        if is_user_found_in_db:
            try:
                password = client.recv(8092).decode('utf-8')

                if len(password) > settings.find_key('_', 'password_length_limit'):
                    client.send('@PasswordLengthExceeded'.encode('utf-8'))
                    client.close()

                if user_data.password == password:
                    print(f'password matched for {nickname}')

                    user_data.current_ip_address = address
                    user_data._current_socket = client

                    if len(user_data.ban_reason) > 0:
                        client.send(f'@MemberBanInProgress <user>{user_data.nickname}</user> <reason>{user_data.ban_reason}</reason>'.encode('utf-8'))
                    else:
                        client.send('@ConnectionSuccessful'.encode('utf-8'))

                        result = client.recv(8092).decode('utf-8')

                        if result == '#Ping':
                            print(f'connection of a user, {nickname} from the IP {user_data.current_ip_address} has succeeded!')
                            broadcast(user_data, '', True, 19, ['{nickname}'], [nickname])

                            current_members.append(user_data)

                            thread = threading.Thread(target=handle, args=(user_data,))
                            thread.start()

                            user_roles = '@UserRoles'

                            for role in user_data.roles:
                                user_roles += f'<role>{role}</role>'
                        
                            client.send(user_roles.encode('utf-8'))
                        else:
                            print(f'{nickname} failed to connect.')
                            client.close()
                else:
                    print(f'wrong password given for {nickname} -> {password}')
                    client.send(f'@WrongPassword'.encode('utf-8'))
                    client.close()
            except:
                continue
        else:
            client.send('@NewMemberPassword'.encode('utf-8'))
            
            password = client.recv(8092).decode('utf-8')

            if len(password) > settings.find_key('_', 'password_length_limit'):
                client.send('@NewMemberPasswordLengthExceeded'.encode('utf-8'))
                client.close()
            else:
                same_address_found = False

                if address != '127.0.0.1':
                    for users in database:
                        if users.current_ip_address == address:
                            client.send('@SameAddressInUse'.encode('utf-8'))
                            client.close()
                            same_address_found = True
                            break
                
                if same_address_found:
                    continue
                        
                user_data.__init__(current_ip_address = address,
                                   _current_socket = client,
                                   nickname = nickname,
                                   password = password,
                                   current_channel=default_channel)
                
                database.append(user_data)
                
                client.send('@ConnectionSuccessful'.encode('utf-8'))

                result = client.recv(8092).decode('utf-8') # pings at first connection

                if result == '#Ping':
                    print(f'connection of a new user, {nickname} from the IP {user_data.current_ip_address} has succeeded!')
                    broadcast(user_data, '', True, 20, ['{nickname}'], [nickname])

                    x, block = wgsd.wgsd(), wgsd.block_wgsd()
                    
                    block.block_name = '_'
                    block.matched_datas = {'username': user_data.nickname,
                                           'password': user_data.password,
                                           'about': '',
                                           'current_channel': user_data.current_channel,
                                           'language': user_data.language,
                                           'roles': '@user'}

                    x.nodes.append(block)
                    
                    user_data.wgsd_init = x

                    with open(f'{users_path}{user_data.nickname}.wgsd', 'w', encoding='utf8') as file_stream:
                        file_stream.write(x.generate())
                    
                    current_members.append(user_data)

                    thread = threading.Thread(target=handle, args=(user_data,))
                    thread.start()
                else:
                    print(f'{nickname} failed to connect.')
                    client.close()
                    return

print('server is waiting for the clients.')
receive()