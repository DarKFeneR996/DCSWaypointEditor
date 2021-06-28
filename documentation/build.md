To build, begin by
[installing python](https://www.python.org/ftp/python/3.9.5/python-3.9.5-amd64.exe)
then
[installing tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
to get the python environment and OCR library the DCS Waypoint Editor uses.

Following installation, reboot/logout to ensure path changes are updated.

Next,
```
pip install -r requirements.txt
pyinstaller -w dcs_wp_editor.py
```
This will install required pypthon packages and create a distribution in
`dist/dcs_wp_editor`. After finishing the build, copy the entire `data/`
directory from the root of the repository into the disribution directory
`dist/dcs_wp_editor` before packaging for install.

If you see a "Failed to execute script" when running the `dcs_wp_editor.exe` 
executable in `dist/dcs_wp_editor`, there are two potential fixes.

First, in the `dcs_wp_editor.spec` file (should be in the same
directory as `dcs_wp_editor.py`), change the `hiddenimports` line to:
```
hiddenimports=['pkg_resources']
```
Then re-run `pyinstaller` on `dcs_wp_editor.spec` (*not* the Python
file, note that if you run `pyinstaller` on the python file, the
`.spec` file will be over-written).

Second, you can add `--hidden-import` to the command line
```
pyinstaller -w --hidden-import pkg_resources dcs_wp_editor.py
```
as in the original invocation. In this case, you should not need to
change the `.spec` file.
