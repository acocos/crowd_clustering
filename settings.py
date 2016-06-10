import datetime
from boto.mturk.qualification import *

settings = {

	'ACCESS_ID' : '',  # fill in your own
	'SECRET_KEY' : '',  # fill in your own
	'HOST' : 'mechanicalturk.sandbox.amazonaws.com',  # uncomment to use the AMT sandbox
#	 'HOST' : 'mechanicalturk.amazonaws.com',  # uncomment to use production AMT
	'PRICE' : 0.25,  # price per HIT
	'REDUNDANCY' : 6,  # number of turkers who must sort each word
    'LIFETIME' : datetime.timedelta(days=7),
	'DURATION' : datetime.timedelta(minutes=10),
    'APPROVAL' : datetime.timedelta(days=1),
	'TITLE' : "Cluster Paraphrases by Sense",
	'DESCRIPTION' : "Given a set of paraphrases for a target word, group them by the sense of the target they convey.",
	'KEYWORDS' : 'Research, English, language, paraphrase, NLP',
	'QUALIFICATIONS' : [NumberHitsApprovedRequirement('GreaterThanOrEqualTo', 50), 
		PercentAssignmentsApprovedRequirement('GreaterThanOrEqualTo', 90)],
	'HIT_LAYOUT_ID' : '',  # fill in your own
    'APPROVE_FEEDBACK': 'Thank you!',
    'APPROVE_FEEDBACK_BOGALONE': 'Thank you for working on our HIT! Please note: We insert control words (false paraphrases) into each HIT as a quality control measure, and ask that workers place these control words into the red trash bin. You placed the control word %s for target word %s into a sort bin. Please place control words in the trash bin on future HITs.',
	'REJECT_BLACKLIST': 'We insert false paraphrase words (that are not paraphrases of the target) into each HIT as a control measure. We require workers to correctly identify the false paraphrases on at least %0.2f of their HITs in order to accept the work. I\'m sorry, but your accuracy in discarding false paraphrases is only %d out of %d. Please take care to cluster only words that are actual paraphrases of the target, and place false paraphrases into the trash on future HITs.',
    'REJECT_ERROR': 'We insert false paraphrase words (that are not paraphrases of the target) into each HIT as a control measure. You did not correctly place the false paraphrase %s for this HIT\'s target word %s into the trash bin. Please take care to cluster only words that are actual paraphrases of the target, and place false paraphrases into the trash on future HITs.',
    'WORKER_ACC_THRESHOLD': 0.75,  # Workers below this percent accuracy will be blacklisted
    'CLUSTER_AGR_THRESHOLD': 0.60,  # This percent of workers must agree on where a word is sorted
    'MERGE_THRESHOLD': 0.6, # This percent of workers must agree on merging two clusters
    'MAX_ATTEMPTS': 5 # Max number of rounds a word will be presented to
                      # workers for sorting. If we reach this number of rnds and
                      # the CLUSTER_AGR_THRESHOLD is not reached, then the word
                      # will be sorted into a solitary cluster.
}
