import re

# Helper function to check if a character is a digit
def is_digit(char):
    return re.match(r'\d', char) is not None

def text_with_space(current, next, space, numbers_space):
    if space or (numbers_space and is_digit(current[-1]) and is_digit(next[0])):
        return " " + next
    else:
        return next