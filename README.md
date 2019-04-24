# BinaryBackup #

###A discord bot created to completely back up your discord servers, including messages, that invites your members back afterwards.###

You can either invite this bot to your discord servers, or host it yourself.
## Invite the bot ##
[Click here](https://discordapp.com/oauth2/authorize?client_id=535811461532876823&scope=bot)

## Host it yourself ##
First clone the repository
`git clone https://github.com/Yuhanun/BinaryBackup.git`

Unpack the following folders and files into the folder where you want to host the bot:
```
backend
cogs
databases
backupbot.py
requirements.txt
```

Go into the databases folder.
Open the file `database.json`
You will see 2 keys, `Permitted` and `Token`
Put the id's of the people you want to allow to restore servers in the array behind `Permitted`.
Put your discord bot token between the "" in `Token`.

Example of a good database.json:
```json
{
    "Permitted": [
        144124542258774017,
        478177530831044608,
        553478921870508061
    ],
    "Token": "NTY24skxNTIJDISzMTc3MDkw.DyNk6w.9wHXkLkedHH5vTLEJezNrFlvpks"
}
```

If you want to edit the prefix, open backupbot.py, you'll see this line:
```python
bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or('.'), case_insensitive=True)
```
Edit the `'.'`, to the prefix you'd like, make sure it's contained between `''` or `""`

Now we are going to install the pip modules required for this bot to work:

We moved the requirements.txt to our new folder, so what we do, is simply open a terminal in that folder, and type the following:
If you're on Linux:
    `pip install -r requirements.txt`
If you're on windows:
    `py -m pip install -r requirements.txt`
    or
    `python -m pip install -r requirements.txt`

Now we simply start backupbot.py, and invite the bot using the link that shows up!

## Feel free to pull request any changes / improvements you make :) ##

# License #
This project is licensed under the MIT License - see the [LICENSE](https://github.com/Yuhanun/BinaryBackup/blob/master/LICENSE) file for details

#Acknowledgments#
Thanks to anyone whose code was used.

Buy me a coffee ;) (BTC)
32dcJ31dsxj8BMD5oD3mWKTDFSzpFHuHP1