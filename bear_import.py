# encoding=utf-8
# python3.6
# bear_import.py
# Developed with Visual Studio Code with MS Python Extension.

'''
# Markdown import to Bear from folder  
Version 1.0.0 - 2018-02-10 at 17:37 EST
github/rovest, rorves@twitter

## NEW import function: 
* Imports markdown or textbundles from nested folders under a `BearImport/input/' folder
* Foldernames are converted to Bear tags
* Also imports MacOS file tags as Bear tags
* Imported notes are also tagged with `#.imported/yyyy-MM-dd` for convenience.
* Import-files are then cleared to a `BearImport/done/' folder
* Use for email input to Bear with Zapier's "Gmail to Dropbox" zap.
* Or for import of nested groups and sheets from Ulysses, images and keywords included.
'''

my_sync_service = 'Dropbox'  # Change 'Dropbox' to 'Box', 'Onedrive',
    # or whatever folder of sync service you need.
    # Your user "Home" folder is added below.

use_filename_as_title = False  # Set to `True` if importing Simplenotes synced with nvALT.
set_logging_on = True

# This tag is added for convenience (easy deletion of imported notes they are not wanted.)
# (Easier to delete one tag, than finding a bunch of tagless imported notes.)

import datetime
import re
import subprocess
import urllib.parse
import os
import time
import shutil
import fnmatch
import json

import_tag = '#.imported/' + datetime.datetime.now().strftime('%Y-%m-%d')
# import_tag = ''  # Blank if not needed

HOME = os.getenv('HOME', '')

# Import folder for files from other apps, 
# or incoming emails via "Gmail to Dropbox" Zapier zap or IFTTT
bear_import = os.path.join(HOME, my_sync_service, 'BearImport')
import_path = os.path.join(bear_import, 'input')
import_done = os.path.join(bear_import, 'done')

gettag_sh = os.path.join(HOME, 'temp/gettag.sh')
gettag_txt = os.path.join(HOME, 'temp/gettag.txt')


def main():
    if not os.path.exists(import_path):
        os.makedirs(import_path)
        print('New path, use it for import to Bear:', import_path)
        return False
    if not os.path.exists(import_done):
        os.makedirs(import_done)
    init_gettag_script()
    count = import_external_files()
    print(str(count), 'files imported.  Job done!')


def import_external_files():
    files_found = False
    file_types = ('*.md', '*.txt', '*.markdown')
    count = 0
    time.sleep(3)  # Wait a little bit after being triggered by Automator Folder Action
    for (root, dirnames, filenames) in os.walk(import_path):
        '''
        This step walks down into all sub folders, if any.
        '''
        for pattern in file_types:
            for filename in fnmatch.filter(filenames, pattern):
                if not files_found:  # Yet
                    # Wait 5 sec at first for external files to finish downloading from dropbox.
                    # Otherwise images in textbundles might be missing in import:
                    time.sleep(5)
                files_found = True
                md_file = os.path.join(root, filename)
                mod_dt = os.path.getmtime(md_file)
                md_text = read_file(md_file)
                if pattern == '*.txt':
                    # Replace rich text bullets to markdown:
                    # (When using with IFTTT or Zapier and Gmail to Dropbox zap.)
                    md_text = md_text.replace('\n• ', '\n- ')
                    md_text = md_text.replace('\n    • ', '\n\t- ')
                    md_text = md_text.replace('\n        • ', '\n\t\t- ')
                if re.search(r'!\[.*?\]\(assets/.+?\)', md_text) \
                    and '.textbundle/' in md_file:
                    # New textbundle with images:
                    bundle = os.path.split(md_file)[0]
                    md_text = get_tag_from_path(md_text, bundle, import_path, False)
                    write_file(md_file, md_text, mod_dt)
                    os.utime(bundle, (-1, mod_dt))
                    subprocess.call(['open', '-a', '/applications/bear.app', bundle])
                    time.sleep(0.5)
                    move_import_to_done(bundle, import_path, import_done)
                else:
                    title = ''
                    # No images, import markdown only even if textbundle:
                    if '.textbundle/' in md_file:
                        file_bundle = os.path.split(md_file)[0]
                    else:
                        file_bundle = md_file
                        if use_filename_as_title:
                            title = os.path.splitext(os.path.split(md_file)[1])[0]
                    md_text = get_tag_from_path(md_text, file_bundle, import_path, False)                    
                    x_create = 'bear://x-callback-url/create?show_window=no' 
                    bear_x_callback(x_create, md_text, title)
                    move_import_to_done(file_bundle, import_path, import_done)
                write_log('Imported to Bear: ', file_bundle)
                count += 1
    if files_found:
        # cleanup empty input sub folders here ??? 
        # But quite tricky since new files may appear. Bette to do that manually when needed.
        # Recursive call to look for leftovers/newly downloaded files: 
        count += import_external_files()
    return count


