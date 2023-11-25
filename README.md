# gechat protocol reference implementation
note: gechat is still work in progress, using it in your server is in full of your responsibility.

[gech@](logo.png)

## client overview:
client part has three different messaging types:
* #commands (hashtag commands):
 * hashtag command input/outputs are client only. so that hashtag commands won't be registered into channel history. also the output is only visible to you.
 * hashtag commands are generally takes 1 or 2 arguments. if user forgot to add arguments, there are some descriptive infos whose will be fetched from server.
* @commands (at commands):
 * a normal gechat server will not take any at commands those comes from clients. only the servers will send those commands such that @Help, @Error etc.
 * @commands are generally blocks socket input/outputs for such a short period of time by sending a buffer to the client/s. if client part has modified before -from reference implementation-, outputs can be wrong or not stylized.
* a standard message.
 * those are interpreted as a standard message, nothing fancy. there's just a single thing that may need attention:
  * gechat servers generally trims messages as front and back to avoid empty (at least unvisible, i mean space and enter inputs.) messages.
  * also, just pressing enter key won't be send that directly to the server. those are client only, will be declined from server.

also note that, reference client part is not using any gui or tui to make interface fancy; there's just some escape sequences to sync inputs that comes from both server and another client.

## server overview:
server part needs some technical overviews:
* gechat protocol uses 7538 port by default. if this port is already in use or blocked for usage by firewall; it's okay to use 17538. 
  or just use any port, these ports just here for standardize connections without messing with ports to find which port is open; and to avoid port collisions.
* gechat has 4 types of privileges: @server, @admin, @moderator, @user.
 * @server has the most privileges who directly has access and modify privileges to the server because @server role can't be attached to others by using hashtag commands. it's only possible by changing metadata from 'users/' folder; or by modifying protocol implementation. it's in full of your responsibility.
 * @admin can ban/unban/kick people for those who have @moderator or @user role. they can use #syncserver command and access to the read-only database by using hashtag commands but they are limited to have no knowledge about passwords. just name, about, roles, current channel are what people with @admin role can access to.
 * @moderator can ban/kick people that have @user role, can't use #syncserver and no access to the read-only database. they have access to the read-only current users list.
 * @user, basic role that everyone takes that. @user role has been given to you after creating an account. people that have @user role can receive and send messages in channels that they have not been banned in.
* limits for usage of commands are not applies to people that have @server role, they also have the permissions to change server settings while people with @admin role are not.
* gechat has two types of translations: server- and client-side. both can be accessible and modifiable from 'l10n/' folder.

### gechat reference implementation licensed under the terms of MIT License.