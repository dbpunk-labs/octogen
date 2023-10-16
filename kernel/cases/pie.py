# Copyright (C) 2023 dbpunk.com Author imotai <codego.me@gmail.com>
# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

""" """
import matplotlib.pyplot as plt
import numpy as np

# Create a pie chart
data = np.array([10, 20, 30, 40])
labels = ["Category 1", "Category 2", "Category 3", "Category 4"]

plt.pie(data, labels=labels, autopct="%1.1f%%")
plt.title("Pie Chart")
plt.show()
