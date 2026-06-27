# Luniren

A feature-rich, verified Discord bot built with Python and discord.py, offering comprehensive moderation, server utilities, image commands, and fun interactions.

---

## Features

- 🔨 **Moderation** — Full suite of moderation tools covering bans, mutes, purging, channel management, role management, lockdowns, and more
- 🛠️ **Utility** — Server and user information, polls, reminders, message tools, and admin utilities
- 🖼️ **Image** — Avatar fetching, banner display, and random animal image commands
- 🎉 **Fun** — Dice rolls, 8-ball, RPS, coinflip, compliments, dad jokes, and more
- ℹ️ **Info** — Bot status, uptime, version info, invite link, and prefix management

---

## Commands

Use `lunihelp` to view all commands, or `lunihelp <command>` for details on a specific command.

### 🎉 Fun
`roll` `8ball` `choose` `rps` `coinflip` `compliment` `dadjoke`

### 🖼️ Image
`cat` `dog` `avatar` `avatarserver` `banner` `bannerserver`

### 🔨 Moderation
`announce` `ban` `banlist` `cleanup` `createchannel` `createrole` `deleterole` `deletechannel` `dump` `hackban` `kick` `listchannel` `lock` `lockdown` `massban` `massunban` `mute` `nickname` `purge` `perms` `role` `rolelist` `slowmode` `tempban` `tempmute` `temprole` `unban` `unlock` `unlockdown` `unmute` `unviewlock` `viewlock` `warn` `movechannel` `rename` `nukechannel` `clone` `topic` `deafen` `undeafen` `softban` `decancer` `dehoist`

### 🛠️ Utility
`calculate` `dm` `left` `rules` `password` `poll` `say` `id` `time` `userinfo` `channelinfo` `serverinfo` `roleinfo` `access` `joined` `firstmessage` `importemoji` `redirect` `messages` `randomcolor` `membercount` `quote` `remind` `snipe` `editsnipe` `afk` `oldest` `youngest`

### ℹ️ Info
`guildcount` `ping` `help` `prefix` `status` `version` `uptime` `sync` `invite` `contact`

---

## Prefix

Luniren supports multiple prefix types:

- **Default prefix** — `luni`
- **Mentions** — `@Luniren`
- **Slash commands** — `/`
- **Custom prefix** — Set per-server by admins and moderators using `luniprefix`

---

## Setup

1. Invite Luniren to your server using the invite link (use `luniinvite`)
2. Ensure Luniren has the necessary permissions (Administrator recommended for full functionality)
3. Optionally set a custom prefix with `luniprefix <your_prefix>`
4. Use `lunihelp` to explore available commands

---

## Tech Stack

- **Language:** Python
- **Library:** discord.py
- **Architecture:** Cog-based modular design
- **Database:** SQLite (persistent server and user data)
- **Status:** Verified on the Discord Developer Platform

---

## Repository Structure

```
Luniren/
├── main.py          # Entry point, bot initialisation, cog loader
├── cogs/
│   ├── moderation.py
│   ├── utility.py
│   ├── fun.py
│   ├── image.py
│   └── info.py
├── database/        # SQLite database layer
└── .env             # Environment config (not committed)
```

---

## Contributing

This is a personal project and not currently open to contributions, but feel free to fork and build on it.

---

## License

All rights reserved. Not licensed for redistribution or reuse without permission.
