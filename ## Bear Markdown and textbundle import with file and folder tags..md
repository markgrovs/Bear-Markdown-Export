## Bear Markdown and textbundle import with file and folder tags.

***bear_import.py***  
*Version 1.0.0 - 2018-02-10 at 17:37 EST*

**See: **bear_export_sync.py** for export and sync-back.

### NEW import function: 
* Imports markdown or textbundles from nested folders under a `BearImport/input/' folder
* Foldernames are converted to Bear tags
* Also imports MacOS file tags as Bear tags
* Imported notes are also tagged with `#.imported/yyyy-MM-dd` for convenience.
* Import-files are then cleared to a `BearImport/done/' folder
* Use for email input to Bear with Zapier's "Gmail to Dropbox" zap.
* Or for import of nested groups and sheets from Ulysses, images and keywords included.
