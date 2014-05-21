bROT - Better ROOT
==================

This tool is meant to be used from a Python interpreter and allows for quick and
efficient plotting of ROOT based LHC data analyses.


Installation
------------

To start using bROT, you first have to clone the project into a directory of
your choice.

```
git clone https://github.com/radziej/bROT.git bROT
```

In principle, bROT is now read to use.

For convenience, it is recommended to have a python command history for easier
access to previously used commands. To set up a history for the common Python
interpreter, one can copy the following file into their home directory.

```
git clone https://gist.github.com/28185647752b647e1f4e.git ~/.pystartup
```

And then load it via their '.bashrc'.

```
export PYTHONSTARTUP=${HOME}/.pystartup
```


Usage
-----

Change into the 'brot' subdirectory and load 'brot.py' into the python interpreter.

```
python -i brot.py
```