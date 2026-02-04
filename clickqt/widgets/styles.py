def BLOB_BUTTON_STYLE_ENABLED(btnsizehalfpx: int):
    return f"""
        QToolButton {{
            background-color: #0f0;
            border-radius: {btnsizehalfpx}px;
            border-style: outset;
            padding: 5px;
        }}
        QToolButton:hover {{
            background-color: #9f9;
        }}
    """


def BLOB_BUTTON_STYLE_DISABLED(btnsizehalfpx: int):
    return f"""
        QToolButton {{
            background-color: #f00;
            border-radius: {btnsizehalfpx}px;
            border-style: outset;
            padding: 5px;
        }}
        QToolButton:hover {{
            background-color: #f99;
        }}
    """


def BLOB_BUTTON_STYLE_ENABLED_FORCED(btnsizehalfpx: int):
    return f"""
        QToolButton {{
            background-color: #696;
            border-radius: {btnsizehalfpx}px;
            border-style: outset;
            padding: 5px;
        }}
        QToolButton:hover {{
            background-color: #898;
        }}
    """


def BLOB_BUTTON_STYLE_DISABLED_FORCED(btnsizehalfpx: int):
    return f"""
        QToolButton {{
            background-color: #966;
            border-radius: {btnsizehalfpx}px;
            border-style: outset;
            padding: 5px;
        }}
        QToolButton:hover {{
            background-color: #988;
        }}
    """
