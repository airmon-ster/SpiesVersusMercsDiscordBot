import os
import sqlite3 as sql
import signal
import sys
import uuid
import re
import random
import discord
from discord.ext import commands, tasks
from discord import CategoryChannel
from dotenv import load_dotenv
# from include.elo_system import * # not going to use right now

# get hidden discord token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN') # set up a .env file and put DISCORD_TOKEN = xxxx

SERVER_ID = 873576006307418172 # instinct test server. change

# save/commit db changes if ctrl_C is pressed
def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Saving and committing...')
    sqlCon.commit()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

class SpyMercList(list): # ensures there is a Spy/Merc class in a list
    def __contains__(self, typ):
        for val in self:
            if isinstance(val, typ):
                return True
        return False

class Spy:
  def __init__(self, discordID):
    self.discordID = discordID
    self.userName = bot.get_user(int(discordID)).name
    self.stats = getUserPoints(int(discordID))
    self.spyExtPoints = self.stats[1]
    self.spyNeuPoints = self.stats[2]
    self.spySabPoints = self.stats[3]
    self.totalPoints = self.stats[7]
    self.wins = self.stats[8]
    self.losses = self.stats[9]

class Merc:
  def __init__(self, discordID):
    self.discordID = discordID
    self.userName = bot.get_user(int(discordID)).name  # make sure to uncomment. just commented out for use with fake users and testing
    self.stats = getUserPoints(int(discordID))
    self.mercExtPoints = self.stats[4]
    self.mercNeuPoints = self.stats[5]
    self.mercSabPoints = self.stats[6]
    self.totalPoints = self.stats[7]
    self.wins = self.stats[8]
    self.losses = self.stats[9]


def getUserPoints(discordID):
    try:
        result = ()
        pointInfo = sqlCon.execute("SELECT * from users where discordID = ?", (discordID,))
        for points in pointInfo:
            result = points
        print(str(result))
        return result
    except:
        return None

def checkIfRegistered(discordID):
    try:
        result = ()
        playerInfo = sqlCon.execute("SELECT discordID from users where discordID = ?", (discordID,))
        for p in playerInfo:
            result = p
        print(str(result))
        if (len(result) == 1):
            return True
        else:
            return False
    except:
        return False

async def idToName(discordID):
    try:
        guild = await bot.fetch_guild(SERVER_ID)
        playerMember = await guild.fetch_member(int(discordID))

        if playerMember.nick is not None:
            if re.match("^\d\s-\s", playerMember.nick): # does it already match our rank scheme
                playerName = re.split("^\d\s-\s", playerMember.nick)[1]
            else:
                playerName = playerMember.nick
        else:
            playerName = playerMember.name
            #name = bot.get_user(int(discordID))
        return playerName
    except:
        return "UnknownName"

# used to confirm that a given uuid for confirm function is legit
async def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False



