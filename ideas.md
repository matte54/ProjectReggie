Project Reggie a.k.a Woodhouse 2.0

* Layout plans
DATA folder only holds constant data (subdirs for diffrent systems)
LOCAL is for user data that gets written to and or changed often (subdirs)
SYSTEMS holds sepereate function files
main only holds the main loop
mother reads systems and controls everything so if something isent called in mother it has no meaning.

* Slash commands <----- GIVEN UP ON THIS 
How do they work i want to implement them for all commands? 
Opting in for fishing game with an "enable" in the channel to be able to see the game messages and also automaticly give you a profile?

* The Logger
Self made logger system, works like i want it to for now, i would like to be able to get some sort of statistics out of it
Like maybe create a folder for each server instead and then have a log file for each person speaking.
Then write a statistic system that can keep track of fun stuff like favourite emoji etc?

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