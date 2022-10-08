@echo on
for /f %%f in ('dir /a /b /s .\build') do (del /q %%f)
for /f %%f in ('dir /a /b /s .\source ^| findstr .rst ^| findstr /v index.rst ^| findstr /v api.rst') do (del /q %%f)
exit
