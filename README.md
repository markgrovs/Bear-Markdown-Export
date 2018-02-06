## Markdown export and sync of Bear notes
_v.1.3.0: 2018-02-05 at 18:05 EST_

Python script for export and roundtrip sync of Bear's notes to OneDrive, Dropbox, etc. Edit or share online in any browser: [OneDrive](http://OneDrive.com) has a nice online plain text editor and Dropbox has a nice markdown preview, and allows for comments on your shared notes.

You can also use a markdown editor on Windows or Android with Dropbox or OneDrive. Remote edits and new notes get synced back into Bear with this script.

This is a concept/beta version, and please feel free to improve or modify as needed. But please be careful! both `rsync` and `shutil.rmtree` are powerful commands that can wipe clean a whole folder tree or even your complete HD if used incorrectly!

*See also: [Bear Power Pack](https://github.com/rovest/Bear-Power-Pack/blob/master/README.md)*

## Features

* Bear notes exported as plain Markdown or Textbundles with images.
* Syncs external edits back to Bear with original image links intact. New external notes are added.
* **NEW:** Can now make nested folders from tags   
(export to folder for first tag only, or all tags.)
* **NEW:** Can restrict export to a list of specific tags
* **NEW:** export as `.md` with links to common image repository or as `.textbundles` with images included. 

Edit your Bear notes online in browser on [OneDrive.com](https://onedrive.live.com). It has a ok editor for plain text/markdown. Or with [StackEdit](https://stackedit.io/app), an amazing online markdown editor that can sync with *Dropbox* or *Google Drive*

Read and edit your Bear notes on *Windows* or *Android* with any markdown editor of choice. Remote edits or new notes will be synced back into Bear again. *Typora* works great on Windows, and displays images of text bundles as well.

Run script manually or add it to a cron job for automatic syncing (every 5 – 15 minutes, or whatever you prefer).  
([LaunchD Task Scheduler](https://itunes.apple.com/us/app/launchd-task-scheduler/id620249105?mt=12) Is easy to configure and works very well for this) 


### Syncs external edits back into Bear
Checks for external edits in Markdown files (previously exported from Bear):

* Replacing text in original note with `bear://x-callback-url/add-text?mode=replace` command   
(That way keeping original note ID and creation date)  
If any changes to title, new title will be added just below original title.  
(`mode=replace` does not replace title)
* Original note is backed up as markdown-file to BearSyncBackup folder  
* If a sync conflict, both original and new version will be in Bear (the new one with a sync conflict message and link to original).
* New notes created online, are just added to Bear  
(with the `bear://x-callback-url/create` command)


### Markdown export to Dropbox, OneDrive, or other:
Exports all notes from Bear's database.sqlite as plain markdown files:

* Checks modified timestamp on database.sqlite, so exports only when needed.
* Sets Bear note's modification date on exported markdown files.
* Appends Bear note's creation date to filename to avoid “title-filename-collisions”
* Note IDs are included at bottom of markdown files to match original note on sync back:  
	{BearID:730A5BD2-0245-4EF7-BE16-A5217468DF0E-33519-0000429ADFD9221A}  
(these ID's are striped off again when synced back into Bear)
* Uses rsync for copying (from a temp folder), so only changed notes will be synced to Dropbox (or other sync services)
* rsync also takes care of deleting trashed notes
* "Hides” tags from being displayed as H1 in other markdown apps by adding `period+space` in front of first tag on a line:   
`. #bear #idea #python`   
(these are striped off again when synced back into Bear)
* Makes subfolders named with first tag in note if `make_tag_folders = True`
* Files can now be copied to multiple tag-folders if `multi_tags = True`
* Export can now be restricted to a list of spesific tags: `limit_export_to_tags = ['bear/github', 'writings']`  
or leave list empty for all notes: `limit_export_to_tags = []`
* Can export and link to images in common image repository
* Or export as textbundles with images included 


You have Bear on Mac but also want your notes on your Android phone, on Linux or Windows machine at your office. Or you want them available online in a browser from any desktop computer. Here is a solution (or call it workaround) for now, until Bear comes with an online, Windows, or Android solution ;)

Happy syncing! ;)
