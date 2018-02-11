## Bear Markdown and textbundle import – with tags from file and folder.

***bear_import.py***  
*Version 1.0.0 - 2018-02-10 at 17:37 EST*

*See also:* **[bear_export_sync.py](https://github.com/rovest/Bear-Markdown-Export/blob/master/README.md)** *for export with sync-back.*


### Features 

* Imports markdown or textbundles from nested folders under a `BearImport/input/' folder
* Foldernames are converted to Bear tags
* Also imports MacOS file tags as Bear tags
* Imported notes are also tagged with `#.imported/yyyy-MM-dd` for convenience.
* Import-files are then cleared to a `BearImport/done/' folder
* Use for email input to Bear with Zapier's "Gmail to Dropbox" zap.
* Or for import of nested groups and sheets from Ulysses, images and keywords included.


### Trigger script with Automator Folder Action

1. New Automator file as `Folder Action` 
2. Set `Folder action receives files and folders added to`: `{user}/Dropbox/BearImport/Input`
3. Add action: `Run Shell Script` choose `bin/bash`
4. Insert one line with full paths to python and script (Use "" if spaces in paths!):  
`/Library/Frameworks/Python.framework/Versions/3.6/bin/python3.6 "/Users/username/scripts/bear_import.py"`
5. Save as `Bear Import` or whatever you choose.

Or skip all this and run it manually :)


### Get mail to Bear with "Zapier Gmail to Dropbox" action

1. Create a free zapier.com account.
2. Use a gmail account of choice and setup a filter for incoming mail if needed. 
3. Make new Zap. See: [Add new Gmail emails to Dropbox as text files](https://zapier.com/apps/dropbox/integrations/gmail/10323/add-new-gmail-emails-to-dropbox-as-text-files)
4. Set zap Dropbox output to `{user}/Dropbox/BearImport/Input` 


### Import from Ulysses’ external folders on Mac

1. Add `{user}/Dropbox/BearImport/Input` as external folder
2. Edit folder settings to `.textbundle` and `Inline Links`!
3. Drag any library group to this folder in Ulysses' sidebar.
4. Voilà – Imports to Bear with images and tags (both from group names and keywords).


