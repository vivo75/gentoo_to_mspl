#!/usr/bin/python

import configuration

######################################################################
### TRANSLATE ATOMS INTO HASHABLE PATTERNS
######################################################################


parse_package_name = configuration.parse_package_name
pattern_create_from_atom = configuration.pattern_create_from_atom
pattern_to_save_format = configuration.pattern_to_save_format
pattern_from_save_format = configuration.pattern_from_save_format



def pattern_get_package_group(pattern): return pattern[1]

def pattern_is_package_group_specific(pattern):
	pattern_package_group = pattern_get_package_group(pattern)
	return (pattern_package_group[0] != "*") and (pattern_package_group[-1] != "*")


######################################################################
### MATCHING FUNCTIONS
######################################################################


def match_only_package_group(pattern, package_group):
	pattern_package_group = pattern[1]
	if pattern_package_group == "*/*":
		return True
	elif (pattern_package_group[0] != "*") and (pattern_package_group[-1] != "*"):
		return self.package_group == group_name
	elif pattern_package_group[0] != "*":
		pattern_subgroup = pattern_package_group[2:]
		els = package_group[1].split("/")
		return pattern_subgroup == els[-1]
	else:
		pattern_category = pattern_package_group[:-2]
		els = package_group[1].split("/")
		return pattern_category == els[-2]

def match_only_package_version(pattern, version_full, version):
	pattern_vop, pattern_version_full, pattern_version, pattern_has_star = pattern[0], pattern[2], pattern[3], pattern[4]

	if (pattern_version_full is None) or (pattern_vop is None):
		return True
	compare = compare_version(version_full, pattern_version_full)
	if pattern_vop == ">=":
		if compare < 0:
			return False
	elif pattern_vop == ">":
		if compare <= 0:
			return False
	elif pattern_vop == "~":
		if pattern_version != version:
			return False
	elif pattern_vop == "=":
		if pattern_has_star:
			if not version_full.startwith(pattern_version_full):
				return False
		else:
			if compare != 0:
				return False
	elif pattern_vop == "<=":
		if compare > 0:
			return False
	elif pattern_vop == "<":
		if compare >= 0:
			return False
	return True

def match_only_slot(pattern, slot, subslot):
	pattern_slot, pattern_subslot, pattern_sop = pattern[5], pattern[6], pattern[7]
	if pattern_slot:
		if pattern_slot != slot:
			return False
	if pattern_subslot:
		if pattern_subslot != subslot:
			return False
	return True


def match_package_path(pattern, package_name):
	package_group, version_full, version = parse_package_name(package_name)
	return match_only_package_group(pattern, package_group) and match_only_package_version(pattern, version_full, version)


def match_spl_full(pattern, spl):
	return match_only_package_group(pattern, hyportage_data.spl_get_group(spl)) and match_spl_simple(pattern, spl)

def match_spl_simple(pattern, spl):
	return match_only_package_version(pattern, hyportage_data.spl_get_version_full(spl), hyportage_data.spl_get_version(spl)) and match_only_slot(pattern, hyportage_data.spl_get_slot(spl), hyportage_data.spl_get_slot(spl))


######################################################################
### PATTERN REPOSITORY MANIPULATION
######################################################################

## repository factory

## pattern_repository_element: { pattern: (ref_count, set_of_spl) }
## pattern_repository: ( { package_group: pattern_repository_element } , pattern_repository_element )

def pattern_repository_create():
	return ({}, {}) # group specific: map group => pattern => list of matched spls, group non specific

def pattern_repository_element_create(required_use):
	return (1, { k: 1 for k in required_use }, set([]))


## pattern repository element management

def pattern_repository_element_add_required_use(pattern_repository_element, required_use):
	pattern_repository_element[0] = pattern_repository_element[0] + 1
	uses = pattern_repository_element[1]
	for use in required_use:
		if use in uses: uses[use] = uses[use] + 1
		else: uses[use] = 1
	return pattern_repository_element[0]

def pattern_repository_element_remove_required_use(pattern_repository_element, required_use):
	if pattern_repository_element[0] == 1: return 0
	pattern_repository_element[0] = pattern_repository_element[0] - 1
	uses = pattern_repository_element[1]
	for use in required_use:
		if uses[use] == 1: uses.pop(use)
		else: uses[use] = uses[use] - 1
	return pattern_repository_element[0]

def pattern_repository_element_add_spl(pattern_repository_element, spl): pattern_repository_element[2].add(spl_name)
def pattern_repository_element_remove_spl(pattern_repository_element, spl): pattern_repository_element[2].discard(spl_name)

def pattern_repository_element_get_required_use(pattern_repository_element): return pattern_repository_element[1]
def pattern_repository_element_get_spl(pattern_repository_element): return pattern_repository_element[2]

##

def pattern_repository_element_to_save_format(pattern_repository_element):
	return { 'ref_count': pattern_repository_element[0], 'required_use': pattern_repository_element[1], 'spl_names': [ hyportage_data.spl_get_name(spl) for spl in pattern_repository_element[2] ] }

def pattern_repository_element_from_save_format(save_format, mspl):
	return ( save_format['ref_count'], save_format['required_use'], set([ mspl[spl_name] for spl_name in save_format['spl_names'] ]) )

## pattern management

def pattern_repository_local_map_add_pattern(pattern_repository_element, pattern, required_use):
	if pattern in pattern_repository_element:
		pattern_repository_element_add_required_use(pattern_repository_element[pattern], required_use)
	else:
		pattern_repository_element[pattern] = pattern_repository_element_create(required_use)


