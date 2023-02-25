import os
import re
import tempfile
from typing import List, Optional

import requests
from langdetect import detect_langs
from pytesseract import pytesseract, TesseractError
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

path_to_tesseract = '/Users/19016133/homebrew/Cellar/tesseract/5.3.0_1/bin/tesseract'
pytesseract.tesseract_cmd = path_to_tesseract
os.environ['TESSDATA_PREFIX'] = 'trained_data'

BOT_TOKEN = os.environ.get('BOT_TOKEN')

LANGDETECT_LANG_TO_TESSERACT_LANG = {
    "ab": "abk",
    "aa": "aar",
    "af": "afr",
    "ak": "aka",
    "sq": "sqi",
    "am": "amh",
    "ar": "ara",
    "an": "arg",
    "hy": "hye",
    "as": "asm",
    "av": "ava",
    "ae": "ave",
    "ay": "aym",
    "az": "aze",
    "bm": "bam",
    "ba": "bak",
    "eu": "eus",
    "be": "bel",
    "bn": "ben",
    "bi": "bis",
    "bs": "bos",
    "br": "bre",
    "bg": "bul",
    "my": "mya",
    "ca": "cat",
    "ch": "cha",
    "ce": "che",
    "ny": "nya",
    "zh": "zho",
    "cu": "chu",
    "cv": "chv",
    "kw": "cor",
    "co": "cos",
    "cr": "cre",
    "hr": "hrv",
    "cs": "ces",
    "da": "dan",
    "dv": "div",
    "nl": "nld",
    "dz": "dzo",
    "en": "eng",
    "eo": "epo",
    "et": "est",
    "ee": "ewe",
    "fo": "fao",
    "fj": "fij",
    "fi": "fin",
    "fr": "fra",
    "fy": "fry",
    "ff": "ful",
    "gd": "gla",
    "gl": "glg",
    "lg": "lug",
    "ka": "kat",
    "de": "deu",
    "el": "ell",
    "kl": "kal",
    "gn": "grn",
    "gu": "guj",
    "ht": "hat",
    "ha": "hau",
    "he": "heb",
    "hz": "her",
    "hi": "hin",
    "ho": "hmo",
    "hu": "hun",
    "is": "isl",
    "io": "ido",
    "ig": "ibo",
    "id": "ind",
    "ia": "ina",
    "ie": "ile",
    "iu": "iku",
    "ik": "ipk",
    "ga": "gle",
    "it": "ita",
    "ja": "jpn",
    "jv": "jav",
    "kn": "kan",
    "kr": "kau",
    "ks": "kas",
    "kk": "kaz",
    "km": "khm",
    "ki": "kik",
    "rw": "kin",
    "ky": "kir",
    "kv": "kom",
    "kg": "kon",
    "ko": "kor",
    "kj": "kua",
    "ku": "kur",
    "lo": "lao",
    "la": "lat",
    "lv": "lav",
    "li": "lim",
    "ln": "lin",
    "lt": "lit",
    "lu": "lub",
    "lb": "ltz",
    "mk": "mkd",
    "mg": "mlg",
    "ms": "msa",
    "ml": "mal",
    "mt": "mlt",
    "gv": "glv",
    "mi": "mri",
    "mr": "mar",
    "mh": "mah",
    "mn": "mon",
    "na": "nau",
    "nv": "nav",
    "nd": "nde",
    "nr": "nbl",
    "ng": "ndo",
    "ne": "nep",
    "no": "nor",
    "nb": "nob",
    "nn": "nno",
    "ii": "iii",
    "oc": "oci",
    "oj": "oji",
    "or": "ori",
    "om": "orm",
    "os": "oss",
    "pi": "pli",
    "ps": "pus",
    "fa": "fas",
    "pl": "pol",
    "pt": "por",
    "pa": "pan",
    "qu": "que",
    "ro": "ron",
    "rm": "roh",
    "rn": "run",
    "ru": "rus",
    "se": "sme",
    "sm": "smo",
    "sg": "sag",
    "sa": "san",
    "sc": "srd",
    "sr": "srp",
    "sn": "sna",
    "sd": "snd",
    "si": "sin",
    "sk": "slk",
    "sl": "slv",
    "so": "som",
    "st": "sot",
    "es": "spa",
    "su": "sun",
    "sw": "swa",
    "ss": "ssw",
    "sv": "swe",
    "tl": "tgl",
    "ty": "tah",
    "tg": "tgk",
    "ta": "tam",
    "tt": "tat",
    "te": "tel",
    "th": "tha",
    "bo": "bod",
    "ti": "tir",
    "to": "ton",
    "ts": "tso",
    "tn": "tsn",
    "tr": "tur",
    "tk": "tuk",
    "tw": "twi",
    "ug": "uig",
    "uk": "ukr",
    "ur": "urd",
    "uz": "uzb",
    "ve": "ven",
    "vi": "vie",
    "vo": "vol",
    "wa": "wln",
    "cy": "cym",
    "wo": "wol",
    "xh": "xho",
    "yi": "yid",
    "yo": "yor",
    "za": "zha",
    "zu": "zul",
}
TEST_CONFIG = '-l eng+rus'


