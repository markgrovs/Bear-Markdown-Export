# encoding=utf-8
# python3.6
# bear_export_sync.py

'''
# Markdown export from Bear sqlite database 
Version 1.3.3, 2018-02-06 at 13:36 EST
github/rovest, rorves@twitter

## Syncing external updates:

First checking for Changes in Markdown files (previously exported from Bear)
* Replacing text in original note with callback-url replace command   
  (Keeping original creation date)
  If Changes in title it will be added just below original title
* New notes are added to Bear (with x-callback-url command)
* Backing up original note as file to BearSyncBackup folder  
  (unless a sync conflict, then both notes will be there)
* 

Then exporting Markdown from Bear sqlite db.
* check_if_modified() on database.sqlite to see if export is needed
* Uses rsync for copying, so only markdown files of changed sheets will be updated  
  and synced by Dropbox (or other sync services)
* "Hide" tags with period: ".#tag" from being seen as H1 in other Markdown apps.   
  (This is removed if sync-back above)
* Makes subfolders named with first tag in note if `make_tag_folders = True`
* Files can now be copied to multiple tag-folders if `multi_tags = True`
* Export can now be restricted to a list of spesific tags: `limit_export_to_tags = ['bear/github', 'writings']`  
or leave list empty for all notes: `limit_export_to_tags = []`
* Can export and link to images in common image repository
* Or export as textbundles with images included 
'''

make_tag_folders = True # Exports to folders using first tag only, if `multi_tag_folders = False`
multi_tag_folders = True # Copies notes to all 'tag-paths' found in note!

# The following two lists are more or less mutually exclusive, so use only one of them.
# (You can use both if you have some nested tags where that makes sense)
# Also, they only work if `make_tag_folders = True`.
only_export_these_tags = [] # Leave this list empty for all notes! See below for sample
# only_export_these_tags = ['bear/github', 'writings'] 
no_export_tags = [] # If a tag in note matches one in this list, it will not be exported.
# no_export_tags = ['private', '.inbox', 'love letters', 'banking'] 

# Set only one of the folowing to True 
    # (if `export_as_textbundles = True`, `export_image_repository` is ignored)
export_image_repository = False  # Exports as md but link images to image repository exported to: `assets_path` 
export_as_textbundles = True  # Exports as Textbundles with images included

my_sync_folder = 'Dropbox'  # Change 'Dropbox' to 'Box', 'Onedrive',
    # or whatever folder of sync service you need.

# NOTE! Your user 'HOME' path and '/Bear Notes' is added below!
# NOTE! So do not change anything below here!!!

import sqlite3
import datetime
import re
import subprocess
import urllib.parse
import os
import time
import shutil
import fnmatch

HOME = os.getenv('HOME', '')

# NOTE! if 'Bear Notes' is left blank, all other files in my_sync_folder will be deleted!! 
export_path = os.path.join(HOME, my_sync_folder, 'Bear Notes')
# NOTE! "export_path" is used for sync-back to Bear, so don't change this variable name!
multi_export = [(export_path, True)] # only one folder output here. 
# Use if you want export to severa places like: Dropbox and OneDrive, etc. See below

# Sample for multi folder export:
# export_path_aux1 = os.path.join(HOME, 'OneDrive', 'Bear Notes')
# export_path_aux2 = os.path.join(HOME, 'Box', 'Bear Notes')

# NOTE! All files in export path not in Bear will be deleted if delete flag is "True"!
# Set this flag fo False only for folders to keep old deleted versions of notes
# multi_export = [(export_path, True), (export_path_aux1, False), (export_path_aux2, True)]

sync_backup = os.path.join(HOME, my_sync_folder, 'BearSyncBackup') # Backup of original note before sync to Bear.
temp_path = os.path.join(HOME, 'Temp', 'BearExportTemp')  # NOTE! Do not change the "BearExportTemp" folder name!!!
bear_db = os.path.join(HOME, 'Library/Containers/net.shinyfrog.bear/Data/Documents/Application Data/database.sqlite')

