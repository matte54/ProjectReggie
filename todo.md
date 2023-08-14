###########################################################################################
Bugs/Problems and or Features , already implemented but needs additional work or fixing
Remove item when finished
###########################################################################################
* Main
- Make the on_reaction take the user var into account and use statistics to consider users fav emojis

* Reflex task
- Implement URL
- Implement Recommendation?
- Add holiday command for reflex?
- implement a chance to just reply with something someone said from the log (needs a emoji check for guild compatibility)
- also needs a chance to just post an emoji (seems more human)

* Status task
- Custom activity seems dosent work
- Look into twitch API for streaming check?
- More data for variaty

* Speaking system
- Needs re-evaluation on all
- Build into a class

* Logger system
- Integrate into user statistics
- The filter needs re-evaluation to include emoji but reduce spam anyway

* Housekeeper system
- Log rotation -> logger

* Emojihandler system

* Help command
- Write help message explaining woodhouse usage.

* Remindme command
- Write remind me task to check the database and post (not started)

* Statistics
- Find a way to limit writes, need to figure out how to have it collect data for each dictionary it needs and write
only like in 5-10 minute intervals, couldnt figure out how to approach it cause of the diffrent types that will be open
simultanously when people are chatting. also diffrent servers.