def read_text_from_image(img) -> Optional[str]:
    try:
        text = pytesseract.image_to_string(img, config=TEST_CONFIG)
    except TesseractError:
        return None

    if not text:
        return None

    correct_config = '-l '
    langs_probs = detect_langs(text)
    # print(langs_probs)
    correct_config += '+'.join([LANGDETECT_LANG_TO_TESSERACT_LANG[lang.lang] for lang in langs_probs])
    correct_text = pytesseract.image_to_string(img, config=correct_config)

    return correct_text


def create_images_with_given_text(text: str) -> List[bytes]:
    print(text)

    groups_of_parts = []
    curr_parts = []
    curr_part = []
    curr_len = 0

    text_parts = text.split('\n\n')
    for text_part in text_parts:
        text_part = re.sub('\\s+', ' ', text_part).strip()

        for word in text_part.split():
            # max: 25x11
            if curr_len + len(word) >= 25:
                curr_parts.append(' '.join(curr_part))
                if len(curr_parts) >= 11:
                    groups_of_parts.append(curr_parts)
                    curr_parts = []
                curr_part = []
                curr_len = 0

            curr_part.append(word)
            curr_len += len(word)

        if curr_part:
            curr_parts.append(' '.join(curr_part))
            curr_parts.append('')
            curr_part = []
            curr_len = 0

            if len(curr_parts) >= 11:
                groups_of_parts.append(curr_parts)
                curr_parts = []

    if curr_part:
        curr_parts.append(' '.join(curr_part))

    if curr_parts:
        groups_of_parts.append(curr_parts)

    for i, group_of_parts in enumerate(groups_of_parts):
        if not group_of_parts[-1]:
            del group_of_parts[-1]

    images = []
    for i, parts in enumerate(groups_of_parts, start=1):
        tmp_text = '|'.join(parts)
        tmp_text = re.sub('#', '_', tmp_text)
        url: str = f"http://chart.apis.google.com/chart?chst=d_text_outline&chld=000000|32|l|FFFFFF|_|{tmp_text}"
        print(url)
        response = requests.get(url)

        print(response.status_code)
        if not response.ok:
            raise ValueError("INVALID DATA!")

        images.append(response.content)

    return images


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_html(
        "Hi there! I am able to split your text into readable pages! Just send me a picture with text :)"
    )


async def parse_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parse user images."""
    photos = update.message.photo
    document = update.message.document

    if not photos and not document:
        await update.message.reply_text(
            "It is not a photo"
        )
        return

    if photos:
        photo = await photos[-1].get_file()
    else:
        photo = await document.get_file()

    with tempfile.NamedTemporaryFile() as tmp:
        await photo.download_to_memory(tmp)
        text: Optional[str] = read_text_from_image(tmp.name)

    if text:
        images = create_images_with_given_text(text)
        await update.message.reply_media_group(
            media=[InputMediaPhoto(image, caption=f'{i}') for i, image in enumerate(images, start=1)]
        )
        return
    else:
        await update.message.reply_text(
            "There is no text on the picture(s)"
        )
        return


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, parse_image))

    application.run_polling()


if __name__ == '__main__':
    main()