# Paths used in image exports:
bear_image_path = os.path.join(HOME,
    'Library/Containers/net.shinyfrog.bear/Data/Documents/Application Data/Local Files/Note Images')
assets_path = os.path.join(HOME, export_path, 'BearImages')

sync_ts = ".sync-time.log"
export_ts = ".export-time.log"

sync_ts_file = os.path.join(export_path, sync_ts)
sync_ts_file_temp = os.path.join(temp_path, sync_ts)
export_ts_file_exp = os.path.join(export_path, export_ts)
export_ts_file = os.path.join(temp_path, export_ts)


def main():
    sync_md_updates()
    if check_db_modified():
        delete_old_temp_files()
        note_count = export_markdown()
        write_time_stamp()
        rsync_files_from_temp()
        if export_image_repository and not export_as_textbundles:
            copy_bear_images()
        # notify('Export completed')
        print(note_count, 'notes exported to:')
        print(export_path)
    else:
        print('No notes needed export')


def check_db_modified():
    if not os.path.exists(sync_ts_file):
        return True
    db_ts = get_file_date(bear_db)
    last_export_ts = get_file_date(export_ts_file_exp)
    return db_ts > last_export_ts


def export_markdown():
    conn = sqlite3.connect(bear_db)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0'"
    c = conn.execute(query)
    note_count = 0
    for row in c:
        title = row['ZTITLE']
        md_text = row['ZTEXT'].rstrip()
        creation_date = row['ZCREATIONDATE']
        modified = row['ZMODIFICATIONDATE']
        uuid = row['ZUNIQUEIDENTIFIER']
        filename = clean_title(title) + date_time_conv(creation_date)
        file_list = []
        if make_tag_folders:
            file_list = sub_path_from_tag(temp_path, filename, md_text)
        else:
            file_list.append(os.path.join(temp_path, filename))
        if file_list:
            mod_dt = dt_conv(modified)
            md_text = hide_tags(md_text)
            md_text += '\n\n<!-- {BearID:' + uuid + '} -->\n'
            for filepath in file_list:
                note_count += 1
                # print(filepath)
                if export_as_textbundles:
                    make_text_bundle(md_text, filepath, mod_dt)
                elif export_image_repository:
                    md_proc_text = process_image_links(md_text, filepath)
                    write_file(filepath + '.md', md_proc_text, mod_dt)
                else:
                    write_file(filepath + '.md', md_text, mod_dt)
    conn.close()
    return note_count


def make_text_bundle(md_text, filepath, mod_dt):
    '''
    Exports as Textbundles with images included 
    '''
    filepath += '.textbundle'
    assets = os.path.join(filepath, 'assets')    
    if not os.path.exists(filepath):
        os.makedirs(filepath)
        os.makedirs(assets)
        
    info = '''{
    "transient" : true,
    "type" : "net.daringfireball.markdown",
    "creatorIdentifier" : "net.shinyfrog.bear",
    "version" : 2
    }'''
    matches = re.findall(r'\[image:(.+?)\]', md_text)
    for match in matches:
        image_name = match
        new_name = image_name.replace('/', '_')
        source = os.path.join(bear_image_path, image_name)
        target = os.path.join(bear_image_path, assets, new_name)
        shutil.copy2(source, target)

    md_text = re.sub(r'\[image:(.+?)/(.+?)\]', r'![](assets/\1_\2)', md_text)
    write_file(filepath + '/text.md', md_text, mod_dt)
    write_file(filepath + '/info.json', info, mod_dt)
    os.utime(filepath, (-1, mod_dt))


