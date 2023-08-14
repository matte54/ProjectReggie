Project Reggie a.k.a Woodhouse 2.0

- Matte's ideas / plans -

* Layout plans
DATA folder only holds constant data (subdirs for diffrent systems)
LOCAL is for user data that gets written to and or changed often (subdirs)
SYSTEMS holds sepereate function files
main only holds the main loop
mother reads systems and controls everything so if something isent called in mother it has no meaning.

* Modular
The goal is to build stuff as modular as possible, in most cases i want to be able to remove a system from the core
by commenting out one line, ideally.
No more back n forth between systems like 1.0.

* House Keeper
Build a system that runs once on start up that takes care of all seperate systems housekeeping tasks.
Like removing time files, rotating logs.
Also keeping a database of UserIDs and there global names, and maybe also serverIDs for future multiserver support?
Obviously important that this system runs indenpedent of the systmes it supports, there should never be any returns

* The Logger
- Self made logger system, works like i want it to for now, i would like to be able to get some sort of statistics out of it
like maybe create a folder for each server instead and then have a log file for each person speaking.
- Messed around with a library called "yake" that can extract keywords from strings, might be able to implement 
something with with the system i was dreaming of at the start. Use the logging for each user to extract keywords
so woodhouse basically "learns" what users often talk about, and use urls/gifs/speak accordingly

* Statistics
Perhaps a independant system for all statistics, like fishing , mons , user chatting etc.
There shouldt be a reason for it to be dependant on its supporting system it should just read and write stats
and send them in text form to chat.
- Use the plotly library to visualize statistics, it has tools to convert charts to images that can be posted and embedded
- User seperate statistic json files, put every sentence thru yake (performance?) keywords : value(times)
emoji value times, other stuff?


* Bring over from 1.0
The only thing worth keeping imo is Fishing and Pokemons the rest seems like a waste of time.
maaaaaybe the link scraping? might need a doover , but i do enjoy when he posts random images or gifs.
- Quiz game shouldnt be to hard to just implement straight over, but might need to rework some stuff.
It would be a shame to leave it even if its not very used, i worked hard on it lol

* Reddit talking
Improvements to be done in the future to filtering, but for now i think i just carry it over.

* Debug
Debugging system expanded, i want to be able to run the bot and have it have as little impact on things as possible
on the side, like adding "if debugging do not write stuff just test no finalizing" and just print the thing instead
of acctually doing it

* Fishing 2.0
Obviously make it better and more logical code wise.
- Base money value of sold fish on weight base value +/-
- Add new fish? double it atleast
- Query fishname to get WR , money value for a medium?
- Redesign fish with rareity in mind , seasonal? super rare? colorcoded 
- Classes stay the same but color code rarities in each class white->yellow->blue->purple ? colors seems hard to
implement pass for now
- No time limit on fishing, but implement the fail chance into the time between your casts, and if you havent casted in 
a long time(up to a certain point) you will have a higher chance of rarity and or class?
For example if you cast 1 minute after you last cast you might get a fail chance of 80% , but if you wait 1 hour you
have the default fail chance, but if you wait 6 hours your might have a 1% fail chance + to have your class roll go up
1-3 steps and rarity?
- WR system should include a timestamp and if it was a shiny *see query system?
- Re-evaluate the old idea of enhancment gear, since buying a new cast now dosent rly make sense so we need something
to spend money on, maybe buy a lure to give everyone a + something to catch for x time, and other temporary fishing gear?
Shiny food for extra shiny chance? , better lure for reduced fail chance?, chance to get unique fish?
- Unique fishes, added a unique bool in the fish database, add fish that are unique , so very low chance to catch,
unique fishes can only be caught once per season? , extra money? special unique leaderboard?
- failflares into file (add more) also add 25% chance failflares that includes the lost fish for extra salt.
- Redesign schools system to be more global and permanent? maybe have something like if sevral class x is caught within
a time frame, increase the chance of class x being caught again (simulating a school being present)
- Include message that you have taken the lead in a competition if u catch a bigger fish
- Use the NAMEDFLARE for when you have a unique and loose it (easy way to roll for it early)

* Remind me
Remind me system is possible ? could be fun
command to add reminders to a json file
a background task to somehow rotate thru and post if reminder hits thonk

* Catching disconnection exceptions
Been looking a lil bit to somehow catch disconnect exceptions, like if discord servers goes down or if i loose internet
right now the program just sits there and spams exceptions endlessly.
Ideally we would want to catch this somehow and just put in a wait timer to retry later.

* Emoji system
- Have woodhouse keep track of emojis that get used to most and have those to be higher chance of usage from
him(this will have to be part of a statistics system)

* Pokemon 2.0
- Shinys
- Make already had pokemons non-catchable(leaving the mon for others) maybe if u $catch a mon and u already have it
say you already have it and list users with a dex that needs it
- Fix mon pictures with white backgrounds, OR if we limit to newer pokemons editions only we can probably scrape up
some better pictures to include in an embed in the goal of making them more into cards.
- Maybe categorize the mons like the trading cards do, with basic/stage1-2 for evolves and also common, uncommon and rare?
And accordingly give mons less/more chances? might be alot of work to build that database into a json file since there
are so many mons.. but would definitly make it more intresting.
- Designing a embed to try to mimic a pokemon card for each mon that appears not just picture
- Pokemon delay, feed a pokemon candy to make it appear again later, if you delay a pokemon and someone catches it
reward delayer with a random free pokemon not in his dex

* New game idea "Random DND" dungeonmaster light?
- Random DND monster can appear in the chat, anyone who wants to can roll for attacking
- anyone who participates gets a dnd profile and gathers money/xp/loot 
- If u attack the monster you are available to be attacked at that point.
- players can pick class/race after that?
- no healing allowed, if u get attacked you always take damage cause rolling saves isent rly feasable
- player death removes the profile and players need to make a new char next monster
- ???