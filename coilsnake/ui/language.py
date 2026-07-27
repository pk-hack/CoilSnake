from collections import defaultdict
from dataclasses import dataclass
import json
import logging
from typing import Dict, List, Optional

@dataclass
class Language:
    iso639_1_name: str
    full_name: str
    alternative_names: List[str]

    def get_json_path(self) -> str:
        return f"coilsnake/lang/{self.iso639_1_name}.json"

LANGUAGES: List[Language] = [
    Language("en", "English", []),
    Language("ja", "日本語", ["Japanese", "jp"]),
]

def _build_language_lookup() -> Dict[str, Language]:
    ret = {}
    for language in LANGUAGES:
        for option in (language.iso639_1_name, language.full_name, *language.alternative_names):
            lookup = option.lower()
            assert lookup not in ret, "duplicate language name"
            ret[lookup] = language
    return ret

_LANGUAGE_LOOKUP = _build_language_lookup()

def get_language_by_string(language_str: str) -> Optional[Language]:
    return _LANGUAGE_LOOKUP.get(language_str.lower(), None)

class TranslationStringManager:
    _TRANSLATIONS_LANGUAGE_NOT_LOADED = defaultdict( lambda: "Translation not loaded" )

    @staticmethod
    def _json_to_translations(json_data):
        missing = "Missing localization string"
        return defaultdict(lambda: missing, json_data)

    @classmethod
    def _load_language(cls, language: Language):
        try:
            with open(language.get_json_path(), "r", encoding="utf-8") as file:
                json_data = json.load(file)
            return cls._json_to_translations(json_data)
        except:
            return None

    def __init__(self):
        self.translations = self._TRANSLATIONS_LANGUAGE_NOT_LOADED
        self.callbacks = set()

    def get(self, string_name: str) -> str:
        return self.translations[string_name]

    def change_language(self, language: Language = None, language_name: str = None) -> None:
        if not language:
            language = get_language_by_string(language_name)
        if not language:
            return False
        translations = self._load_language(language)
        if not translations:
            return False
        self.translations = translations
        for cb in self.callbacks:
            cb()
        return True

    def register_callback(self, cb, invoke=True):
        self.callbacks.add(cb)
        if invoke:
            cb()

global_strings = TranslationStringManager()

class TranslatedLogRecord(logging.LogRecord):
    def getMessage(self):
        msg = str(self.msg) # see logging cookbook
        if self.args:
            args = self.args
            if isinstance(args, list) and len(args) == 1:
                args = args[0]
            assert isinstance(args, dict), "Incorrect use of log.info_t() or similar method"
            msg = msg.format(**args)
        return msg

class TranslatedLogger(logging.Logger):
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func = None, extra = None, sinfo = None):
        assert extra is None, "extra not supported"
        return TranslatedLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)

    def debug_t(self, msg_string_name: str, **replacements) -> None:
        'Same as `logger.debug()` but takes the name of a translated string in place of a message.'
        self.debug(global_strings.get(msg_string_name), replacements)
    def info_t(self, msg_string_name: str, **replacements) -> None:
        'Same as `logger.info()` but takes the name of a translated string in place of a message.'
        self.info(global_strings.get(msg_string_name), replacements)
    def warn_t(self, msg_string_name: str, **replacements) -> None:
        'Deprecated - use `warning_t` instead'
        self.warn(global_strings.get(msg_string_name), replacements)
    def warning_t(self, msg_string_name: str, **replacements) -> None:
        'Same as `logger.warning()` but takes the name of a translated string in place of a message.'
        self.warning(global_strings.get(msg_string_name), replacements)
    def error_t(self, msg_string_name: str, **replacements) -> None:
        'Same as `logger.error()` but takes the name of a translated string in place of a message.'
        self.error(global_strings.get(msg_string_name), replacements)

def getLogger(name: str) -> TranslatedLogger:
    oldLoggerClass = logging.getLoggerClass()
    try:
        logging.setLoggerClass(TranslatedLogger)
        logger = logging.getLogger(name)
    finally:
        logging.setLoggerClass(oldLoggerClass)
    return logger

'''
HOW TO USE THE LOGGER FOR EASY TRANSLATED STRINGS:

1. Change the translated strings to use format strings with a field name.
(https://docs.python.org/3/library/string.html#formatstrings)

In practice, this looks like taking format strings which look like this:
    "console_finish_decomp": "Finished decompiling {} in {:.2f}s",

... and changing them to this format:
    "console_finish_decomp": "Finished decompiling {class_name} in {duration:.2f}s",

This assigns names to each element in the format string, so we can refer to them later.

If the string has no fields to be formatted, you don't do anything here.

2. Change the code to use `getLogger()` from language.py instead of logging.

If before we had this:
    import logging
    # Set up logging
    log = logging.getLogger(__name__)

Change to:
    from coilsnake.ui.language import getLogger
    # Set up logging
    log = getLogger(__name__)

3. Change invocations of `log.info` or any other logging method to `log.info_t`
and use the translated string name (such as "console_finish_decomp") instead of
getting the string value.

An example would be:
    # JSON has: "console_finish_decomp": "Finished decompiling {} in {:.2f}s"
    log.info(strings.get("console_finish_decomp").format(module_class.NAME, time.time() - start_time))

This becomes:
    # JSON has: "console_finish_decomp": "Finished decompiling {class_name} in {duration:.2f}s"
    log.info_t("console_finish_decomp", class_name=module_class.NAME, duration=time.time() - start_time)

If the string has no fields to be formatted, you call `log.info_t()` with only the
string name, and no added arguments.
    Ex: log.info_t("console_proj_already_updated")
'''