def sub_path_from_tag(temp_path, filename, md_text):
    # Get tags in note:
    pattern1 = r'(?<!\S)\#([.\w\/\-]+)[ \n]?(?!([\/ \w]+\w[#]))'
    pattern2 = r'(?<![\S])\#([.\w\/ ]+?)\#[ \n]'
    if multi_tag_folders:
        # Files copied to all tag-folders found in note
        tags = []
        for matches in re.findall(pattern1, md_text):
            tag = matches[0]
            tags.append(tag)
        for matches2 in re.findall(pattern2, md_text):
            tag2 = matches2
            tags.append(tag2)
        if len(tags) == 0:
            # No tags found, copy to root level only
            return [os.path.join(temp_path, filename)]
    else:
        # Only folder for first tag
        match1 =  re.search(pattern1, md_text)
        match2 =  re.search(pattern2, md_text)
        if match1 and match2:
            if match1.start(1) < match2.start(1):
                tag = match1.group(1)
            else:
                tag = match2.group(1)
        elif match1:
            tag = match1.group(1)
        elif match2:
            tag = match2.group(1)
        else:
            # No tags found, copy to root level only
            return [os.path.join(temp_path, filename)]
        tags = [tag]
    paths = []
    for tag in tags:
        if tag == '/':
            continue
        if only_export_these_tags:
            export = False
            for export_tag in only_export_these_tags:
                if tag.lower().startswith(export_tag.lower()):
                    export = True
                    break
            if not export:
                continue
        for no_tag in no_export_tags:
            if tag.lower().startswith(no_tag.lower()):
                return []
        sub_path = tag.replace('.', '_')    
        tag_path = os.path.join(temp_path, sub_path)
        if not os.path.exists(tag_path):
            os.makedirs(tag_path)
        paths.append(os.path.join(tag_path, filename))      
    return paths


def process_image_links(md_text, filepath):
    '''
    Bear image links converted to MD links
    '''
    root = filepath.replace(temp_path, '')
    level = len(root.split('/')) - 2
    parent = '../' * level
    md_text = re.sub(r'\[image:(.+?)\]', r'![](' + parent + r'BearImages/\1)', md_text)
    return md_text


def restore_image_links(md_text):
    '''
    MD image links restored back to Bear links
    '''
    if export_as_textbundles:
        md_text = re.sub(r'!\[\]\(assets/(.+?)_(.+?)\)', r'[image:\1/\2]', md_text)
    elif export_image_repository :
        # md_text = re.sub(r'\[image:(.+?)\]', r'![](../assets/\1)', md_text)
        md_text = re.sub(r'!\[\]\((\.\./)*BearImages/(.+?)\)', r'[image:\2]', md_text)
    return md_text


def copy_bear_images():
    # Image files copied to a common image repository
    subprocess.call(['rsync', '-r', '-t', '--delete', 
                    bear_image_path + "/", assets_path])


def write_time_stamp():
    # write to time-stamp.txt file (used during sync)
    write_file(export_ts_file, "Markdown from Bear written at: " +
               datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), 0)
    write_file(sync_ts_file_temp, "Markdown from Bear written at: " +
               datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), 0)


def hide_tags(md_text):
    # Hide tags from being seen as H1, by placing `period+space` at start of line:
    md_text =  re.sub(r'(\n)[ \t]*(\#[\w.]+)', r'\1. \2', md_text)
    return md_text


def restore_tags(md_text):
    # Tags back to normal Bear tags, stripping the `period+space` at start of line:
    md_text =  re.sub(r'(\n)\.[ \t]*(\#[\w]+)', r'\1\2', md_text)
    return md_text


def clean_title(title):
    title = title[:56].strip()
    if title == "":
        title = "Untitled"
    title = re.sub(r'[/\\*?$@!^&\|~:]', r'-', title)
    title = re.sub(r'-$', r'', title)    
    return title.strip()


def write_file(filename, file_content, modified):
    f = open(filename, "w", encoding='utf-8')
    f.write(file_content)
    f.close()
    if modified > 0:
        os.utime(filename, (-1, modified))


