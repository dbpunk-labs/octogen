Installation
============

You can install octopus to your local computer and cloud server

Requirements
------------

Octopus works with macOs, Linux and Windows.
Octopus requires the following enviroment

- Python 3.10.0 and above.
- `Pip <https://pip.pypa.io/en/stable/installation/>`_
- `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_ 

To use codellama, your host must have at least 8 CPUs and 16 GB of RAM

Install
-------------------------

the first step, install ``og_up`` tool::

    $ pip install og_up

the second step, use ``og_up`` to setup the octopus service and cli::

    $ og_up

You have the option to select from 

- OpenAI
- Azure OpenAI
- CodeLlama
- Octogen(beta) agent services

If you opt for CodeLlama, Octogen will automatically download it from huggingface.co. 
In case the installation of the Octogen Terminal CLI is taking longer than expected, 
you might want to consider switching to a different pip mirror.

the third step, open your terminal and execute the command ``og``, you will see the following output::

    Welcome to use octogen❤️ . To ask a programming question, simply type your question and press esc + enter
    You can use /help to look for help

    [1]🎧>


