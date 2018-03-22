#!/usr/bin/python3
'''
   Copyright 2017 Mirko Brombin (brombinmirko@gmail.com)
   Copyright 2017 Ian Santopietro (ian@system76.com)

   This file is part of Repoman.

    Repoman is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Repoman is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Repoman.  If not, see <http://www.gnu.org/licenses/>.
'''

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class App:
    application_id = "repoman"
    application_name = "Repoman"
    application_description = "Easily manage PPAs"
    application_version ="1.0"
    main_url = "https://github.com/isantop/repoman"
    bug_url = "https://github.com/isantop/repoman/issues/labels/bug"
    help_url = "https://github.com/isantop/repoman/issues"
    about_authors = {"Ian Santopietro <ian@system76.com>"}
    about_comments = application_description
    about_license_type = Gtk.License.GPL_3_0
