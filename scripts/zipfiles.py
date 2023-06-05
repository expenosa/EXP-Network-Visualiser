import os
from glob import glob
from argparse import ArgumentParser
import zipfile as zip

def zipdir(path, ziph):
    print("Zipping directory: " + path)
    # ziph is zipfile handle
    files = glob(path + "/**/*", recursive=True)
    for f in files:
        print("Zipping file: " + f)
        ziph.write(f)

def zipfile(path, ziph):
    # ziph is zipfile handle
    files = glob(path)
    for f in files:
        print("Zipping file: " + f)
        ziph.write(f)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('zip', help="Output zip file")
    parser.add_argument('files', nargs='+', help="Files to be added to the zip")
    args = parser.parse_args()

    zipf = zip.ZipFile(args.zip, 'w', zip.ZIP_DEFLATED)
    print(f'Zipping files/dirs: {args.files}')
    try:
        for f in args.files:
            if os.path.isdir(f):
                zipdir(f, zipf)
            else:
                zipfile(f, zipf)
        zipf.close()
    except Exception as e:
        zipf.close()
        os.remove(args.zip)
        raise e

    print("Zip File succesfully written.")