import webview

def open_file_dialog(window):
    file_types = ('PJson Files (*.pjson)', 'All files (*.*)')

    result = window.create_file_dialog(webview.OPEN_DIALOG,  directory='.', allow_multiple=False, file_types=file_types)
    print(result)
    window.destroy()


def save_file_dialog(window):
    result = window.create_file_dialog(webview.SAVE_DIALOG, directory='.', save_filename='untitled.pjson')
    print(result)
    window.destroy()

def main():
    window = webview.create_window('Open file dialog example', 'https://pywebview.flowrl.com/hello', frameless=True)
    # webview.start(save_file_dialog, window)
    webview.start(open_file_dialog, window)


if __name__ == '__main__':
    main()