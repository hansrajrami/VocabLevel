from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
import os
import codecs
from collections import Counter
import operator
import enchant
from nltk.metrics import edit_distance
import csv
import random
from nltk.corpus import wordnet

class SpellCorrection(object):
    def __init__(self, dict_name='en-US', max_dist=2):
        self.spell_dict = enchant.Dict(dict_name)
        self.max_dist = max_dist
    def replace(self, word): # If the edit distance is greater than max_dist, it returns None
        if self.spell_dict.check(word):
            return word
        suggestions = self.spell_dict.suggest(word)
        if suggestions and edit_distance(word, suggestions[0]) <= self.max_dist:
            return suggestions[0]
        else:
            return None
        
### To Do: we can consider words with different POS as different words
        
if os.path.exists('word_list.csv'):
    with open('word_list.csv', 'r') as f:
        csv_in = csv.reader(f)
        sorted_words = [row for row in csv_in]
else:
    # extract words
    # a. Remove proper nouns
    # b. Keep only alphabetic words
    # c. Correct misspellings
    # d. Lemmatize words
    # e. Lower-case words
    words = []
    for subdir, _, files in os.walk('Subtitles/'):
        for file in files:
            f = codecs.open(os.path.join(subdir, file), 'r', 'latin-1')
            tagged_sent = pos_tag(word_tokenize(f.read()))
            words.extend([word for word,pos in tagged_sent if pos != 'NNP']) 
    
    replacer = SpellCorrection()
    lemmatizer = WordNetLemmatizer()
    filtered = []
    for w in words:
        if str.isalpha(w):
            modif_word = replacer.replace(w)
            if modif_word and str.isalpha(modif_word):
                mw = modif_word.lower()
                # Lemmatize as 'verb' and 'noun' and hold whichever that makes the word different
                # (Need more investigation for adjectives and adverbs. Better to use the real POS of the word)
                mwv = lemmatizer.lemmatize(mw, pos='v') # verb lemma
                if mwv != mw:
                    filtered.append(mwv)
                else:
                    filtered.append(lemmatizer.lemmatize(mw)) # noun lemma 

    # count words and sort according to their frequencies
    sorted_words = sorted(Counter(filtered).items(), key=operator.itemgetter(1), reverse=True)

    # save the word lists
    with open('word_list.csv','w') as f:
        csv_out = csv.writer(f)
        for row in sorted_words:
            csv_out.writerow(row)
            
# Multiple-choice check: when the user claims to know a word, show its WordNet definition
# among a few definitions of other random words, and only count the word as known if the
# right one is picked.
NUM_CHOICES = 4

def definition(word):
    synsets = wordnet.synsets(word)
    return synsets[0].definition() if synsets else None

def knows_word(word, words):
    correct = definition(word)
    if correct is None:
        return True # no definition available, so we trust the user's answer
    distractors = set()
    while len(distractors) < NUM_CHOICES - 1:
        d = definition(random.choice(words)[0])
        if d and d != correct:
            distractors.add(d)
    options = list(distractors) + [correct]
    random.shuffle(options)
    print('Which one is the meaning of "%s"?' % word)
    for i, o in enumerate(options):
        print('  %s) %s' % ('abcdefghij'[i], o))
    answer = input().strip().lower()
    return answer != '' and 'abcdefghij'.find(answer[0]) == options.index(correct)

# interact with user to find his/her vocabulary level
start = 0
end = len(sorted_words)-1
while start <= end:
    pos = int((start+end)/2)
    print('Do you know the meaning of "%s" (y,n)?' % sorted_words[pos][0])
    if input()=='n' or not knows_word(sorted_words[pos][0], sorted_words):
        end = pos - 1
        pos -= 1 # position of the last word that you know
    else:
        start = pos + 1
# pos: the position where the user does not knows its meaning and the meaning of the words after that

total = len(sorted_words)
pos += 1
print("************************RESULTS***********************")
print("You approximately knows %d words out of %d (%%%.1f)" %(pos,total,pos*100/total))
print("******************************************************")

# We can give the separate lists of words that the user knows and does not know
