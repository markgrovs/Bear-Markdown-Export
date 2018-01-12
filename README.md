## Markdown export and sync of Bear notes
_v.0.07: 2018-01-12 at 12:21 EST_

Python script for export and roundtrip sync of Bear's notes to OneDrive, Dropbox, or any other sync service.
* All Bear notes are exported as plain Markdown (text only in this version, so no media or file attachments are exported)
* Edit your Bear notes online in browser on [OneDrive.com](https://onedrive.live.com). It has a nice editor for plain markdown.
* Or read and edit your Bear notes on Windows or Android with any markdown editor of choice.   
* Remote updates or new notes are synced back into Bear with this script (original image links will still work on return).

Run it manually or add it to a cron job for automatic syncing (every 5 – 15 minutes, or whatever you prefer).

This is a concept/beta version, and please feel free to improve or modify as needed. 

### Sync external note edits back into Bear
Checks for external edits in Markdown files (previously exported from Bear):
* Adds updated or new Notes to Bear with x-callback-url command
* Marks updated note with message and link to original note.
* Moves original note to trash (unless a sync conflict)
* Copies changed files to a "Sync Inbox" as a backup. 

### Markdown export to Dropbox, OneDrive, or other:
Exports all notes from Bear's database.sqlite as plain markdown files:
* Checks modified timestamp on database.sqlite, so exports only when needed.
* Sets Bear note's modification date on exported markdown files.
* Appends Bear note's creation date to filename to avoid “title-filename-collisions”
* Uses rsync for copying, so only changed notes need to be synced to Dropbox (or other sync services)
* "Hides” tags from being displayed as H1 in other markdown apps by adding a period in front of all tags:   
.#bear .#idea .#python   
(these are striped off again when synced back into Bear)

Happy syncing! ;)