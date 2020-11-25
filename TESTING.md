# TESTING.md

*Package Maintainers!*
This document describes testing procedures for the software contained in this
repository. All sections must be completed and signed off before a package can
be moved from one repository to the next.

## Part 1: Staging -> Proposed
* Did it build?
* Are files present in build package:
    - Check package, data.tar - make sure all files intended to be installed are
      there

## Part 2: Proposed -> Stable

All advertised functionality must be present and functional. 
Things to check for correct function:

* Install `software-properties-gtk` from apt, if not installed.
* Settings Tab: 
  1. Disable all checkmarks listed in both standard and developer options
  2. Launch `software-properties-gtk` and check that all sources are disabled
     * Four main repos are in "Ubuntu Software" Tab
     * Source Code is in "Ubuntu Software" Tab
     * Pre-release updates is in "Developer Options" tab
     * `software-properties-gtk` must now be closed.
  3. Enable all source checkmarks in both standard and developer options
  4. Launch `software-properties-gtk` and check that all sources are enabled
     * Same places as before.
     * Remember to close `software-properties-gtk`
* Updates Tab:
  1. Disable all update repos in Updates Tab
  2. Launch `software-properties-gtk` and check that all sources are disabled
     * All repos are in "Updates" tab.
     * Close `software-properties-gtk` now.
  3. Enable all update repos in Updates Tab
  4. Launch `software-properties-gtk` and check that all sources are enabled
     * Same places, close when finished.
* Extra Sources Tab:
  1. Click "Add" (+) button at bottom.
     * "Add Source" dialog appears
     * "Add" button is grayed out.
  2. Add extra repository (e.g. `ppa:system76/proposed`)
     * "Add" button is enabled when valid ppa is typed in.
     * Repository is added to list after breif update
  3. Select repository and click the modify button (pencil icon); check that Modify Source dialog opens.
     * "Modify Source" dialog opens.
     * "Cancel" button in top left.
     * Green "Save" button in top right.
  4. Set "Version" to `xenial`
  5. Set "Type" to `Source Code`
  6. Click "Save".
     * Dialog closes
     * Repository is updated in list after a short delay.
  7. Click same repository and click modify button.
     * "Modify Source" opens again.
  8. Change "Version" to `xebiak`
  9. Click "Save"
      * Repository is updated after delay.
      * Error message appears: "Does not have a Release File"
  10. Click Close
  11. Select same repository and click modify
      * "Modify Source" opens again.
  12. Change "Version" to xenial
  13. Turn off "Enabled" Switch
  14. Click "Save"
      * Repository is updated and moved to disabled section below.
      * Repository is not bold
      * "_(disabled)_" is appended to end of repository
  15. Select same repository and click the remove button
      * "Remove Source" confirmation dialog opens.
      * "Cancel button" in top left
      * Red "Remove" button in top right.
  16. Click "Remove"
      * Repository disappears from list after short delay.
  17. Select "Pop-OS" Repository and click the remove button
      * "Remove Source" dialog opens again.
  18. Click "Cancel"
      * "Remove Source" dialog closes.
      * "Pop-OS" repository remains in list.
  