async def scorecard(players, gameMode, winner):
    try:
        elo = EloSystem(base_elo = 1200, k = 32)
        if winner == "SPIES":
            for x in players:
                if type(x) is Spy:
                    x.wins += 1
                    if gameMode == "NEU":
                        #if (x.spyNeuPoints < 200) :
                        x.spyNeuPoints += 50
                        x.totalPoints += 50
                        sqlCon.execute("UPDATE users set spyNeu = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.spyNeuPoints, x.wins, x.totalPoints, x.discordID))
                        sqlCon.commit()
                    if gameMode == "EXT":
                        #if (x.spyExtPoints < 200):
                        x.spyExtPoints += 50
                        x.totalPoints += 50
                        sqlCon.execute("UPDATE users set spyExt = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.spyExtPoints, x.wins, x.totalPoints, x.discordID))
                        sqlCon.commit()
                    if gameMode == "SAB":
                        #if (x.spySabPoints < 200):
                        x.spySabPoints += 50
                        x.totalPoints += 50
                        sqlCon.execute("UPDATE users set spySab = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.spySabPoints, x.wins, x.totalPoints, x.discordID))
                        sqlCon.commit()
                if type(x) is Merc:
                    x.losses += 1
                    sqlCon.execute("UPDATE users set losses = ? WHERE discordID = ?", (x.losses, x.discordID))
                    sqlCon.commit()

                    if gameMode == "NEU":
                        if (x.merdNeuPoints > 200) :
                            x.mercNeuPoints -= 10
                            x.totalPoints -= 10
                            sqlCon.execute("UPDATE users set mercNeu = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.mercNeuPoints, x.wins, x.totalPoints, x.discordID))
                            sqlCon.commit()
                    if gameMode == "EXT":
                        if (x.mercExtPoints > 200):
                            x.mercExtPoints -= 10
                            x.totalPoints -= 10
                            sqlCon.execute("UPDATE users set mercExt = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.mercExtPoints, x.wins, x.totalPoints , x.discordID))
                            sqlCon.commit()
                    if gameMode == "SAB":
                        if (x.mercSabPoints > 200):
                            x.mercSabPoints -= 10
                            x.totalPoints -= 10
                            sqlCon.execute("UPDATE users set mercSab = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.mercSabPoints, x.wins, x.totalPoints, x.discordID))
                            sqlCon.commit()


                # update nickname / level
                guild = await bot.fetch_guild(SERVER_ID)
                playerMember = await guild.fetch_member(int(x.discordID))

                if playerMember.nick is not None:
                    if re.match("^\d\s-\s", playerMember.nick): # does it already match our rank scheme
                        oldName = re.split("^\d\s-\s", playerMember.nick)[1]
                    else:
                        oldName = playerMember.nick
                else:
                    oldName = playerMember.name
                
                numberOfGames = x.losses + x.wins
                removeFinalDigit = str(numberOfGames)[0:int(len(str(numberOfGames))-1)]
                newName = str(removeFinalDigit) + " - " + oldName

                await playerMember.edit(nick=newName)





        if winner == "MERCS":
            for x in players:
                if type(x) is Merc:
                    x.wins += 1
                    if gameMode == "NEU":
                        #if (x.merdNeuPoints < 200) :
                        x.mercNeuPoints += 50
                        x.totalPoints += 50
                        sqlCon.execute("UPDATE users set mercNeu = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.mercNeuPoints, x.wins, x.totalPoints, x.discordID))
                        sqlCon.commit()
                    if gameMode == "EXT":
                        #if (x.mercExtPoints < 200):
                        x.mercExtPoints += 50
                        x.totalPoints += 50
                        sqlCon.execute("UPDATE users set mercExt = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.mercExtPoints, x.wins, x.totalPoints , x.discordID))
                        sqlCon.commit()
                    if gameMode == "SAB":
                        #if (x.mercSabPoints < 200):
                        x.mercSabPoints += 50
                        x.totalPoints += 50
                        sqlCon.execute("UPDATE users set mercSab = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.mercSabPoints, x.wins, x.totalPoints, x.discordID))
                        sqlCon.commit()
                if type(x) is Spy:
                    x.losses += 1
                    sqlCon.execute("UPDATE users set losses = ? WHERE discordID = ?", (x.losses, x.discordID))
                    sqlCon.commit()

                    if gameMode == "NEU":
                        if (x.spyNeuPoints > 200) :
                            x.spyNeuPoints -= 10
                            x.totalPoints -= 10
                            sqlCon.execute("UPDATE users set spyNeu = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.spyNeuPoints, x.wins, x.totalPoints, x.discordID))
                            sqlCon.commit()
                    if gameMode == "EXT":
                        if (x.spyExtPoints > 200):
                            x.spyExtPoints -= 10
                            x.totalPoints -= 10
                            sqlCon.execute("UPDATE users set spyExt = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.spyExtPoints, x.wins, x.totalPoints, x.discordID))
                            sqlCon.commit()
                    if gameMode == "SAB":
                        if (x.spySabPoints > 200):
                            x.spySabPoints -= 10
                            x.totalPoints -= 10
                            sqlCon.execute("UPDATE users set spySab = ?, wins = ?, totalPoints = ? WHERE discordID = ?", (x.spySabPoints, x.wins, x.totalPoints, x.discordID))
                            sqlCon.commit()


                # update nickname / level
                guild = await bot.fetch_guild(SERVER_ID)
                playerMember = await guild.fetch_member(int(x.discordID))

                if playerMember.nick is not None:
                    if re.match("^\d\s-\s", playerMember.nick): # does it already match our rank scheme
                        oldName = re.split("^\d\s-\s", playerMember.nick)[1]
                    else:
                        oldName = playerMember.nick
                else:
                    oldName = playerMember.name
                
                numberOfGames = x.losses + x.wins
                removeFinalDigit = str(numberOfGames)[0:int(len(str(numberOfGames))-1)]
                newName = str(removeFinalDigit) + " - " + oldName
                await playerMember.edit(nick=newName)



    except Exception as e:
        print(e)


# open up the db for use
with sql.connect('svmranks.db') as sqlCon:
    try:

        # required tables
        # create table matches(matchID TEXT primary key, spyOne INTEGER, spyTwo INTEGER, mercOne INTEGER, mercTwo INTEGER, gameMode TEXT, winner TEXT, confirmed BOOLEAN);
        # create table users(discordID INTEGER UNIQUE, spyExt INTEGER DEFAULT 0, spyNeu INTEGER DEFAULT 0, spySab INTEGER DEFAULT 0, mercExt INTEGER DEFAULT 0, mercNeu INTEGER DEFAULT 0, mercSab INTEGER DEFAULT 0, totalPoints INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0);

        # test/fake users and scores
        # insert into users values(236948883819855872,0,0,0,0,0,0,0,0,0);
        # insert into users values(415363016935079937,0,0,0,0,0,0,0,0,0);
        # insert into users values(264604675846701056,0,0,0,0,0,0,0,0,0);
        # insert into users values(361912382059970560,0,0,0,0,0,0,0,0,0);

        sqlCon.execute("create table if not exists matches(matchID TEXT primary key, spyOne INTEGER, spyTwo INTEGER, mercOne INTEGER, mercTwo INTEGER, gameMode TEXT, winner TEXT, confirmed BOOLEAN);")
        sqlCon.execute("create table if not exists users(discordID INTEGER UNIQUE, spyExt INTEGER DEFAULT 0, spyNeu INTEGER DEFAULT 0, spySab INTEGER DEFAULT 0, mercExt INTEGER DEFAULT 0, mercNeu INTEGER DEFAULT 0, mercSab INTEGER DEFAULT 0, totalPoints INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0);")
        sqlCon.commit()

        #allow discord to query user information
        intents = discord.Intents.all()
        intents.members = True

        #create bot object
        bot = commands.Bot(command_prefix='!rank ', intents=intents)


        #report a match outcome
        @bot.command(name="report", help="!rank report <lobby_name (Alpha/Bravo etc.)> <game-mode (Neutralization, Sabotage, Extraction)> <winning-team (Spies/Mercs)>")
        async def reportMatch(ctx, category: CategoryChannel, gameMode, winner):
            try:
                gameModes = ["EXT", "NEU", "SAB"]
                winnerTypes = ["SPIES", "MERCS"]

                if ((gameMode.upper() not in gameModes) or (winner.upper() not in winnerTypes)):
                    await ctx.send(f"```Gamemode (EXT,NEU,SAB) or Winner Type (SPIES,MERCS) parameters not recognized.```")
                    return

                players = []

                #this section works. ready for testing
                spies_channel = discord.utils.get(category.channels, name="SPIES", type=discord.ChannelType.voice)
                spy_ids = spies_channel.voice_states.keys()
                # spy_results = []
                if (len(spy_ids) == 2):
                    for discordID in spy_ids:
                        if (checkIfRegistered(discordID)):
                            players.append(Spy(discordID))
                        else:
                            await ctx.send(f"```{bot.get_user(int(discordID))} is not registered.```")
                            return
                else:
                    await ctx.send(f"```There must be 2 players in each voice channel (Spies/Mercs)```")
                    return

                mercs_channel = discord.utils.get(category.channels, name="MERCS", type=discord.ChannelType.voice)
                merc_ids = mercs_channel.voice_states.keys()
                # merc_results = []
                if (len(merc_ids) == 2):
                    for discordID in merc_ids:
                        if (checkIfRegistered(discordID)):
                            players.append(Spy(discordID))
                        else:
                            await ctx.send(f"```{bot.get_user(int(discordID))} is not registered.```")
                            return
                else:
                    await ctx.send(f"```There must be 2 players in each voice channel (Spies/Mercs)```")
                    return



                #test users and array
                # players = [] # spyOne,spyTwo,mercOne,mercTwo

                # players.append(Spy(361912382059970560)) # instinct
                # players.append(Spy(236948883819855872)) # test players xec
                # players.append(Merc(415363016935079937)) # test player mrg
                # players.append(Merc(264604675846701056)) # sneaky

                # for player in players:
                #     if (checkIfRegistered(player.discordID)):
                #         print("Player is registered: ", bot.get_user(int(player.discordID)))


                if (len(players) != 4):
                    await ctx.send(f"```There must be 2 players in each voice channel (Spies/Mercs)```")
                    return
                

                # print(players)

                
                # custom type checker to ensure there is at least 1 spy and 1 merc
                typeChecker = SpyMercList(players)

                # this check intends to see if there were only mercs or only spies in the voice lobby. You need at least 1 spy if there are mercs or at least 1 merc if there are spies. Needs to be tested
                if ((Spy not in typeChecker) or (Merc not in typeChecker)):
                    await ctx.send(f"```There was either a spy or merc missing in the player list.```")
                    return

                
                # at this point everybody should be registered, got their object set up, and ensured there was at least 1 spy and 1 merc
                uuidGen = str(uuid.uuid4())
                # sqlCon.execute("INSERT INTO matches values(?,?,?,?,?,?,?,0)",(uuidGen, jsonpickle.encode(players[0]),jsonpickle.encode(players[1]), jsonpickle.encode(players[2]), jsonpickle.encode(players[3]), gameMode.upper(), winner.upper()))
                sqlCon.execute("INSERT INTO matches values(?,?,?,?,?,?,?,0)",(uuidGen, players[0].discordID, players[1].discordID, players[2].discordID, players[3].discordID, gameMode.upper(), winner.upper()))

                sqlCon.commit()

                spy_names = []
                spy_names.append(await idToName(players[0].discordID))
                spy_names.append(await idToName(players[1].discordID))

                merc_names = []
                merc_names.append(await idToName(players[2].discordID))
                merc_names.append(await idToName(players[3].discordID))

                partition = "==================================\n"

                formatted_spies = "\n".join(spy_names)
                formatted_mercs = "\n".join(merc_names)

                for player in players:
                    await bot.get_user(int(player.discordID)).send(f"New Ranking Request: \n{partition}Spies:\n{formatted_spies}\n{partition}Mercs:\n{formatted_mercs}\n{partition}GameMode: {gameMode}\n{partition}Winning Team: {winner}\n{partition}\nMatches are confirmed and validated every 2 minutes.\nBefore validation, anybody in the match can reject it by copying and pasting the following bot command:\n```!rank reject {uuidGen}```")



                await ctx.send(f"```Rank Request sent: {uuidGen}```")

                #await scorecard(players, gameMode.upper(), winner.upper()) # should do this after confirmation

            except Exception as e:
                #await ctx.send(e)
                await ctx.send("```There was an error. Please confirm information entered and ensure all players are registered and that there are two spies and two mercs in their appropriate channels.```")


        # ============== HELP ================#
        @bot.command(name='helpEx', help='!rank helpEx - Shows detailed help information.')
        async def helpEx(ctx):
            await ctx.send(f"```!rank register - Enters calling player into the database. Required.\n!rank report <case sensitive voice channel> <game mode (\'sab, neu, ext\')> <winner (\'spies, mercs\')>\n!rank top - See top 10 in leaderboard.\n!rank reject <uuid> - Reject given match outcome. Deletes from DB.\n!rank viewplayer <discord ID> - View stats of given Discord ID.\n!rank mapgen - Suggests a map and mode based on weighted criteria.```")



        # ============== MAP SUGGESTOR ================#
        @bot.command(name='mapgen', help='!rank mapgen - Shows detailed help information.')
        async def mapgen(ctx):
            try:
                mapCombos = [
                'Deftech Belew / Extraction',
                'Deftech Belew / Neutralisation',
                'Deftech Belew / Sabotage',
                'Cinema / Neutralisation',
                'Factory / Extraction',
                'Factory / Neutralisation',
                'Factory / Sabotage',
                'Krauser Lab / Extraction',
                'Krauser Lab / Neutralisation',
                'Krauser Lab / Sabotage',
                'Missile Strike / Extraction',
                'Missile Strike / Neutralisation',
                'Missile Strike / Sabotage',
                'Mount Hospital / Extraction',
                'Mount Hospital / Neutralisation',
                'Mount Hospital / Sabotage',
                'Museum / Neutralisation',
                'Museum / Sabotage',
                'Orphanage / Extraction',
                'Orphanage / Neutralisation',
                'Orphanage / Sabotage',
                'Schermerhorn / Extraction',
                'Schermerhorn / Neutralisation',
                'Schermerhorn / Sabotage',
                'Station / Extraction',
                'Station / Neutralisation',
                'Station / Sabotage',
                'Vertigo Plaza / Extraction',
                'Vertigo Plaza / Neutralisation',
                'Warehouse / Extraction',
                'Warehouse / Neutralisation',
                ]


                weights = [
                4, # 'Deftech Belew / Extraction',
                2, # 'Deftech Belew / Neutralisation',
                2, # 'Deftech Belew / Sabotage',
                7, # 'Cinema / Neutralisation',
                1, # 'Factory / Extraction',
                2, # 'Factory / Neutralisation',
                1, # 'Factory / Sabotage',
                1, # 'Krauser Lab / Extraction',
                2, # 'Krauser Lab / Neutralisation',
                6, # 'Krauser Lab / Sabotage',
                1, # 'Missile Strike / Extraction',
                2, # 'Missile Strike / Neutralisation',
                1, # 'Missile Strike / Sabotage',
                2, # 'Mount Hospital / Extraction',
                7, # 'Mount Hospital / Neutralisation',
                10, # 'Mount Hospital / Sabotage',
                7, # 'Museum / Neutralisation',
                8, # 'Museum / Sabotage',
                1, # 'Orphanage / Extraction',
                8, # 'Orphanage / Neutralisation',
                10, # 'Orphanage / Sabotage',
                2, # 'Schermerhorn / Extraction',
                4, # 'Schermerhorn / Neutralisation',
                1, # 'Schermerhorn / Sabotage',
                2, # 'Station / Extraction',
                4, # 'Station / Neutralisation',
                10, # 'Station / Sabotage',
                1, # 'Vertigo Plaza / Extraction',
                3, # 'Vertigo Plaza / Neutralisation',
                7, # 'Warehouse / Extraction',
                5, # 'Warehouse / Neutralisation',
                ]

                topThree = random.choices(mapCombos, weights=weights, k=3)
                formattedResults = "\n".join(topThree)
                partition = "==================================\n"
                await ctx.send(f"```Top Three Choices:\n{partition}{formattedResults}```") # return top 3 choices
            except Exception as e:
                await ctx.send("```There was an error during random map suggestion generation.```")

        # ============== REGISTER ================#
        # Register and init db entry
        @bot.command(name='register', help='!rank register - Enters user into the DB for ranking.')
        async def register(ctx):
            try:
                userSubscriptionID = int(ctx.message.author.id) #get the raw, global user id
                userSubscriptionObject = bot.get_user(int(userSubscriptionID)) #turn global user id into friendly discord id (e.g. username#1337)

                sqlCon.execute("INSERT INTO users(discordID) VALUES (?);", (userSubscriptionID,))
                sqlCon.commit()



                # update nickname / level
                guild = await bot.fetch_guild(SERVER_ID)
                playerMember = await guild.fetch_member(int(userSubscriptionID))

                if playerMember.nick is not None:
                    if re.match("^\d\s-\s", playerMember.nick): # does it already match our rank scheme
                        oldName = re.split("^\d\s-\s", playerMember.nick)[1]
                    else:
                        oldName = playerMember.nick
                else:
                    oldName = playerMember.name
                
                newNick = "0 - " + oldName
                
                await playerMember.edit(nick=newNick)
                await ctx.send(f"```Registered: {str(newNick)}.```")
            except Exception as e:
                await ctx.send("```There was an error during registration or user is already registered.```")



        # ============== CONFIRM/UPDATE ================# GOING FOR AUTO CONFIRM UNLESS REJECTED INSTEAD
        # # update matches set confirmed = 1 where id = 'uuid4';
        # @bot.command(name='confirm', help='!rank confirm <uuid>: Confirms a given TK instance.')
        # async def confirm(ctx, uuidGen):
        #     try:
        #         if (await is_valid_uuid(uuidGen)):
        #             username = ctx.message.author.id
        #             confirmations = ""
        #             results = sqlCon.execute("SELECT confirmations from matches where matchID = ?;", (uuidGen,))
        #             for id in results:
        #                 confirmations = id[0]
        #             if (confirmations):
        #                 confirmations += 1
        #                 sqlCon.execute("update matches set confirmations = ? where matchID = ?;", (confirmations, uuidGen))
        #                 await ctx.send(f"```Confirmation Recorded: {uuidGen}. {confirmations} of 4.```")
        #                 if (confirmations > 2):
        #                     sqlCon.execute("update matches set confirmed = 1 where matchID = ?;", (uuidGen,))
        #             else:
        #                 await ctx.send(f"Provided instance not found. It may have already been rejected.")
        #         else:
        #             await ctx.send("```Please enter a valid input```")
        #     except Exception as e:
        #         await ctx.send("```There was an error with your request.```")
        #     sqlCon.commit()




        # # ============== REJECT/UNLOCK ================#
        # # when message is rejected, it will allow new requests to come in
        @bot.command(name='reject', help='!rank reject <uuid>: Rejects a given instance.')
        async def reject(ctx, uuidGen):
            try:
                if (await is_valid_uuid(uuidGen)):
                    username = ctx.message.author.id
                    result = ""
                    results = sqlCon.execute("SELECT * from matches where matchID = ?;", (uuidGen,))
                    for id in results:
                        result = id
                    if (username in result):
                        sqlCon.execute("delete from matches where matchID = ?;", (uuidGen,))
                        await ctx.send(f"```Rejected match id: {uuidGen}```")
                    else:
                        await ctx.send(f"Provided instance not found or you were not in that match.")
                else:
                    await ctx.send("```Please enter a valid input```")
            except:
                await ctx.send("```There was an error with your request.```")
            sqlCon.commit()

        # # ============== VIEW PLAYER ================#
        # select count() from tks where confirmed is true;
        @bot.command(name='viewplayer', help='!rank viewplayer <player>: Shows a single player\'s stats.')
        async def viewSingle(ctx, player):
            try:
                if re.match('^[0-9]', player): # input validate user input
                    data = sqlCon.execute("select * from users where discordID = ?;", (player,))
                    for d in data:
                        await ctx.send(f"```Player: {await idToName(d[0])} Spy-Ext: {d[1]} Spy-Neu: {d[2]} Spy-Sab: {d[3]} Merc-Ext: {d[4]} Merc-Neu: {d[5]} Merc-Ext: {d[6]} TotalPoints: {d[7]} Wins: {d[8]} Losses: {d[9]}```")
                    # else:
                    #     await ctx.send(f"```I didn't find {offendingPlayer} in the database. Tell them to register or check your spelling!```")
                else:
                    await ctx.send("```Please enter a valid input```")
            except:
                await ctx.send("```There was an error with your request.```")
            sqlCon.commit()

        # # ============== VIEW TOP 10 ================#
        @bot.command(name='top', help='!rank top: Shows the Top 10 players in the database.')
        async def top(ctx):
            try:
                results = []
                data = sqlCon.execute("select * from users order by totalPoints desc limit 10;")
                for d in data:
                    results.append(f"Player: {await idToName(d[0])} Spy-Ext: {d[1]} Spy-Neu: {d[2]} Spy-Sab: {d[3]} Merc-Ext: {d[4]} Merc-Neu: {d[5]} Merc-Ext: {d[6]} TotalPoints: {d[7]} Wins: {d[8]} Losses: {d[9]}")
                print(results)
                formattedMembers = "\n".join(results)
                if formattedMembers:
                    await ctx.send(f"```{formattedMembers}```")
                else:
                    await ctx.send(f"```Error```")
            except Exception as e:
                #await ctx.send(e)
                await ctx.send("```There was an error with your request or there were no results.```")
            sqlCon.commit()

        # confirm the matches every x mins and update ranks
        @tasks.loop(seconds=120)
        async def confirmTimer():
            try:
                results = []
                data = sqlCon.execute("select * from matches where confirmed = 0;")
                for d in data:
                    results.append(d)

                for match in results:
                    players = []
                    uuid = match[0]
                    # spyOne = players.append(jsonpickle.decode(match[1]))
                    # spyTwo = players.append(jsonpickle.decode(match[2]))
                    # mercOne = players.append(jsonpickle.decode(match[3]))
                    # mercTwo = players.append(jsonpickle.decode(match[4]))
                    players.append(Spy(match[1])) # discord ids #spyOne
                    players.append(Spy(match[2])) #spyTwo
                    players.append(Merc(match[3])) #mercOne
                    players.append(Merc(match[4])) #mercTwo
                    gameMode = match[5]
                    winner = match[6]
                    confirmed = match[7]

                    await scorecard(players, gameMode, winner)
                    sqlCon.execute("update matches set confirmed = 1 where matchID = ?;", (uuid,))
                    sqlCon.commit()



            except Exception as e:
                print(e)
    except Exception as e:
        print(e)

    confirmTimer.start()
    sqlCon.commit()
    bot.run(TOKEN) #start the bot
