## Markdown export and sync of Bear notes
_v.0.11: 2018-01-13 at 20:59 EST_

Python script for export and roundtrip sync of Bear's notes to OneDrive, Dropbox, etc. Edit or share online in any browser: [OneDrive](http://OneDrive.com) has a nice online plain text editor and Dropbox has a nice markdown preview, and allows for comments on your shared notes.

You can also use a markdown editor on Windows or Android with Dropbox or OneDrive. Remote edits and new notes get synced back into Bear with this script.

Another option is using nvAlt.app as sync engine to Simplenote. Simplenote has online edit, publish, and share with collaboration. Simplenote also has client apps for Android, Windows, Linux. You will not get images synced over, but text and sync back to Bear will still work, and original images from Bear will still work on edited notes when returned to Bear. In this version, only one way export to Simplenote/nvAlt folder is implemented.

This is a concept/beta version, and please feel free to improve or modify as needed. 

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

You have Bear on Mac but also want your notes on your Android phone, on Linux or Windows machine at your office. Or you want them available online in a browser from any desktop computer. Here is a solution (or call it workaround) for now, until Bear comes with an online, Windows, or Android solution ;)

Happy syncing! ;)