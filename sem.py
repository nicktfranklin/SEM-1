import numpy as np
import copy

from event_schemas import BasicRNN

def log_normal_likelihood(x, mu, sigma):
    return np.subtract(-0.5 *((np.subtract(x, mu))/sigma)**2, np.log((np.sqrt(2 * np.pi) * sigma)))

def logsumexp(x):
    if len(x) == 0:
        return 0
    y = np.max(x)
    x = x - y
    s = y + np.log(sum(np.exp(x)))
    return s

def sem_init(opts):
    sem = {}

    # initialize event info
    sem['event_counts'] = np.zeros(opts['max_events'])
    sem['last_event'] = -1
    sem['current_event_scenes'] = []

    # initialize list of RNN structures for each event
    sem['theta'] = []
    for i in range(opts['max_events']):
        sem['theta'].append(opts['transition'](opts['d']))
    return sem

def sem_options(f, d, max_events = 20, lambd = 10.0, alpha = 0.1, beta = 1.0, eta = 0.01, model = BasicRNN):
    opts = {}

    opts['f'] = f
    opts['d'] = d 
    opts['max_events'] = max_events
    opts['lambd'] = lambd
    opts['alpha'] = alpha
    opts['beta'] = beta
    opts['eta'] = eta
    opts['transition'] = model
    
    return opts
    
def sem_segment(states, sem, opts):
    d = opts['d']
    k = opts['max_events']
    
    # return all event ids and all predictions under the last event id
    all_events = []
    all_predictions = []

    # default creation of first event and assignment of first scene
    sem['current_event_scenes'].append(states[0])
    sem['last_event'] = 0
    sem['event_counts'][0] = 1
    all_events.append(0)

    n = len(states)
    for time in range(1, n):
        # create scrp prior from event counts
        prior = copy.copy(sem['event_counts'])        
        empty = np.where(prior == 0)[0]
        # new event creation parameter
        if len(empty) > 0:
            prior[empty[0]] = opts['alpha']
        # stickiness parameter
        if sem['last_event'] != -1:
            prior[sem['last_event']] += opts['lambd']

        predictions = [[] for i in range(k)]
        likelihood = np.zeros(k)
        active = np.nonzero(prior)[0]
        for i in active:   
            if i == sem['last_event'] and sem['theta'][i].is_recurrent():     
                # feed entire event sequence to RNN for current event to predict on the sequence
                predictions[i] = sem['theta'][i].predict(sem['current_event_scenes'])
            else:
                # feed only last scene and current scene to RNN for inactive events to predict likelihood of event break
                predictions[i] = sem['theta'][i].predict([sem['current_event_scenes'][-1]])
            likelihood[i] = sum(log_normal_likelihood(states[time], predictions[i], opts['beta']))

        # construct posterior from prior and likelihood to choose event at current time
        posteriors = np.zeros(k)
        p = np.log(prior[active]) + likelihood[active]
        post = np.exp(p-logsumexp(p))    
        posteriors[active] = post
        posteriors[np.isnan(posteriors)] = 0

        chosenevent = np.where(posteriors == max(posteriors))[0][0]

        if chosenevent != sem['last_event']:
            if sem['theta'][sem['last_event']].is_recurrent():
                # on event boundaries train the event RNN using the entire observed sequence
                sem['theta'][sem['last_event']].train_recurrent(sem['current_event_scenes']) 
            sem['current_event_scenes'] = [states[time - 1], states[time]]
        else:
            if not sem['theta'][sem['last_event']].is_recurrent():
                sem['theta'][sem['last_event']].update([states[time - 1]], [states[time]]) 
            sem['current_event_scenes'].append(states[time])
        
        # update scene prediction and event prediction lists
        all_predictions.append(predictions[sem['last_event']])
        all_events.append(chosenevent)
        sem['last_event'] = chosenevent
        sem['event_counts'][chosenevent] += 1

    # train current RNN one more time with leftover scenes
    if sem['theta'][sem['last_event']].is_recurrent():
        sem['theta'][sem['last_event']].train_recurrent(sem['current_event_scenes'])
    return all_events, all_predictions