def pattern_repository_add_pattern(pattern_repository, pattern, required_use):
	if pattern_is_package_group_specific(pattern):
		package_group = pattern_get_package_group(pattern)
		if package_group in pattern_repository[0]:
			pattern_repository_local_map_add_pattern(pattern_repository[0][package_group], pattern, required_use)
		else:
			res = {}
			pattern_repository_local_map_add_pattern(res, pattern, required_use)
			pattern_repository[0][package_group] = res
	else:
		pattern_repository_local_map_add_pattern(pattern_repository[1], pattern, required_use)


def pattern_repository_local_map_remove_pattern(pattern_repository_element, pattern, required_use):
	if pattern_repository_element_remove_required_use(pattern_repository_element[pattern], required_use) == 0: pattern_repository_element.pop(pattern)

def pattern_repository_remove_pattern(pattern_repository, pattern, required_use):
	if pattern_is_package_group_specific(pattern):
		pattern_repository_local_map_remove_pattern(pattern_repository[0][pattern_get_package_group(pattern)], pattern, required_use)
	else:
		pattern_repository_local_map_remove_pattern(pattern_repository[1], pattern, required_use)

## spl management

def pattern_repository_local_map_add_spl(pattern_repository_element, spl, match_function):
	for pattern, element in pattern_repository_element.iteritems():
		if match_function(pattern, spl): pattern_repository_element_add_spl(element, spl)


def pattern_repository_add_spl(pattern_repository, spl):
	package_group = hyportage_data.spl_get_group(spl)
	if package_group in pattern_repository[0]:
		pattern_repository_local_map_add_spl(pattern_repository[0][package_group], spl, match_spl_simple)
	pattern_repository_local_map_add_spl(pattern_repository[1], spl, match_spl_full)


def pattern_repository_local_map_remove_spl(pattern_repository_element, spl, match_function):
	for pattern, element in pattern_repository_element.iteritems():
		if match_function(pattern, spl): pattern_repository_element_remove_spl(element, spl)


def pattern_repository_remove_spl(pattern_repository, spl):
	package_group = hyportage_data.spl_get_group(spl)
	if package_group in pattern_repository[0]:
		pattern_repository_local_map_remove_spl(pattern_repository[0][package_group], spl, match_spl_simple)
	pattern_repository_local_map_remove_spl(pattern_repository[1], spl, match_spl_full)


## main functionalities

def pattern_repository_add(pattern_repository, spl):
	for pattern, required_use in hyportage_data.spl_get_raw_dependencies(spl):
		pattern_repository_add_pattern(pattern_repository, pattern, required_use)
	pattern_repository_add_spl(pattern_repository, spl)

def pattern_repository_update(pattern_repository, old_spl, new_spl):
	for pattern, required_use in hyportage_data.spl_get_raw_dependencies(old_spl):
		pattern_repository_remove_pattern(pattern_repository, pattern, required_use)
	for pattern, required_use in hyportage_data.spl_get_raw_dependencies(new_spl):
		pattern_repository_add_pattern(pattern_repository, pattern, required_use)

def pattern_repository_remove(pattern_repository, spl):
	for pattern, required_use in hyportage_data.spl_get_raw_dependencies(spl):
		pattern_repository_remove_pattern(pattern_repository, pattern, required_use)
	pattern_repository_remove_spl(pattern_repository, spl)


def pattern_repository_local_map_get_required_use(pattern_repository_element, pattern): return pattern_repository_element_get_required_use(pattern_repository_element[pattern])
def pattern_repository_local_map_get_spl(pattern_repository_element, pattern): return pattern_repository_element_get_spl(pattern_repository_element[pattern])

def pattern_repository_get_required_use(pattern_repository, pattern):
	if pattern_is_package_group_specific(pattern): return pattern_repository_local_map_get_required_use(pattern_repository[0][pattern_get_package_group(pattern)], pattern)
	else: return pattern_repository_local_map_get_required_use(pattern_repository[1], pattern)

def pattern_repository_get_spl(pattern_repository, pattern):
	if pattern_is_package_group_specific(pattern): return pattern_repository_local_map_get_spl(pattern_repository[0][pattern_get_package_group(pattern)], pattern)
	else: return pattern_repository_local_map_get_spl(pattern_repository[1], pattern)

##

def pattern_repository_local_map_to_save_format(pattern_repository_element):
	return [ { 'pattern': pattern_to_save_format(pattern), 'data': pattern_repository_element_to_save_format(element) } for pattern, element in pattern_repository_element.iteritems() ]
def pattern_repository_to_save_format(pattern_repository):
	return { 'package_specific': { k: pattern_repository_local_map_to_save_format(local_map) for k, local_map in pattern_repository[0].iteritems() },  'global_patterns': pattern_repository_local_map_to_save_format(pattern_repository[1]) }

def pattern_repository_local_map_from_save_format(save_format, mspl):
	return { pattern_from_save_format(save_formal_element['pattern']): pattern_repository_element_from_save_format(save_formal_element['data'], mspl)  for save_formal_element in save_format }
def pattern_repository_from_save_format(save_format, mspl):
	return ( { k: pattern_repository_local_map_from_save_format(sf_local_map, mspl) for k, sf_local_map in save_format['package_specific'].iteritems() }, pattern_repository_local_map_from_save_format(save_format['global_patterns'], mspl) )
