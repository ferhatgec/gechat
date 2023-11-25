# gechat protocol reference implementation
note: gechat is still work in progress, using it in your server is in full of your responsibility.

[gech@](logo.png)

## client overview:
client part has three different messaging types:
* #commands (hashtag commands):
 * command input/outputs are client only. so that hashtag commands won't be registered into channel history; also the output is only visible to you.
 * hashtag commands are generally takes 1 or 2 arguments. if user forgot the add arguments, there's descriptive infos will be fetched from server.
* @commands (at commands):
 * a normal gechat server will not take any at commands those comes from clients. only the servers will accept those commands such that @Help, @Error etc.
 * @commands are blocks input/outputs such a short period of time by sending a buffer. if client part is changed from reference implementation, outputs can be wrong or not stylized.
* a standard message.
 * those are interpreted as a standard message, nothing fancy. there's just a single thing that may need attention:
  * gechat servers are trims front and back spaces to avoid empty (at least unvisible, i mean space and enter inputs.)
  * also, just pressing enter won't be send to the server. those are client only.

also note that, reference client part is not using any gui or tui to make interface fancy; there's just some escape sequences to sync inputs that comes from both server and another client.

## server overview:
server part needs some technical overviews:
* gechat protocol uses 7538 port by default. if this port is already on use or blocked to use by firewall; it's okay to use 75380. 
  or just use any port these ports just here for standardize connections without messing with ports.
* there's 4 types of privileges: @server, @admin, @moderator, @user.
 * @server has the most privileges who has access to the server because @server role can't be attached to others from hashtag commands. it's only possible from 'users/' folder or just set to the database by changing code. it's in full of your responsibility.
 * @admin can ban/unban/kick people that have @moderator or @user role, can use #syncserver command and access to the read-only database using hashtag commands but they have no knowledge about passwords. just name, about, roles, current channel.
 * @moderator can ban/kick people that have @user role, can't use #syncserver and no access to the read-only database only current users list.
 * @user, basic role that everyone takes @user role after creating an account. people that have @user role can receive and send messages in channels they have not been banned.
* limit for usage of commands are not applies to people that have @server role.
* there's two types or translations: server and client-side. both can be accessible from 'l10/' folder.

### gechat reference implementation licensed under the terms of MIT License.