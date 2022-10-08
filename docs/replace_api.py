import os


# 代码来源于网络
source_api_path = 'source'
old_automo_method = 'automodule'
automo_method = 'automodapi' # automodapi | automodsumm | automodule
for rst_file in os.listdir(source_api_path):
    if rst_file.endswith('.rst'):
        with open(source_api_path + os.sep + rst_file, 'r', encoding="utf-8") as f:
            contents = f.read()
        contents = contents.replace(old_automo_method, automo_method)
        with open(source_api_path + os.sep + rst_file, 'w', encoding="utf-8") as f:
            f.write(contents)
        print(f"change {source_api_path}/{rst_file} {old_automo_method} => {automo_method}")