def read_file(file_name):
    f = open(file_name, "r", encoding='utf-8')
    file_content = f.read()
    f.close()
    return file_content


def get_file_date(filename):
    try:
        t = os.path.getmtime(filename)
        return t
    except:
        return 0


def dt_conv(dtnum):
    # Formula for date offset based on trial and error:
    hour = 3600 # seconds
    year = 365.25 * 24 * hour
    offset = year * 31 + hour * 6
    return dtnum + offset


def date_time_conv(dtnum):
    newnum = dt_conv(dtnum) 
    dtdate = datetime.datetime.fromtimestamp(newnum)
    #print(newnum, dtdate)
    return dtdate.strftime(' - %Y-%m-%d_%H%M')


def time_stamp_ts(ts):
    dtdate = datetime.datetime.fromtimestamp(ts)
    return dtdate.strftime('%Y-%m-%d at %H:%M') 


def date_conv(dtnum):
    dtdate = datetime.datetime.fromtimestamp(dtnum)
    return dtdate.strftime('%Y-%m-%d')


def delete_old_temp_files():
    # Deletes all files in temp folder before new export using "shutil.rmtree()":
    # NOTE! CAUTION! Do not change this function unless you really know shutil.rmtree() well!
    if os.path.exists(temp_path) and "BearExportTemp" in temp_path:
        # *** NOTE! Double checking that temp_path folder actually contains "BearExportTemp"
        # *** Because if temp_path is accidentally empty or root,
        # *** shutil.rmtree() will delete all files on your complete Hard Drive ;(
        shutil.rmtree(temp_path)
        # *** NOTE: USE rmtree() WITH EXTREME CAUTION!
    os.makedirs(temp_path)


def rsync_files_from_temp():
    # Moves markdown files to new folder using rsync:
    # This is a very important step! 
    # By first exporting all Bear notes to an emptied temp folder,
    # rsync will only update destination if modified or size have changed.
    # So only changed notes will be synced by Dropbox or OneDrive destinations.
    # Rsync will also delete notes on destination if deleted in Bear.
    # So doing it this way saves a lot of otherwise very complex programing.
    # Thank you very much, Rsync! ;)
    for (dest_path, delete) in multi_export:
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        if delete:
            subprocess.call(['rsync', '-r', '-t', '--delete',
                             '--exclude', 'BearImages/',
                             '--exclude', '.Ulysses*',
                             '--exclude', '*.Ulysses_Public_Filter',
                             temp_path + "/", dest_path])
        else:
            subprocess.call(['rsync', '-r', '-t',
                            temp_path + "/", dest_path])


def sync_md_updates():
    updates_found = False
    if not os.path.exists(sync_ts_file) or not os.path.exists(export_ts_file):
        return False
    ts_last_sync = os.path.getmtime(sync_ts_file)
    ts_last_export = os.path.getmtime(export_ts_file)
    # Update synced timestamp file:
    update_sync_time_file(0)
    file_types = ('*.md', '*.txt', '*.markdown')
    for root, dirnames, filenames in os.walk(export_path):
        '''
        This step walks down into all sub folders, if any.
        '''
        for pattern in file_types:
            for filename in fnmatch.filter(filenames, pattern):
                md_file = os.path.join(root, filename)
                ts = os.path.getmtime(md_file)
                if ts > ts_last_sync:
                    updates_found = True
                    md_text = read_file(md_file)
                    backup_ext_note(md_file)
                    if check_if_image_added(md_text, md_file):
                        textbundle_to_bear(md_text, md_file, ts)
                        print("*** Textbundle imported to Bear")
                    else:
                        update_bear_note(md_text, ts, ts_last_export)
                        print("*** Bear Note Updated")
    if updates_found:
        # Give Bear time to process updates:
        time.sleep(3)
        # Check again, just in case new updates synced from remote (OneDrive/Dropbox) 
        # during this process!
        # The logic is not 100% fool proof, but should be close to 99.99%
        sync_md_updates() # Recursive call
    return updates_found


