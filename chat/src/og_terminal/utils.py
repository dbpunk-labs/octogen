# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """


def parse_file_path(real_prompt):
    """
    parse the file path from the prompt
    """
    filepaths = []
    position = 0
    while position < len(real_prompt):
        first_pos = real_prompt.find("/up", position)
        # break the loop if no file to upload
        if first_pos == -1 or len(real_prompt) - first_pos <= 4:
            break
        #
        if real_prompt[first_pos + 3] != " ":
            position = first_pos + 4
            continue
        end_pos = real_prompt.find("\n", first_pos + 4)
        end_pos = end_pos if end_pos >= 0 else len(real_prompt)
        blank_pos = real_prompt.find(" ", first_pos + 4, end_pos)
        if blank_pos == -1:
            filepath = real_prompt[first_pos + 4 : end_pos]
            position = len(real_prompt)
        else:
            filepath = real_prompt[first_pos + 4 : blank_pos]
            position = blank_pos
        if filepath:
            filepaths.append(filepath)
    return filepaths
