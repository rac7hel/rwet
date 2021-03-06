#!/usr/bin/env python

import argparse
import heapq
import json
import numpy
import operator
import random
import re
import sklearn.preprocessing
import sys


HTML_HEADER = u'''<html>
  <head>
    <meta charset="utf-8">
    <style type="text/css">
      body {
        margin-left: 3em;
        margin-top: 3em;
      }
      table {
        border-collapse: collapse;
      }
      td.item {
        color: white;
        font-weight: bold;
      }
    </style>
  </head>
  <body>'''


HTML_FOOTER = u'''  </body>
</html>
'''


class Words(object):
  """A word vector database.
  """

  def __init__(self, probability, words, vectors):
    """Saves the words and word vectors.
    """
    self.probability = probability
    self.words = words
    self.word_set = set(words)
    self.vectors = vectors

  def sanitize(self, word):
    """Strips neighboring and intermeidate punctuation characters and turns the word to lowercase.
    """
    return re.sub(u'[^\\w\']', u'', word.lower())

  def choose(self, choices):
    """Chooses a random word with an approximately geometric distribution, prioritizing earlier
    words.
    """
    index = min(numpy.random.geometric(self.probability) - 1, len(choices) - 1)
    return choices[index]

  def word_to_vector(self, word):
    """Translates a word into its vector form.
    """
    word = self.sanitize(word)
    if word not in self.word_set:
      return numpy.zeros(self.vectors.shape[1])
    index = self.words.index(word)
    return self.vectors[index]

  def words_to_vector(self, words):
    """Translates words into their word vectors, sums them and returns the normalized result.
    """
    words = map(lambda word: self.sanitize(word), words)
    indices = [self.words.index(word) for word in words if word in self.word_set]
    result = self.vectors[indices].sum(axis = 0)
    length = numpy.linalg.norm(result)
    return result / length if length > 0 else result

  def nearest_n_words_to_vector(self, n, vector):
    """Queries for the n words with the most similar word vectors to vector using the dot product.
    """
    dot_products = numpy.dot(self.vectors, vector)
    indices = [t[0] for t in heapq.nlargest(n, enumerate(dot_products), operator.itemgetter(1))]
    return map(lambda index: self.words[index], indices)


def read_vocabulary(filename):
  """Reads a vocabulary text file, with one word per line, and returns the words as a list.
  """
  result = list()
  with open(filename) as file:
    for line in file:
      result.append(line.strip().decode('utf8'))
  return result


def read_vectors(filename):
  """Reads a numpy 2d array file and returns the array.
  """
  with open(filename) as file:
    vectors = numpy.load(file)
  return vectors


def html_intro(line0, line1):
  """HTML template for the original couplet at the beginning of the document.
  """
  return u'    <p>%s<br />\n    %s</p>' % (' '.join(line0), ' '.join(line1))


def main():
  commands = argparse.ArgumentParser(description = 'Find the nearest words to sums of pairs of '
      'words from a couplet of an original text.')
  commands.add_argument('--number', type = int, default = 10, help = 'the number of similar words')
  commands.add_argument('--vocabulary', required = True, help = 'the input vocabulary text file')
  commands.add_argument('--vectors', required = True, help = 'the input numpy vector binary file')
  commands.add_argument('-p', '--probability', type = float, default = 0.3,
      help = 'the probability parameter for the geometric distribution for choosing words')
  commands.add_argument('--html', action = 'store_true', help = 'whether to output html')
  arguments = commands.parse_args()

  word_vectors = Words(arguments.probability,
      read_vocabulary(arguments.vocabulary), read_vectors(arguments.vectors))

  # read and split two lines
  line0 = sys.stdin.readline().strip().decode('utf8').split()
  line1 = sys.stdin.readline().strip().decode('utf8').split()

  if arguments.html:

    # print an HTML output format with colors symbolizing degree of association between the depicted
    # word and the sum of the vectors of the two original words
    print HTML_HEADER
    print html_intro(line0, line1)
    print u'    <table>'
    print (u'      <tr><td />%s</tr>' % ''.join(
        map(lambda item: u'<td>%s</td>' % item, line0))).encode('utf8')
    for word1 in line1:
      words = list()
      for word0 in line0:
        pair_vector = word_vectors.words_to_vector([word0, word1])
        choice = word_vectors.choose(
            word_vectors.nearest_n_words_to_vector(arguments.number, pair_vector)[2:])
        choice_vector = word_vectors.word_to_vector(choice)
        agreement = int(255 - 255 * numpy.dot(pair_vector, choice_vector))
        words.append((choice, agreement))
      entries = ''.join(
          map(lambda item: u'<td class="item" style="background-color:rgb(%s,%s,%s);%s">%s</td>' % (
              item[1], item[1], item[1], u'' if item[1] < 235 else u'color:black', item[0]), words))
      print (u'      <tr><td>%s</td>%s</tr>' % (word1, entries)).encode('utf8')
    print u'    </table>'
    print HTML_FOOTER
  else:

    # print a text formatted poem
    print u' '.join(line0)
    print u' '.join(line1)
    print

    print u'\t',
    for word0 in line0:
      print word0,
    for word1 in line1:
      print
      print u'%s\t' % word1,
      for word0 in line0:
        print word_vectors.choose(word_vectors.nearest_n_words_to_vector(arguments.number,
            word_vectors.words_to_vector([word0, word1]))[2:]),


if '__main__' == __name__:
  main()
