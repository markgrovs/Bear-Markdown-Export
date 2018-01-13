## Markdown export and sync of Bear notes
_v.0.10: 2018-01-13 at 17:51 EST_

Python script for export and roundtrip sync of Bear's notes to OneDrive, Dropbox, etc. Edit online with any browser on [OneDrive](http://OneDrive.com), which has a nice online editor, or use a markdown editor on Windows or Android. Remote edits and new notes get synced back into Bear with this script.

It's a concept/beta version, so please feel free to improve or modify as needed. 

* All Bear notes are exported as plain Markdown  
	(Text only in this version, so no media or file attachments are exported.  
	But original image links will still work and display images on return to Bear)
* Edit your Bear notes online in browser on [OneDrive.com](https://onedrive.live.com). It has a nice editor for plain text/markdown.
* Read and edit your Bear notes on Windows or Android with any markdown editor of choice.   
* Remote edits or new notes will be synced back into Bear again.

Run it manually or add it to a cron job for automatic syncing (every 5 – 15 minutes, or whatever you prefer).


### Syncs external edits back into Bear
Checks for external edits in Markdown files (previously exported from Bear):

* Adds edited or new notes to Bear with x-callback-url command (if modified > export timestamp)
* Marks edited note with message and link to original note.
* Moves original note to trash (unless a sync conflict)
* Copies changed files to a "Sync Inbox" as a backup. 


### Markdown export to Dropbox, OneDrive, or other:
Exports all notes from Bear's database.sqlite as plain markdown files:

* Checks modified timestamp on database.sqlite, so exports only when needed.
* Sets Bear note's modification date on exported markdown files.
* Appends Bear note's creation date to filename to avoid “title-filename-collisions”
* Note IDs are included at bottom of markdown files to match original note on sync back:  
	{BearID:730A5BD2-0245-4EF7-BE16-A5217468DF0E-33519-0000429ADFD9221A}  
(these ID's are striped off again when synced back into Bear)
* Uses rsync for copying, so only changed notes need to be synced to Dropbox (or other sync services)
* "Hides” tags from being displayed as H1 in other markdown apps by adding a period in front of all tags:   
.#bear .#idea .#python   
(these are striped off again when synced back into Bear)

You may have Bear on a Mac or iPad and want your notes on your Android phone. Or you have Bear on iPhone or iPad and want your notes on your Windows or Linux PC. Or you want to have them available online in a browser from any desktop computer. Here is a solution (or call it workaround) for now, until Bear comes with an online, Windows, or Android solution ;)

Happy syncing! ;)