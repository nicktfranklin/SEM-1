from encoding_schemes import encode_causal_attention, encode_trait_addition, encode_trait_boolean_binding
import random

# lower threshold to introduce noise in story construction - currently constant across all transitions
DECISION_THRESHOLD = 1.0

def encode_scene(context, encoding, subj, action, obj, subject_property = None, action_property = None, object_property = None):
	if encoding == 'causal_attention':
		scene, generating = encode_causal_attention(subj, action, obj, context, subject_property = subject_property, action_property = action_property, object_property = object_property)
	elif encoding == 'trait_addition':
		scene, generating = encode_trait_addition(subj, action, obj, context)
	elif encoding == 'trait_boolean_binding':
		scene, generating = encode_trait_boolean_binding(subj, action, obj, context)
	return scene, generating

def transition(decision, options):
	if decision:
		threshold = DECISION_THRESHOLD
	else:
		threshold = 1 - DECISION_THRESHOLD
	if random.random() < threshold:
		return options[0]
	else:
		return options[1]

def enter_coffeeshop(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p1'], context.verbs['enter'], context.nouns['coffeeshop'], subject_property = 'thirsty')
	event.append(scene)
	generating_fillers.append(generating)
	return transition(variables['p1']['properties']['thirsty'], [walk_to_front, walk_to_back])

def walk_to_back(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p1'], context.verbs['obey'], context.nouns['line'], subject_property = 'impatient')
	event.append(scene)
	generating_fillers.append(generating)
	return transition(variables['p1']['properties']['impatient'], [walk_to_front, buy_coffee])

def walk_to_front(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p1'], context.verbs['cut'], variables['p2'], object_property = 'violent')
	event.append(scene)
	generating_fillers.append(generating)
	return transition(variables['p2']['properties']['violent'], [confront, buy_coffee])

def confront(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p2'], context.verbs['confront'], variables['p1'], object_property = 'violent')
	event.append(scene)
	generating_fillers.append(generating)
	return transition(variables['p1']['properties']['violent'], [hit, apologize])

def apologize(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p1'], context.verbs['apologize'], variables['p2'])
	event.append(scene)
	generating_fillers.append(generating)
	return transition(True, [buy_coffee])

def hit(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p1'], context.verbs['hit'], variables['p2'])
	event.append(scene)
	generating_fillers.append(generating)
	return transition(True, [leave_coffeeshop])

def buy_coffee(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p1'], context.verbs['buy'], context.nouns['coffee'])
	event.append(scene)
	generating_fillers.append(generating)
	return transition(True, [leave_coffeeshop])

def leave_coffeeshop(event, generating_fillers, variables, context, encoding):
	scene, generating = encode_scene(context, encoding, variables['p1'], context.verbs['leave'], context.nouns['coffeeshop'])
	event.append(scene)
	generating_fillers.append(generating)
	return None