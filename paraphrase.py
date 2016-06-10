import sys
import numpy as np
from copy import deepcopy
from collections import namedtuple, defaultdict

word_type = namedtuple("word_type", "word, type")

class Paraphrase:
    def __init__(self, wt, score=0.0):
        '''
        Initialize Paraphrase object. Score indicates a weight between this Paraphrase and the target word
        of the ParaphraseSet to which it belongs.
        :param wt: word_type object
        '''
        self.word = wt.word
        self.pos = wt.type
        self.word_type = wt
        self.score = score
        self.vector = []

    def load_vec(self, vec):
        '''
        Load embedding from vector
        :param vec: np array
        '''
        self.vector = vec

    def as_string(self):
        outstring = self.word + ' ' + str(self.score) + ';'
        return outstring

    def jdefault(self):
        return self.__dict__

class ParaphraseSet:
    def __init__(self, tgt_wt, pp_dict):
        '''
        Initialize ParaphraseSet from target word_type and a dictionary of Paraphrase objects, where the key
        is the Paraphrase.word and value is Paraphrase object
        :param tgt_wt: word_type
        :param pp_dict: {word -> Paraphrase}
        '''
        self.target_word = tgt_wt.word
        self.pos = tgt_wt.type
        self.word_type = tgt_wt
        self.pp_dict = pp_dict
        self.sense_clustering = defaultdict(set)
        self.cluster_count = 0

    def magic_sense_cluster(self):
        '''
        Cluster by sense
        :return:
        '''
        self.sense_clustering = {}

    def add_sense_cluster(self, clus):
        '''
        Add sense cluster to dictionary of
        {int -> set}
        where int indicates the cluster number and the set contains strings
        :clus: list of strings
        :return:
        '''
        self.cluster_count += 1
        self.sense_clustering[self.cluster_count] = set(clus)

    def load_vecs(self, vec_dict):
        '''
        Load paraphrase vectors for all paraphrases in vec_dict
        :param vec_dict: {word -> np.array}
        :return:
        '''
        for p in self.pp_dict.itervalues():
            try:
                p.load_vec(vec_dict[p.word])
            except KeyError:
                continue

    def as_str(self):
        outline = self.target_word + '.' + self.pos + ' :: '
        for pp in self.pp_dict:
            outline += self.pp_dict[pp].as_string() + ' '
        return outline.strip()

    def filter_ppset_by_gold(self, goldfile):
        '''
        Filter paraphrase sets in ppdict to include only words that appear in gold classes
        '''
        pp_sets = deepcopy(self.pp_dict)
        goldsoln = read_gold(goldfile)[self.word_type]  # ParaphraseSet object
        filtered = set([w.word for w in goldsoln.get_paraphrase_wtypes()])

        pp_sets = {w: pp_sets[w] for w in set(pp_sets.keys()) & filtered}
        self.pp_dict = pp_sets

    def filter_sense_clustering(self, otherppset):
        '''
        Filter sense clustering to include only terms that appear as
        paraphrases of otherppset
        '''
        if type(otherppset) == set:  # can pass just a set instead
            filtered = otherppset
        else:
            filtered = set([w.word for w in otherppset.get_paraphrase_wtypes()])
        self.sense_clustering = \
            {num: (clus & filtered) for num, clus in self.sense_clustering.iteritems()}
        self.sense_clustering = {k: v for k,v in self.sense_clustering.iteritems() if len(v) > 0}
        self.cluster_count = len(self.sense_clustering)

    def get_paraphrase_wtypes(self):
        return [p.word_type for p in self.pp_dict.itervalues()]

    def jdefault(self):
        return self.__dict__

def read_gold(infile):
    '''
    Read gold standard clustering solution from infile
    :param infile:
    :return: dict (word_type -> {class -> set})
    :return: dict of {word_type -> ParaphraseSet}
    '''
    classes = {}

    for line in open(infile, 'rU'):
        entry = line.strip().split(' :: ')
        if len(entry) > 1:
            wtype = word_type(entry[0].split()[0].split('.')[0], entry[0].split()[0].split('.')[1])
            if wtype not in classes:
                classes[wtype] = ParaphraseSet(wtype, {})
                classes[wtype].cluster_count = 0
            poss_class = set([w[0] for w in [s.split() for s in entry[1].split(';')] if len(w)>0])
            if len(poss_class) > 0:
                classes[wtype].add_sense_cluster(poss_class)
    for wtype in classes:
        ppset = set().union(*[s for c,s in classes[wtype].sense_clustering.iteritems()])
        classes[wtype].pp_dict = {w: Paraphrase(word_type(w, wtype.type)) for w in ppset}
    return classes

def read_pps(infile):
    '''
    Read paraphrase lists from infile
    :param infile: str
    :return: dict {word_type -> ParaphraseSet}
    '''
    ppsets = {}
    with open(infile, 'rU') as fin:
        for line in fin:
            try:
                tgt, pps = line.split(' :: ')
            except ValueError:
                pass
            wtype = word_type(tgt.split('.')[0], tgt.split('.')[1])
            ppdict = {w: Paraphrase(word_type(w, wtype.type), score=float(s)) for w, s in
                      [(ent.split()[0], ent.split()[1]) for ent in pps.split(';')[:-1]]}
            ppsets[wtype] = ParaphraseSet(wtype, ppdict)
    return ppsets


def load_bin_vecs(filename):
    '''
    Loads 300x1 word vecs from Google word2vec in .bin format
    Thanks to word2vec google groups for this script
    :param filename: string
    :return: dict, int
    '''
    word_vecs = {}
    sys.stderr.write('Reading word2vec .bin file')
    cnt = 0
    with open(filename, 'rb') as fin:
        header = fin.readline()
        vocab_size, layer1_size = map(int, header.split())
        binary_len = np.dtype('float32').itemsize * layer1_size
        for line in xrange(vocab_size):
            word = []
            while True:
                ch = fin.read(1)
                if ch == ' ':
                    word = ''.join(word)
                    break
                if ch != '\n':
                    word.append(ch)
            word_vecs[word] = np.fromstring(fin.read(binary_len), dtype='float32')
            if cnt % 100000 == 0:
                sys.stderr.write('.')
            cnt += 1
    sys.stderr.write('\n')
    return word_vecs, layer1_size