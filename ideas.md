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

* Slash commands <----- GIVEN UP ON THIS 
How do they work i want to implement them for all commands? 
Opting in for fishing game with an "enable" in the channel to be able to see the game messages and also automaticly give you a profile?

* The Logger
Self made logger system, works like i want it to for now, i would like to be able to get some sort of statistics out of it
Like maybe create a folder for each server instead and then have a log file for each person speaking.

* Statistics
Perhaps a independant system for all statistics, like fishing , mons , user chatting etc.
There shouldt be a reason for it to be dependant on its supporting system it should just read and write stats
and send them in text form to chat.

* Bring over from 1.0
The only thing worth keeping imo is Fishing and Pokemons the rest seems like a waste of time.
maaaaaybe the link scraping? might need a doover , but i do enjoy when he posts random images or gifs.

* Reddit talking
Improvements to be done in the future to filtering, but for now i think i just carry it over.
The dream is to have the bot run on a machine with a graphics card with cuda cores so it can do language models 
instead like Falcon 7b with tensorflow. (https://huggingface.co/tiiuae/falcon-7b-instruct)

* debug
Debugging system expanded, i want to be able to run the bot and have it have as little impact on things as possible
on the side, like adding "if debugging do not write stuff just test no finalizing" and just print the thing instead
of acctually doing it

* Fishing 2.0
Obviously make it better and more logical code wise.
- Base money value of sold fish on weight base value +/-
- Add new fish?
- Query fishname to get WR , money value for a medium?
- Redesign fish with rareity in mind , seasonal? super rare? colorcoded 
- Classes stay the same but color code rarities in each class white->yellow->blue->purple ?