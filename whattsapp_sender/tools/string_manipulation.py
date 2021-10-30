import re
import unidecode

def is_word_in_list(s, list_to_iterate):
    pattern = re.compile(f'\\b{s}\\b', re.IGNORECASE)
    for i in list_to_iterate:
        if pattern.search(i) is not None:
            return True
    return False


def normalize_string(col):
    return unidecode.unidecode(col).lower()


def count_times_word_in_list(s, list_to_iterate):
    pattern = re.compile(f'\\b{s}\\b', re.IGNORECASE)
    counter = 0
    for i in list_to_iterate:
        if pattern.search(i) is not None:
            counter += 1
    return counter


def is_word_repeated_in_list(s, list_to_iterate):
    return count_times_word_in_list(s, list_to_iterate) <= 1


def is_word_unique_in_list(s, list_to_iterate):
    return count_times_word_in_list(s, list_to_iterate) == 1


def match_any_target_word_in_string(s, target_words):
    for i in target_words:
        pattern = re.compile(f'\\b{i}\\b', re.IGNORECASE)
        if pattern.search(s) is not None:
            return i
    return None
