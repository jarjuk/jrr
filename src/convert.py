import os
def convert_main(parsed):
    mypath = parsed.image_dir
    for f in os.listdir(mypath):
        filepath = os.path.join(mypath, f)
        if os.path.isfile(filepath):
            logger.info("filepath: %s", filepath)

