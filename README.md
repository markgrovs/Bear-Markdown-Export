## Markdown export and sync of Bear notes
_github/rovest, rorves@twitter: 2018-01-10 at 22:57 EST_

### Syncing updates from Dropbox, OneDrive, or other:
First checks for external changes in Markdown files (previously exported from Bear)
* Adding updated or new Notes to Bear with x-callback-url command
* Marking updated note with message and link to original note.
* Moving original note to trash (unless a sync conflict)
* Moving changed files to a "Sync Inbox" as a backup. 

### Markdown export to Dropbox, OneDrive, or other:
Then exports Markdown from Bear sqlite db.
* Uses rsync for copying, so only markdown files of changed sheets will be updated and synced by Dropbox (or other sync services)
* Keeps original modification date on export file
* Uses rsync to only update changed files in Dropbox or OneDrive folders
* Appends creation date to filename to avoid “title-filename-collisions”