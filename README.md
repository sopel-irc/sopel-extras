#Introduction

This repository holds modules for [Willie](https://github.com/embolalia/willie)
which, for whatever reason, we don't want to include in the main repository. It
may be that they are used for some specific purpose on [NFIRC](http://dftba.net)
which doesn't have the broad use that makes it worth putting in Willie. It may
be that the module conflicts with another module in Willie in some way, so it's
been removed to require explicitly adding it and running a separate instance. It
may be that the module is new, experimental, or just broken. It may be some
other reason.

#Instructions

The easiest way to install these is to put them in ``~/.willie/modules``, and
then add ``extra = /home/yourname/.willie/modules`` to the ``[core]`` section of
your config file.

If any one module has further instructions, there will (probably) be a file
named something like ``modulename-README.md`` to detail them.

#Copying

Each file is licensed individually. If no license is stated, the Eiffel Forum
License v2, below, can be assumed.

Eiffel Forum License, version 2

1. Permission is hereby granted to use, copy, modify and/or distribute this
  package, provided that:
  * copyright notices are retained unchanged,
  * any distribution of this package, whether modified or not, includes this license text.

2. Permission is hereby also granted to distribute binary programs
  which depend on this package. If the binary program depends on a
  modified version of this package, you are encouraged to publicly
  release the modified version of this package.

***********************

THIS PACKAGE IS PROVIDED "AS IS" AND WITHOUT WARRANTY. ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE TO ANY PARTY FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES ARISING IN ANY WAY OUT OF THE USE OF THIS PACKAGE.

***********************
