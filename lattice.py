# A representation of possible mappings from a word's spelling to some other domain (pronunciation or syllabification).

NO_PATHS_FOUND = 999
SEARCHED_TOO_LONG = 998
WORD_TOO_SHORT = 997
ERRORS = { 
999: 'NO_PATHS_FOUND', \
998: 'SEARCHED_TOO_LONG', \
}

class Lattice:
	# Nodes are endpoints within the target word with a set location and candidate phoneme.
	class Node:
		def __init__(self, matched_letter, phoneme, index):
			self.matched_letter = matched_letter
			self.phoneme = phoneme
			self.index = index
			self.from_arcs = [] 
			self.to_arcs = []
			self.visited = False
		def __hash__(self):
			return hash((self.matched_letter, self.phoneme, self.index))
		def __eq__(self, other):
			if not isinstance(other, type(self)):
				return NotImplemented
			return self.matched_letter == other.matched_letter \
			and self.phoneme == other.phoneme \
			and self.index == other.index
		def __ne__(self, other):
			return not self.__eq__(other)
		def __str__(self):
			return '{}'.format(self.phoneme)
	# Arcs span nodes with phonemes between them (or nothing, if the two nodes are bigrams.)
	class Arc:
		def __init__(self, intermediate_phonemes, from_node, to_node):
			self.from_node = from_node
			self.intermediate_phonemes = intermediate_phonemes
			self.to_node = to_node
			self.count = 1
			# Used to assemble what M&D call "path structure."
			self.structure_component = (to_node.index - from_node.index)
		def __eq__(self, other):
			if not isinstance(other, type(self)):
				return NotImplemented
			return self.from_node == other.from_node \
			and self.intermediate_phonemes == other.intermediate_phonemes \
			and self.to_node == other.to_node
		def __ne__(self, other):
			return not self.__eq__(other)
		def __str__(self):
			return '[{}:{}]'.format(self.intermediate_phonemes, self.count)
		def __hash__(self):
			return hash((self.from_node, self.intermediate_phonemes, self.to_node))
		# Accepts a list of nodes.
		# Returns whether this arc's endpoints exist within that list.
		def contains(self, list_of_nodes):
			return (self.from_node in list_of_nodes) or (self.to_node in list_of_nodes)				

	class Candidate:
		# Initialize candidate as empty or as shallow copy.
		def __init__(self, other=None):
			# Init as empty.
			if other == None:
				self.path = [] # Includes all nodes.
				self.arcs = [] # Arcs only.
				# path_strings need to remain fluid during the breadth-first search, because 
				# to "pop" an arc involves the removal of any number of intermediate phonemes.
				self.path_strings = []
				# path_strings get merged into pronunciation after path is completed.
				self.pronunciation = ''
				self.arc_count_sum = 0
				self.arc_count_product = 1
				self.sum_of_products = 0
				self.frequency_of_same_pronunciation = 1 # There's at least one with this pronunciation -- itself.
				self.length = 0
				self.path_structure_standard_deviation = 0
				self.weakest_link = 0
				self.number_of_different_symbols = 0
				return
			# Init as shallow copy.
			# Path and path string.
			self.path = other.path[:]
			self.arcs = other.arcs[:]
			self.path_strings = other.path_strings[:]
			self.pronunciation = other.pronunciation
			# Heuristics.
			self.length = other.length
			self.arc_count_sum = other.arc_count_sum
			self.arc_count_product = other.arc_count_product
			self.sum_of_products = other.sum_of_products
			self.frequency_of_same_pronunciation = other.frequency_of_same_pronunciation
			self.path_structure_standard_deviation = other.path_structure_standard_deviation
			self.weakest_link = other.weakest_link
			self.number_of_different_symbols = 0
		# Finalizes path_strings (only run this when a path is complete.)
		def solidify(self):
			self.pronunciation = ''.join(self.path_strings)
			
		def __str__(self):
			return self.pronunciation
		def __hash__(self):
			return hash(tuple([arc for arc in self.arcs]))
		# Append arc to this candidate with its nodes and heuristics.
		def update(self, parent, arc):
			# Update path and path string.
			self.path += [arc.from_node, arc]
			self.arcs += [arc]
			self.path_strings += [arc.from_node.phoneme, arc.intermediate_phonemes]
			# Update heuristics.
			# Ignore start node and end node's counts. Those arcs would only count how many times a word starts with
			# the word's start letter and ends with the word's end letter.
			self.arc_count_sum += arc.count if not arc.contains([parent.START_NODE, parent.END_NODE]) else 0
			self.length += 1
			# If it's the start, we don't need the first node, which merely represents the start node.
			if len(self.arcs) == 1:
				self.path = self.path[1:]
				self.path_strings = self.path_strings[1:]

		def pop(self, parent):
			# Decrement from heuristics.
			removed = self.arcs[-1]
			self.arc_count_sum -= removed.count if not removed.contains([parent.START_NODE, parent.END_NODE]) else 0
			self.length -= 1
			# Pop from path and path string.
			self.arcs = self.arcs[:-1]
			self.path = self.path[:-2] # path and path_strings had [node, arc, node], three references to remove.
			self.path_strings = self.path_strings[:-2]

	# Initialize pronunciation lattice.
	def __init__(self, letters):
		self.letters = letters

		self.nodes = {}
		self.arcs = {}

		self.START_NODE = self.Node('', '', -1)
		self.END_NODE = self.Node('', '', len(letters))
		self.nodes[hash(('', '', -1))] = self.START_NODE
		self.nodes[hash(('', '', len(letters)))] = self.END_NODE

		self.unrepresented_bigrams = set()
	# String interpretation of pronunciation lattice (unlinked. use print() for all linked pronunciations.)
	def __str__(self):
		s = ''
		for arc in self.arcs:
			inter_letters = ''
			if arc.from_node.index != None and arc.to_node.index != None:
				inter_letters = self.letters[arc.from_node.index + 1:arc.to_node.index]
				inter_letters = '<' + inter_letters + '>' if inter_letters != '' else ''

			key = '{}{}{}'.format(arc.from_node.matched_letter, inter_letters, arc.to_node.matched_letter)
			val = '{}{}{}'.format(arc.from_node.phoneme, arc.intermediate_phonemes, arc.to_node.phoneme)

			s += '{} [{}, {}] is pronounced {}: {} times\n'.format(key, arc.from_node.index, arc.to_node.index, val, arc.count)
		return s
	# For debugging.
	def print_nodes(self):
		for node in self.nodes:
			print('Node {} has {} arcs into it and {} arcs out of it.'.format(node.matched_letter + node.phoneme + str(node.index), len(node.from_arcs), len(node.to_arcs)))
	# Lists all paths via breadth-first search.
	def find_all_paths(self, verbose = False):
		import sys
		min_length = sys.maxsize
		
		# Link unrepresented bigrams.
		# fixes the silence problem.
		self.link_unrepresented()
		# While helpful, this will not suffice. An extant bigram STILL
		# may not have any paths that lead into it if phonemes don't match.
		# We will keep track of furthest_index and attempt to manually dig further
		# if no paths exist.
		furthest_index = 0

		candidates = []

		overflow = False
		util_call_count = 0
		def util(u, d, candidate_buffer):
			nonlocal overflow
			nonlocal min_length
			nonlocal furthest_index
			nonlocal util_call_count
			if util_call_count != 0 and util_call_count%2500000 == 0:
				print('Recurred {} times. {} candidates found.'.format(util_call_count, len(candidates)))
			util_call_count += 1
			if util_call_count > 25000000:
				overflow = True
				return
			u.visited = True
			furthest_index = u.index if u.index > furthest_index else furthest_index
			if u == d:
				complete_candidate = self.Candidate(candidate_buffer)
				complete_candidate.solidify()
				candidates.append(complete_candidate) # Append a copy.
				if verbose:
					print(complete_candidate.pronunciation, complete_candidate.arc_count_product)
				if candidate_buffer.length < min_length:
					min_length = candidate_buffer.length
			elif candidate_buffer.length < min_length:
				for arc in u.to_arcs:
					v = arc.to_node
					candidate_buffer.update(self, arc) # Append arc to buffer with its nodes and heuristics. 
					if v.visited == False:
						util(v, d, candidate_buffer) # Recur over successor node.
					candidate_buffer.pop(self) # Wipe candidate buffer.
			u.visited = False # Allow future revisiting.
		last_furthest_index = -1
		while furthest_index < len(self.letters) and not overflow:
			if furthest_index == last_furthest_index:
				print('Progress has stopped.')
				return NO_PATHS_FOUND
			# Set visited to False for all.
			for node in self.nodes.values():
				node.visited = False
			candidate_buffer = self.Candidate()
			# Begin breadth-first search listing all paths.
			util(self.START_NODE, self.END_NODE, candidate_buffer)
			if len(candidates) > 0:
				continue
			print('Warning. No paths were found. Furthest index: {}'.format(furthest_index))
			# Patch every gap associated with the pair of letters beginning at that index.
			self.link_silences(furthest_index)
		if overflow:
			print('Path threshold reached. Skipping.')
			return SEARCHED_TOO_LONG
		return candidates

	# Count identical pronunciations generating
	# 1) "the maximum frequency of the same pronunciation (FSP) within the shortest paths," and
	# 2) "the sum of products over...multiple paths [of] identical pronunciations"
	def get_frequencies_by_pronunciation(self, candidate_list):
		# Map unique pronunciations to the number of times that pronunciation occurs.
		pronunciation_to_repeat_count = {}
		# Map unique pronunciations to the sum of (products of each occurrence's arcs).
		pronunciation_to_sum_of_product = {}
		for i, candidate in enumerate(candidate_list):
			# Iterate frequency.
			pronunciation_to_repeat_count[candidate.pronunciation] = pronunciation_to_repeat_count.get(candidate.pronunciation, 0) + 1
			# Add sum of products.
			pronunciation_to_sum_of_product[candidate.pronunciation] = \
				pronunciation_to_sum_of_product.get(candidate.pronunciation, 0) + candidate.arc_count_product
		return pronunciation_to_repeat_count, pronunciation_to_sum_of_product

	# These help break ties. See page 9 of "Can syllabification improve pronunciation by analogy of English?"
	def compute_heuristics(self, candidates):
		import math
		import statistics
		from operator import attrgetter
		# 1. Maximum arc count product
		for i in range(len(candidates)):
			candidates[i].arc_count_product = math.prod([arc.count for arc in candidates[i].arcs])

		pronunciation_to_repeat_count, pronunciation_to_sum_of_product = self.get_frequencies_by_pronunciation(candidates)

		other_candidates_symbols = ''
		for i in range(len(candidates)):
			pronunciation = candidates[i].pronunciation
			# 2. Minimum standard deviation.
			candidates[i].path_structure_standard_deviation = statistics.stdev([arc.structure_component for arc in candidates[i].arcs])
			#print('{}: {}'.format([arc.intermediate_phonemes for arc in self.arcs], self.path_structure_standard_deviation))

			# 3. Maximum frequency of the same pronunciation 
			candidates[i].frequency_of_same_pronunciation = pronunciation_to_repeat_count[pronunciation]
			# (We'll also do sum of products here, too, even though it's not one of M&D's 5.)
			candidates[i].sum_of_products = pronunciation_to_sum_of_product[pronunciation]

			# 4. Minimum number of different symbols per candidate.
			number_of_different_symbols = 0
			# Isolate current candidate from others.
			other_candidates = candidates[:i] + candidates[i + 1:]
			# Compare char at each index of this candidate to that of every competitor, counting differences.
			for other_candidate in other_candidates:
				for j, ch in enumerate(pronunciation):
					number_of_different_symbols += 1 if ch != other_candidate.pronunciation[j] else 0
			candidates[i].number_of_different_symbols = number_of_different_symbols
			#print('{} different symbols in {} versus {}'.format(number_of_different_symbols, candidates[i], other_candidates_symbols))

			# 5. Maximum weakest link. (The weakest link is the minimum arc count)
			candidates[i].weakest_link = min([arc.count for arc in candidates[i].arcs if not arc.contains([self.START_NODE, self.END_NODE])])

		#print(['{}: {}'.format(arc.from_node.matched_letter + arc.intermediate_phonemes + arc.to_node.matched_letter, arc.count) for arc in self.arcs])

	# Ranks candidates by the five heuristics. 
	def rank_by_heuristics(self, candidates):
		import itertools
		# Rank according to these five heuristics and orders.
		heuristic = ['arc_count_product', \
			'path_structure_standard_deviation', \
			'frequency_of_same_pronunciation', \
			'number_of_different_symbols', \
			'weakest_link']
		descending = [True, False, True, False, True]

		results = tuple([self.rank_by_heuristic(candidates, heuristic[i], \
			descending=descending[i], verbose=False) for i in range(len(heuristic))])
		# We pass in heuristic[i] for titling print statements only.
		results = tuple([self.rank_to_score(leaderboard, heuristic[i]) for i, leaderboard in enumerate(results)])

		labeled_results = {}
		# Rank fusion.
		# There are 31 possible rank fusions, i.e.:
		# 00001, 00011, 00101, ..., 10111, 01111, 11111
		strategies = list(itertools.product([0, 1], repeat=5))
		# Permute through every way of scoring.
		for strategy in strategies:
			# Ignore 00000.
			if not any(strategy):
				continue
			label = '' # A string representation of this fusion.
			# Flush dict for this current fusion method.
			totals = {}
			# Each bit maps onto a results column, multiplied by the bit.
			for i, bit in enumerate(strategy):
				label += str(bit)
				if not bit:
					continue
				column = results[i]
				for candidate in candidates:
					# Multiply by points received by this strategy, or 1 if this strategy is not included
					# (though technically that triggers continue above.)
					totals[candidate] = totals.get(candidate, 1) * (column[candidate] * bit + (1 - bit))
			# Now that every column has been added, save the maximum.
			best = max(totals, key=totals.get)
			best_val = totals[best]
			#print(label)
			#print('{}: {}'.format(best.pronunciation, best_val))
			labeled_results[label] = best
		return labeled_results

	# The best rank is 1. Then 2, then 3, and so on.
	# Multiple candidates can share the same rank, naturally.
	def rank_by_heuristic(self, candidates, attribute, descending=True, verbose=False):
		from operator import attrgetter
		candidates.sort(key=attrgetter(attribute), reverse=descending)
		# Map candidates to how well they did (lower is better.)
		candidate_to_rank_map = {}
		# Sort candidates by attribute.
		prev = getattr(candidates[0], attribute)
		rank = 1
		# Ties within one rank should increase the gap between that rank and the next.
		candidates_at_prev_rank = 0 	# i.e. 1st, 1st, 1st, 2nd, 3rd -> 1st, 1st, 1st, 4th, 5th
		# Every time the attribute changes, we increment the score.
		for candidate in candidates:
			curr = getattr(candidate, attribute)
			if prev != curr:
				# The next tier has been reached.
				rank += candidates_at_prev_rank
				candidates_at_prev_rank = 0
			candidate_to_rank_map[candidate] = rank
			candidates_at_prev_rank += 1
			prev = curr
		if verbose:
			print('Ranked candidates by {}. Results:\n'.format(attribute))
			for key in candidate_to_rank_map.keys():
				print('#{}: {} ({})'.format(candidate_to_rank_map[key], key.pronunciation, getattr(key, attribute)))
		return candidate_to_rank_map

	# Given a dict of candidates mapped to their rank given some heuristic,
	# Distribute points.
	# Return a dict of candidates mapped to points received.
	def rank_to_score(self, candidate_to_rank_map, heuristic, verbose=False):
		candidate_to_score_map = {}
		# Total points awarded: N(N + 1)/2 where N is the number of candidates.
		# Handling ties:
		# For a given range of tied candidates, we evenly distribute the number 
		# of points that would have been awarded had there been no ties within that range.
		# CANDIDATE RANK----1---2---3---3---3---6---7
		# POINTS, NO TIES---7---6--[5---4---3]--2---1
		# POINTS WITH TIES--7---6--[4---4---4]--2---1
		points_awarded_to_first = len(candidate_to_rank_map) # Points awarded to first place if not tied.

		rank_to_points_map = {}
		point_buffer = 0
		candidates_at_this_rank = 0
		# Thankfully, dict order is preserved. We can count on the first entry being rank 1.
		prev_rank = -1
		# Map each rank to the number of points awarded to that rank.
		for n, rank in enumerate(candidate_to_rank_map.values()):
			if prev_rank != rank:
				# Rank has just changed. Flush the buffer.
				point_buffer = points_awarded_to_first - n
				candidates_at_this_rank = 1
			else:
				# Points will be shared evenly between these iterations' candidates.
				point_buffer += points_awarded_to_first - n
				candidates_at_this_rank += 1
			# Update mapping.
			rank_to_points_map[rank] = point_buffer/candidates_at_this_rank
			# Prepare to iterate.
			prev_rank = rank
		if verbose:
			print('Points awarded to candidates for {}:'.format(heuristic))
		# Distribute the points to each rank.
		for candidate in candidate_to_rank_map:
			rank = candidate_to_rank_map[candidate]
			points = rank_to_points_map[rank]
			if verbose:
				print('{}, rank {}, got {} points'.format(candidate.pronunciation, rank, points))
			candidate_to_score_map[candidate] = points
		return candidate_to_score_map
	# Given a list of pronunciation candidates, returns a dict of string labels mapped to either:
	# 1) the shortest path candidate, if a unique shortest path exists.
	# 2) 31 candidates determined by every posisble fusion of 5 heuristics, 
	#    as well as 2 candidates chosen by "simple" single-strategies.
	def decide(self, candidates, verbose=False):
		from operator import attrgetter
		from collections.abc import Iterable
		# I will explain this very clearly for my future self.
		# PART 1:
		# - func is a function, either min() or max().
		# - func expects a list of objects and some attribute of that object
		#   by which to sort the list. 
		# - It returns only one candidate (again, either min or max attribute).
		# PART 2:
		# - But what if there are ties for min or max?
		# - The second part filters the list by the min or max attribute.
		# - The entire function, func_by_attribute, returns the list of ties, if applicable.
		def func_by_attribute(list_, attribute, func):
			from collections.abc import Iterable
			func_string = ''
			if func == min:
				func_string = 'min'
			elif func == max:
				func_string = 'max'
			else:
				print('Warning. Function {} has not been tested and cannot be guaranteed to work'.format(func))
			# Find min or max attribute among a list of candidates.
			candidate = func(list_, key=attrgetter(attribute))
			attr_val = getattr(candidate, attribute)
			# Filter the candidates by that attribute value.
			filtered_list = list(filter(lambda x: getattr(x, attribute) == attr_val, list_))
			if verbose:
				print('{a} {b}: {c}.\n Candidates of {a} {b}: {d}'.format(a=func_string, b=attribute, c=attr_val, \
					d=[choice.pronunciation for choice in filtered_list]))
			return filtered_list
		if candidates == None:
			print('Candidates list is None.')
			return
		elif not isinstance(candidates, Iterable) and candidates in ERRORS:
			print('Error reached.')
			return candidates # This is an error code.
		elif len(candidates) == 0:
			print('Candidates list is empty.')
			return

		
		# Find the minimum length among the candidates
		#min_length = min(candidates, key=attrgetter('length')).length
		# Filter out the candidates by that length.
		#min_lengths = list(filter(lambda x: x.length == min_length, candidates))
		min_lengths = func_by_attribute(candidates, 'length', min)

		if len(min_lengths) == 1:
			# Convert to strings.
			return {'min_length': min_lengths[0]}

		self.compute_heuristics(min_lengths)
		results = self.rank_by_heuristics(min_lengths)

		# Choose the 0th of each of the following, just because rank_by_heuristics can't break ties either.
		# Supposedly superior selection method.
		results['sum_of_products'] = func_by_attribute(min_lengths, 'sum_of_products', max)[0]
		# Old selection method.
		results['arc_count_sum'] = func_by_attribute(min_lengths, 'arc_count_sum', max)[0]

		return results

	def print(self):
		self.find_all_paths(True)

	def add(self, sub_letters, sub_phones, start_index):
		def create_or_iterate_arc(inter, a, b):
			new = self.Arc(inter, a, b)
			found = self.arcs.get(hash((inter, a, b)), None)
			if found is not None: # Do not iterate start nodes. The only count the number of words that start and end with
				found.count += 1 if not found.contains([self.START_NODE, self.END_NODE]) else 0 # this word's first and end letter.
				return found
			self.arcs[hash((inter, a, b))] = new # Not found. Add new one.
			found2 = self.arcs.get(hash((inter, a, b)), None)
			a.to_arcs.append(new)
			b.from_arcs.append(new)
			return new				# Return.
			
		def create_or_find_node(l, p, i):
			new = self.Node(l, p, i)
			found = self.nodes.get(hash((l, p, i)), None)
			if found is not None:
				return found # Found. Return.

			self.nodes[hash((l, p, i))] = new # Not found. Add new one.
			return new 	# Return it.
		
		# Add start node.
		a = create_or_find_node(sub_letters[0], sub_phones[0], start_index)
		# Add end node.
		b = create_or_find_node(sub_letters[-1], sub_phones[-1], start_index + len(sub_letters) - 1)
		# Add arc between them.
		arc = create_or_iterate_arc(sub_phones[1:-1], a, b)
		# Handle beginning and ending nodes.
		if start_index == 0:
			start_arc = create_or_iterate_arc('', self.START_NODE, a)
		elif start_index + len(sub_letters) == len(self.letters):
			end_arc = create_or_iterate_arc('', b, self.END_NODE)

	# Fix the silence problem.
	# Every node at index furthest should link to every node at furthest + 1.
	# (Thanks to link_unrepresented, a node at every index is guaranteed to exist.)
	def link_silences(self, furthest):
		import re
		# Link every node at index i to every node at index i + 1.
		added_count = 0
		def link(i):
			nonlocal added_count
			furthest_reached_nodes = []
			nodes_beyond = []
			for hash_ in self.nodes:
				if self.nodes[hash_].index == i:
					furthest_reached_nodes.append(self.nodes[hash_])
				elif self.nodes[hash_].index == i + 1:
					nodes_beyond.append(self.nodes[hash_])
			print('Adding {} x {} arcs'.format(len(furthest_reached_nodes), len(nodes_beyond)))
			for from_node in furthest_reached_nodes:
				for to_node in nodes_beyond:
					self.add(from_node.matched_letter + to_node.matched_letter, \
						from_node.phoneme + to_node.phoneme, i)
					added_count += 1
		# Get the unpaired letters by index.
		silent_pair = self.letters[furthest] + self.letters[furthest + 1]
		# Find every instance of the problematic letters.
		indices = [m.start() for m in re.finditer('(?={})'.format(silent_pair), self.letters)]
		# Patch all instances.
		print('Instances of {}:\n{}'.format(silent_pair, indices))
		for index in indices:
			link(index)
		print('Successfully added {} arcs.'.format(added_count))

	# Prophylactic measure.
	# Adds nodes between gaps in paths to solve the "silence problem."
	def link_unrepresented(self):
		if not len(self.unrepresented_bigrams):
			return
		for item in self.unrepresented_bigrams:
			start_index = item[0]
			end_index = start_index + 1
			bigram = item[1]
			start_char = bigram[0]
			end_char = bigram[1]
			#print('{}: {} at {}, {} at {}'.format(self.letters, start_char, start_index, end_char, end_index))
			# Nodes ending at start_index
			nodes_at_start_index = [node for node in self.nodes.values() if node.index == start_index]
			# Nodes starting at end_index
			nodes_at_end_index = [node for node in self.nodes.values() if node.index == end_index]
			# Because we're iterating from left onward, we know nodes_at_start_index must be populated.
			if not len(nodes_at_start_index):
				# This will only be a problem if the input has not been sanitized.
				print('No nodes started with {}.'.format(start_char))
				exit()
			# Nodes at end index, however, cannot be guaranteed to exist.
			if not len(nodes_at_end_index):
				nodes_at_end_index.append(self.Node(end_char, '-', end_index))

			# Now link all nodes at start to nodes at end through new arcs.
			for start_node in nodes_at_start_index:
				for end_node in nodes_at_end_index:
					self.add(start_node.matched_letter + end_node.matched_letter, \
						start_node.phoneme + end_node.phoneme, start_index)

	# Solves the "silence problem" as documented by M&D in
	# "Can syllabification improve pronunciation by analogy of English?"
	# The silence problem occurs when a letter pair in the input word
	# does not exist in the dataset.
	def flag_unrepresented_bigrams(self, input_word, database):
		represented_bigrams = set()
		keys = list(database.keys())
		# For each word.
		for word in keys:
			# For each bigram.
			for index in range (0, len(word) - 2):
				bigram = word[index] + word[index + 1]
				represented_bigrams.add(bigram)
		unrepresented_bigrams = []
		for x in range(0, len(input_word) - 2):
			bigram = input_word[x] + input_word[x + 1]
			if bigram not in represented_bigrams:
				unrepresented_bigrams.append((x, bigram))

		self.unrepresented_bigrams = unrepresented_bigrams