def move_import_to_done(file_bundle, import_path, import_done):
    file_path = file_bundle.replace(import_path + '/', '')
    sub_path = os.path.split(file_path)[0]
    dest_path = os.path.join(import_done, sub_path)
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    count = 2
    file_name = os.path.split(file_bundle)[1]
    dest_file = os.path.join(dest_path, file_name)
    (file_raw, ext) = os.path.splitext(file_name)
    while os.path.exists(dest_file):
        # Adding sequence number to identical filenames, preventing overwrite:
        dest_file = os.path.join(dest_path, file_raw + " - " + str(count).zfill(2) + ext)
        count += 1
    # dest_path = os.path.split(dest_file)[0]
    shutil.move(file_bundle, dest_file)


def get_tag_from_path(md_text, file_bundle, root_path, inbox_for_root=True):
    path = file_bundle.replace(root_path, '')[1:]
    sub_path = os.path.split(path)[0]
    tags = []
    if sub_path == '': 
        if inbox_for_root:
            tag = '#.inbox'
        else:
            tag = ''
    elif sub_path.startswith('_'):
        tag = '#.' + sub_path[1:].strip()
    else:
        tag = '#' + sub_path.strip()
    if ' ' in tag: 
        tag += "#"               
    if tag != '': 
        tags.append(tag)
    if import_tag != '':
        tags.append(import_tag)
    for tag in get_file_tags(file_bundle):
        tag = '#' + tag.strip()
        if ' ' in tag: tag += "#"                   
        tags.append(tag)
    return md_text.strip() + '\n\n' + ' '.join(tags) + '\n'


def get_file_tags(file_bundle):
    try:
        subprocess.call([gettag_sh, file_bundle, gettag_txt])
        tags_raw = read_file(gettag_txt)
        tags_text = re.sub(r'\\n\d{1,2}', r'', tags_raw)
        tag_list = json.loads(tags_text)
        return tag_list
    except:
        return []


def bear_x_callback(x_command, md_text, title):
    if title != '' and not title.startswith("#"):
        md_text = '# ' + title + '\n' + md_text
    x_command_text = x_command + '&text=' + urllib.parse.quote(md_text)
    subprocess.call(["open", x_command_text])
    time.sleep(.2)


def init_gettag_script():
    gettag_script = \
    '''#!/bin/bash
    if [[ ! -e $1 ]] ; then
    echo 'file missing or not specified'
    exit 0
    fi
    JSON="$(xattr -p com.apple.metadata:_kMDItemUserTags "$1" | xxd -r -p | plutil -convert json - -o -)"
    echo $JSON > "$2"
    '''
    temp = os.path.join(HOME, 'temp')
    if not os.path.exists(temp):
        os.makedirs(temp)
    write_file(gettag_sh, gettag_script, 0)
    subprocess.call(['chmod', '777', gettag_sh])


def write_log(message, file_bundle):
    if set_logging_on == True:
        log_file = os.path.join(import_done, 'bear_import_log.txt')
        time_stamp = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")
        # file_name = os.path.split(file_path)[1]
        file_path = file_bundle.replace(import_path + '/', '')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(time_stamp + ': ' + message + file_path +'\n')


def write_file(filename, file_content, modified):
    with open(filename, "w", encoding='utf-8') as f:
        f.write(file_content)
    if modified > 0:
        os.utime(filename, (-1, modified))


def read_file(file_name):
    with open(file_name, "r", encoding='utf-8') as f:
        file_content = f.read()
    return file_content


if __name__ == '__main__':
    main()