def check_if_image_added(md_text, md_file):
    if not '.textbundle/' in md_file:
        return False
    matches = re.findall(r'!\[\]\(assets/(.+?)\)', md_text)
    for image_match in matches:
        'F89CDA3D-3FCC-4E92-88C1-CC4AF46FA733-10097-00002BBE9F7FF804_IMG_2280.JPG'
        if not re.match(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}-\w{5}-\w{16}_', image_match):
            return True
    return False        


def textbundle_to_bear(md_text, md_file, mod_dt):
    md_text = restore_tags(md_text)
    match = re.search(r'\{BearID:(.+?)\}', md_text)
    if match:
        uuid = match.group(1)
        # Remove old BearID: from new note
        md_text = re.sub(r'\<\!-- ?\{BearID\:' + uuid + r'\} ?--\>', '', md_text).rstrip() + '\n'
        md_text = insert_link_top_note(md_text, 'Images added! Link to original note:', uuid)
    write_file(md_file, md_text, mod_dt)
    bundle = os.path.split(md_file)[0]
    os.utime(bundle, (-1, mod_dt))
    subprocess.call(['open', '-a', '/applications/bear.app', bundle])
    time.sleep(0.5)


def backup_ext_note(md_file):
    if '.textbundle' in md_file:
        bundle_path = os.path.split(md_file)[0]
        bundle_name = os.path.split(bundle_path)[1]
        target = os.path.join(sync_backup, bundle_name)
        bundle_raw = os.path.splitext(target)[0]

        count = 2
        while os.path.exists(target):
            # Adding sequence number to identical filenames, preventing overwrite:
            bundle_raw = re.sub(r"(( - \d\d)?\.textbundle)", r"", target)
            target = bundle_raw + " - " + str(count).zfill(2) + ".textbundle"
            count += 1
        shutil.copytree(bundle_path, target)
    else:
        shutil.copy2(md_file, sync_backup + '/')


