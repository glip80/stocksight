
def find_words(text_array, search):
    """Find exact words"""
    for text in text_array:
        if text in search:
            return True
    return False

sentence = "Report: Broadcom's biggest customer  Apple  is going to stop buying a key part"
ingored = ['stock', 'prediction']

v = find_words(ingored, sentence)
print(v)

find_words(['stock', 'prediction'], "Report: Broadcom's biggest customer  Apple  is going to stop buying a key part")