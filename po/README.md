## Updating translations

#### Note: All of these should be run from the project root directory

To update the translations for Repoman, use the following command to generate
an updated POT file:

`xgettext -L Python -d repoman -p po/ -o repoman.pot repoman/*`

Then update the existing PO files with the updated strings:

`msgmerge po/LANG.po po/repoman.pot -U`

Add any missing translations, then generate the actual messages for gettext:

`msgfmt -o po/LANG/repoman.mo po/LANG.po`


## Adding missing languages

Generate a new PO file from the existing POT file:

`msginit -i po/repoman.pot -o po/LANG.po -l LANG`

Then translate the strings in LANG.po. To generate the messages:

`msgfmt -o po/LANG/repoman.mo po/LANG.po`
