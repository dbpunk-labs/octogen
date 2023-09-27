# vim:fenc=utf-8
#
# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