def update_sync_time_file(ts):
    write_file(sync_ts_file,
        "Checked for Markdown updates to sync at: " +
        datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S"), ts)


def update_bear_note(md_text, ts, ts_last_export):
    uuid = ''
    md_text = restore_tags(md_text)
    md_text = restore_image_links(md_text)    
    match = re.search(r'\{BearID:(.+?)\}', md_text)
    sync_conflict = False
    if match:
        uuid = match.group(1)
        # Remove old BearID: from new note
        md_text = re.sub(r'\<\!-- ?\{BearID\:' + uuid + r'\} ?--\>', '', md_text).rstrip() + '\n'

        sync_conflict = check_sync_conflict(uuid, ts_last_export)
        if sync_conflict:
            link_original = 'bear://x-callback-url/open-note?id=' + uuid
            message = '::Sync conflict! External update: ' + time_stamp_ts(ts) + '::'
            message += '\n[Click here to see original Bear note](' + link_original + ')'
            x_create = 'bear://x-callback-url/create?show_window=no' 
            bear_x_callback(x_create, md_text, message, '')   
        else:
            # Regular external update
            orig_title = backup_bear_note(uuid, ts)
            # message = '::External update: ' + time_stamp_ts(ts) + '::'   
            x_replace = 'bear://x-callback-url/add-text?show_window=no&mode=replace&id=' + uuid
            bear_x_callback(x_replace, md_text, '', orig_title)
            # # Trash old original note:
            # x_trash = 'bear://x-callback-url/trash?show_window=no&id=' + uuid
            # subprocess.call(["open", x_trash])
            # time.sleep(.2)
    else:
        message = '::New external Note - ' + time_stamp_ts(ts) + '::' 
        x_create = 'bear://x-callback-url/create?show_window=no' 
        bear_x_callback(x_create, md_text, message, '')   
    return


def bear_x_callback(x_command, md_text, message, orig_title):
    if message != '':
        lines = md_text.splitlines()
        lines.insert(1, message)
        md_text = '\n'.join(lines)
    if orig_title != '':
        lines = md_text.splitlines()
        title = re.sub(r'^#+ ', r'', lines[0])
        if title != orig_title:
            md_text = '\n'.join(lines)
        else:
            md_text = '\n'.join(lines[1:])        
    x_command_text = x_command + '&text=' + urllib.parse.quote(md_text)
    subprocess.call(["open", x_command_text])
    time.sleep(.2)


def check_sync_conflict(uuid, ts_last_export):
    conflict = False
    # Stub: Check modified date of original note in Bear sqlite db!
    conn = sqlite3.connect(bear_db)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM `ZSFNOTE` WHERE `ZTRASHED` LIKE '0' AND `ZUNIQUEIDENTIFIER` LIKE '" + uuid + "'"
    c = conn.execute(query)
    for row in c:
        title = row['ZTITLE']
        modified = row['ZMODIFICATIONDATE']
        uuid = row['ZUNIQUEIDENTIFIER']
        mod_dt = dt_conv(modified)
        dtdate = datetime.datetime.fromtimestamp(mod_dt)
        # print(dtdate.strftime('%Y-%m-%d %H:%M'))
        # print(title, ts_last_export, mod_dt)
        conflict = mod_dt > ts_last_export
    conn.close()
    return conflict


def backup_bear_note(uuid, mod_dt):
    # Get single note from Bear sqlite db!
    conn = sqlite3.connect(bear_db)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM `ZSFNOTE` WHERE `ZUNIQUEIDENTIFIER` LIKE '" + uuid + "'"
    c = conn.execute(query)
    title = ''
    for row in c:  # Will only get one row if uuid is found!
        title = row['ZTITLE']
        md_text = row['ZTEXT'].rstrip()
        # modified = row['ZMODIFICATIONDATE']
        # mod_dt = dt_conv(modified)
        md_text = insert_link_top_note(md_text, 'Link to updated note: ', uuid)
        dtdate = datetime.datetime.fromtimestamp(mod_dt)
        filename = clean_title(title) + dtdate.strftime(' - %Y-%m-%d_%H%M') + '.md'
        save_to_backup(filename, md_text, mod_dt)
    conn.close()
    return title


def insert_link_top_note(md_text, message, uuid):
    lines = md_text.split('\n')
    title = re.sub(r'^#{1,6} ', r'', lines[0])
    link = '::' + message + '[' + title + '](bear://x-callback-url/open-note?id=' + uuid + ')::'        
    lines.insert(1, link) 
    return '\n'.join(lines)


def save_to_backup(filename, md_text, ts):
    if not os.path.exists(sync_backup):
        os.makedirs(sync_backup)
    synced_file = os.path.join(sync_backup, filename)
    count = 2
    while os.path.exists(synced_file):
        # Adding sequence number to identical filenames, preventing overwrite:
        file_part = re.sub(r"(( - \d\d)?\.md)", r"", synced_file)
        synced_file = file_part + " - " + str(count).zfill(2) + ".md"
        count += 1
    write_file(synced_file, md_text, ts)
    print("*** Copied file to sync_backup: " + filename)


def notify(message):
    title = "ul_sync_md.py"
    try:
        # Uses "terminal-notifier", download at:
        # https://github.com/julienXX/terminal-notifier/releases/download/2.0.0/terminal-notifier-2.0.0.zip
        # Only works with MacOS 10.11+
        subprocess.call(['/Applications/terminal-notifier.app/Contents/MacOS/terminal-notifier',
                         '-message', message, "-title", title, '-sound', 'default'])
    except:
        print('* "terminal-notifier.app" is missing!')
    # print("* Message:", str(message.encode("utf-8")))
    return


if __name__ == '__main__':
    main()
