#!/usr/bin/env python
import os
import sys

import shutil
import logging
from io import BytesIO
from PIL import Image
from shutil import copyfileobj

from zipfile import ZipFile
import tarfile

from tempfile import mkdtemp
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

extentionByFormat = {
    "JPEG": ".jpeg",
    "JPG": ".jpg",
    "WEBP": ".webp",
    "PNG": ".png"
}


def filename_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


def get_extention(file_name):
    return os.path.splitext(file_name)[1].lower()


def unpack_archive(path):
    tmp_dir = mkdtemp()
    file_extension = get_extention(path)

    if file_extension in ['.zip', '.cbz']:
        archive = ZipFile(path, 'r')
        namelist = archive.namelist()
    elif file_extension in [".tar", ".cbt"]:
        archive = tarfile.TarFile(path, 'r')
        namelist = archive.getnames()

    for member in namelist:
        filename = os.path.basename(member)
        # if directory break the loop
        if not filename:
            continue

        # extract each file
        source = archive.open(member)
        target = open(os.path.join(path, filename), "wb")
        with source, target:
            copyfileobj(source, target)

    return tmp_dir


class DisplayManager():
    def __init__(self):
        self.terminal_size = 30
        try:
            self.terminal_size = int(
                os.popen('stty size', 'r').read().split()[1])
        except Exception as e:
            pass

        self.bar_length = 20

        self.job_title = None
        self.current_steps = [0, 0]

        self.block = False

    def new_job(self, title, number_of_step):
        self.job_title = title
        self.current_steps = [0, number_of_step]
        self.diplay_job()

    def update_job(self, step=1):
        self.current_steps[0] += 1
        self.diplay_job()

    def diplay_job(self):
        if not self.block:
            progress_line = ""  # string to display

            # compute loading bar length
            if len(self.job_title) + 3 + self.bar_length <= self.terminal_size:
                percent_progression = self.current_steps[0] * \
                    self.bar_length / self.current_steps[1]

                # building loading string
                loading_string = "#" * int(percent_progression)
                while len(loading_string) < self.bar_length:
                    loading_string += " "
                loading_string = "[%s]" % loading_string

                # build the whole line
                white_spaces = " " * \
                    (self.terminal_size - (len(self.job_title) +
                                           len(loading_string)))
                progress_line = "%s%s%s" % (
                    self.job_title, white_spaces, loading_string)
            else:
                loading_string = " [%i/%i]" % (self.current_steps[0],
                                               self.current_steps[1])
                if len(self.job_title) <= self.terminal_size:
                    progress_line = self.job_title
                else:
                    progress_line = self.job_title[:self.terminal_size]

                # fill with white space
                while len(progress_line) < self.terminal_size:
                    progress_line += " "

                # add loading string to line
                progress_line = progress_line[:len(
                    progress_line) - len(loading_string)] + loading_string

            # go back in terminal to rewrite the line
            if(self.current_steps[0] == self.current_steps[1]):
                print(progress_line)
            else:
                print(progress_line, end='\r')


def convert_file(origin, image_format, resize, futur_file_name,
                 tar_destination):
    try:
        im = Image.open(origin).convert("RGB")

        if resize[0]:
            im.thumbnail((int(resize[0]), int(resize[1])), Image.ANTIALIAS)

        tmpFile = BytesIO()
        im.save(tmpFile, image_format, quality=90)
        tmpFile.seek(0)

        info = tarfile.TarInfo(futur_file_name)
        info.size = len(tmpFile.getbuffer())
        with tar_archive_lock:
            tar_destination.addfile(info, tmpFile)
        tmpFile.close()

    except Exception as e:
        logger.info("---- error occured while converting: %s" % origin)
        logger.info("------ %s" % e)


diplay_manager = DisplayManager()
tar_archive_lock = Lock()


def convert_archive(working_directory, new_file_path, image_format="JPEG",
                    resize=None):

    with tarfile.open(new_file_path, "w") as tar_file:
        file_to_process = []

        # search all files in the extracted directory
        for dir_name, dir_list, file_list in os.walk(working_directory):
            for fileName in file_list:
                # if the file is exploitable we push it in list
                if get_extention(fileName) in extentionByFormat.values():
                    file_to_process.append(os.path.join(dir_name, fileName))

        # we convert every file
        diplay_manager.new_job(os.path.basename(
            new_file_path), len(file_to_process))
        executor = ThreadPoolExecutor(max_workers=5)
        futures = []

        for image_path in file_to_process:
            new_file_name = '%s%s' % (os.path.splitext(image_path)[
                                      0], extentionByFormat[image_format])

            # substract temp file path ex: /tmp/fesfene
            new_file_name = new_file_name.replace(
                "%s/" % working_directory, "")

            task = executor.submit(convert_file, image_path, image_format,
                                   resize, new_file_name, tar_file)
            task.add_done_callback(diplay_manager.update_job)
            futures.append(task)

        try:
            executor.shutdown(wait=True)
        except KeyboardInterrupt:
            print("Warning, program stopped, archive incomplete")
            for future in futures:
                future.cancel()
            DisplayManager.block = True
            # we waiting thread to finish
            executor.shutdown(wait=True)
            sys.exit()


def launch(path="./", image_format="JPEG", resize=None, recursive=False):
    root_dir = os.getcwd()

    files_to_process = []

    # we walk directory topdown
    for dir_name, dir_list, file_list in os.walk(path):
        for file_name in file_list:
            # we check if each file is supported
            if get_extention(file_name).replace(".", "") in ['.zip', '.cbz',
                                                             '.tar', 'cbt']:
                # we rebuild the filename path
                files_to_process.append("%s/%s" % (dir_name, file_name))
        if not recursive:
            break

    for archive_path in files_to_process:
        logger.info("- Unpacking: %s" % archive_path)
        file_path = os.path.join(root_dir, archive_path)

        # unpacking archive
        unpacked_archive_path = unpack_archive(file_path)
        new_file_path = "%s.tar" % os.path.splitext(file_path)[0]

        convert_archive(unpacked_archive_path,
                        new_file_path, image_format, resize)

        # we clean unpacked directory
        shutil.rmtree(unpacked_archive_path)
        logger.info("- Finished: %s" % new_file_path)
