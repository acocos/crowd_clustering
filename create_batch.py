#!/usr/bin/env python

###########################################################
# create_batch.py
#
# Given a directory of paraphrase set JSON files, generate
# a new HIT batch .csv for each file in directory.
#
# - For each paraphrase set, choose N (default 10) words not
#   yet clustered as new words, and add to HIT along with
#   1-2 words from each existing class
# - Also add one 'bogus' word per HIT
#
###########################################################

import optparse
import time
import random
import json
import csv
import os
from settings import settings
from boto.mturk import connection
from boto.mturk import layoutparam
from boto.mturk.qualification import Qualifications
from xml.sax.saxutils import escape

def escape_string(s) : return escape(s.replace('"', "''"))

def jdefault(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj.__dict__

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

if __name__ == "__main__":
    ## Get command line arguments
    optparser = optparse.OptionParser()
    optparser.add_option("-j", "--jsondir", type="string", default='hit_data/json', dest="jsondir", help="Directory containing paraphrase set json files")

    optparser.add_option("-o", "--outdir", type="string", default='hit_data/batch')
    optparser.add_option("-n", "--n", type="int", default=10, dest="n", help="Number of unsorted words in each HIT")
    optparser.add_option("-b", "--bogusfile", type="string", default="hit_data/boguslist", dest="bogusfile", help="File containing grab bag of bogus words, one per line")

    optparser.add_option("-m", "--mode", type="string", default="manual", dest="mode", help="Mode for uploading and downloading results ('manual' or 'auto')")

    (opts, _) = optparser.parse_args()

    boguswords = set([w.strip() for w in
                      open(opts.bogusfile, 'rU').readlines()])

    ppfiles = [os.path.join(opts.jsondir,f) for f in
               os.listdir(opts.jsondir) if f[0] != '.']

    hits = []
    random.seed(314)
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    all_files_complete = True

    for file in ppfiles:
        with open(file, 'rU') as fin:
            pps = byteify(json.load(fin))

        ## Check to make sure this word is not already in an iteration or finished
        if pps['lock'] == 1 or pps['complete'] == 2:
            continue
        else:
            all_files_complete = False

            ## Choose appropriate bogus term
            ok = False
            while not ok:
                b = random.sample(boguswords, 1)[0]
                validate = raw_input("Bogus for "+pps['tgt']+": "+b+". OK? (y/n)")
                if validate == 'y':
                    ok = True
                    pps['bogusword'] = b

            ## Pick random grab bag of unsorted words
            tosort = set([w for w,d in
                          pps['ppset']['pp_dict'].iteritems()
                          if d['state'] in ['attempted','none']])
            randtosort = list(tosort)
            random.shuffle(randtosort)
            pps['unsorted'] = randtosort[:min(opts.n, len(randtosort))]
            for pp in pps['unsorted']:
                pps['ppset']['pp_dict'][pp]['state'] = 'in_progress'

            ## Choose a random sample of the crowd_gold to start off the hit
            pps['crowdstarter'] = {int(k): random.sample(v, min(6, len(v))) for k,v in
                                   pps['crowd_gold']['sense_clustering'].iteritems()}
            pps['sorted'] = pps['crowdstarter'].values()
            seeded = len(pps['sorted']) > 0

            ## Update parameters with batch information
            pps['latest_timestamp'] = timestamp
            pps['num_anno'] = settings['REDUNDANCY']


            ## Lock this target until we finish the iteration
            pps['lock'] = 1

            ## Compile HIT data
            tgt = pps['tgt']
            pos = pps['pos']
            bogus = pps['bogusword']
            unsorted = str(pps['unsorted'])
            sorted = str(pps['sorted'])
            starter = json.dumps(pps['crowdstarter'], default=jdefault)
            num_classes = str(pps['crowd_gold']['cluster_count'])
            num_anno = pps['num_anno']
            latest_timestamp = pps['latest_timestamp']
            hits.append({'tgt':tgt,
                         'pos':pos,
                         'bogus':bogus,
                         'unsorted':unsorted,
                         'sorted':sorted,
                         'seeded':seeded,
                         'num_classes':num_classes,
                         'num_anno':num_anno,
                         'latest_timestamp':latest_timestamp,
                         'crowdstarter':starter})

            ## Update json file
            with open(file, 'w') as fout2:
                print >> fout2, json.dumps(pps, indent=2, default=jdefault)

    if all_files_complete:
        print 'All finished clustering this group of json files. Thanks.'
    else:
        ## Write to new batch file
        outfile = os.path.join(opts.outdir, 'batch_'+timestamp+'.csv')
        print 'Manually writing batch to csv file', outfile+'...',
        with open(outfile, 'w') as fout:
            headers = ['tgt','pos','bogus','unsorted','sorted','seeded',
                       'num_classes','num_anno','latest_timestamp','crowdstarter']
            writer = csv.DictWriter(fout, fieldnames=headers)
            writer.writeheader()
            writer.writerows(hits)
            print 'Done'
        ## optionally auto-upload to AMT
        if opts.mode=='auto':
            print 'Auto-uploading HITs to', settings['HOST']
            conn = connection.MTurkConnection(
                aws_access_key_id=settings['ACCESS_ID'],
                aws_secret_access_key=settings['SECRET_KEY'],
                host=settings['HOST'])
            qualifications = Qualifications()
            for q in settings['QUALIFICATIONS'] : qualifications.add(q)

            for i, h in enumerate(hits):
                print 'posting HIT %d of %d'%(i, len(hits))
                params = [layoutparam.LayoutParameter(k,v) for k,v in h.iteritems()]
                result = conn.create_hit(hit_layout=settings['HIT_LAYOUT_ID'], qualifications=qualifications,
                                         max_assignments=settings['REDUNDANCY'], title=settings['TITLE'],
                                         description=settings['DESCRIPTION'], keywords=settings['KEYWORDS'],
                                         duration=settings['DURATION'], reward=settings['PRICE'],
                                         layout_params=layoutparam.LayoutParameters(params),
                                         lifetime=settings['LIFETIME'], approval_delay=settings['APPROVAL'],
                                         annotation='paraclust_'+timestamp)
            print 'Done. Now go to https://workersandbox.mturk.com/ to do the HITs.'

