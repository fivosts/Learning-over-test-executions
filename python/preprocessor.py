#!/usr/bin/env python
import model_parser as ps
import utils
import os, sys
import torch
import torch.nn as nn
import torch.optim as optim
from random import shuffle
import architecture as arc
from collections import defaultdict
import itertools
import struct

class preprocessor:

	def __init__(this):
		return

	def preprocess_traces(this, project_name, base_path = "/home/trace_classification/",starting_folder = "traces", 
																								trace_name = "trace_",
																								below_keyword = "",
																								post_call_key = [],
																								encoding_size = 64, 
																								one_hot_vec = 32,
																								start_size = 0,
																								end_size = 0,
																								keep_only_argret = False,
																								excluded_keywords = [],
																								trace_reduce = True,
																								trace_encode = True,
																								## Ablation study arguments
																								encode_caller = True,
																								encode_callee = True,
																								encode_ret = True,
																								encode_args = True,
																								encode_globals = True,
																								discard_half = False,
																								preprocess_roper = False):

		trace_path_list, label_set = utils.set_trace_path(base_path + project_name + "/", starting_folder.replace("/", ""))
		for cat in trace_path_list:
			cat['path'] = cat['path'].replace(starting_folder.replace("/", "") + "/", "")
		trace_list = this.traces_to_list(trace_path_list, trace_name, starting_folder)
	
		if trace_reduce == True:
			if len(post_call_key) == 0:
				post_call_key = ["", ""]
			elif len(post_call_key) != 2:
				assert False, "Wrong length of postorder function call conversion keyword inserted"
			trace_list = this.trace_reduction(trace_list, trace_name, below_keyword, keep_only_argret, excluded_keywords, post_call_key, start_size, end_size, preprocess_roper)
		else:
			if preprocess_roper == True:
				trace_list = this.reduce_traces_keep_callees(trace_list, trace_name)
				this.list_to_trace_files(trace_list, "reduced_roper_traces", "log", trace_name)
		if trace_encode == True:
			trace_list = this.trace_encoding(trace_list, trace_name, encoding_size, one_hot_vec, preprocess_roper, encode_caller, encode_callee, encode_ret, encode_args, encode_globals, discard_half)

		return

	def trace_reduction(this, trace_list, trace_name, below_keyword, keep_only_argret, excluded_keywords, post_call_key, start_size, end_size, preprocess_roper):

		trace_list = this.reduce_traces_below_keyword(trace_list, below_keyword, trace_name)
		trace_list = this.reduce_traces_keep_argret(trace_list, trace_name, keep_only_argret)
		trace_list = this.reduce_traces_exclude_keyword(trace_list, excluded_keywords)
		trace_list = this.reduce_traces_convert_postorder(trace_list, trace_name, post_call_key[0], post_call_key[1])
		trace_list = this.reduce_traces_keep_front_back(trace_list, start_size, end_size)

		if preprocess_roper == True:
			trace_list = this.reduce_traces_keep_callees(trace_list, trace_name)
			this.list_to_trace_files(trace_list, "reduced_roper_traces", "log", trace_name)
		else:
			this.list_to_trace_files(trace_list, "reduced_traces", "log", trace_name)

		return trace_list	

	def trace_encoding(this, trace_list, trace_name, encoding_size, one_hot_vec, preprocess_roper, encode_caller, encode_callee, encode_ret, encode_args, encode_globals, discard_half):

		if preprocess_roper == False:
			trace_map = this.create_trace_map(trace_list, encoding_size, one_hot_vec)
			trace_list = this.encode_binary_traces(trace_map, trace_list,  encode_caller, encode_callee, encode_ret, encode_args, encode_globals, discard_half)
			this.list_to_trace_files(trace_list, "encoded_traces", "csv", trace_name)
		else:
			trace_list = this.encode_roper_traces(trace_list)
			# trace_list = this.encode_roper_arg_traces(trace_list)
			this.list_to_trace_files(trace_list, "encoded_roper_traces", "csv", trace_name)

		return trace_list

	def traces_to_list(this, trace_path_list, trace_name, subfolder):

		trace_list = {}
		errors = []
		for path in trace_path_list:
			trace_list[path['path']] = []
			
			for trace_file in os.listdir(path['path'] + subfolder):

				file_list = []

				if not os.path.isdir(path['path'] + "{}/{}".format(subfolder, trace_file)):
					try:
						f = open(path['path'] + "{}/{}".format(subfolder, trace_file), 'r', errors = 'ignore')
					except FileNotFoundError:
						errors.append("File {} not found".format(path['path'] + "{}/{}".format(subfolder, trace_file)))
						continue
					try:
						for line in f:
							file_list.append(line)
					except UnicodeDecodeError:
						errors.append("File {} is binary".format(path['path'] + "{}/{}".format(subfolder, trace_file)))
						continue
					if len(file_list) > 0:
						trace_list[path['path']].append(file_list)
					f.close()

		for error in errors:
			print(error)

		return trace_list

	def list_to_trace_files(this, trace_list, subfolder, file_extension, trace_name):

		for cat in trace_list:
			empty_file_counter = 0
			for index, trace in enumerate(trace_list[cat]):
				if len(trace) == 0:
					empty_file_counter += 1
					continue
				out = open(cat + "{}/{}{}.{}".format(subfolder, trace_name, index - empty_file_counter + 1, file_extension), 'w')
				for line in trace:
					if isinstance(line, (str)):
						out.write(line)
					elif isinstance(line, (list)):
						section_str = []
						for section in line:
							section_str.append(' '.join(section).replace("\n", ""))
						out.write(','.join(section_str) + '\n')
				out.close()
		return

	def reduce_traces_below_keyword(this, trace_list, keyword, trace_name, suppress_errors = False):

		errors = []
		del_index = []

		if keyword == "":
			return trace_list

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				found_keyword = False
				reduced_trace_list = []
				for line in trace:
					if found_keyword == False and keyword not in line:
						continue
					elif keyword in line:
						found_keyword = True
					# else:
					reduced_trace_list.append(line)

				if found_keyword == False and suppress_errors == False:
					errors.append("Keyword not found in {}".format(cat + "traces/{}{}.log".format(trace_name, index + 1)))

				if len(reduced_trace_list) == 0:
					del_index.append(index)
				else:
					trace_list[cat][index] = reduced_trace_list

			for i, ind in enumerate(del_index):
				del trace_list[cat][ind - i]
			del_index = []

		for error in errors:
			print(error)

		return trace_list

	def reduce_traces_keep_argret(this, trace_list, trace_name, keep_only_argret):

		errors = []
		del_index = []

		if keep_only_argret == False:
			return trace_list

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				reduced_trace = []
				for line in trace:
					stripped_line = line.replace('\n', "")
					split_line = stripped_line.split(', ')
					if len(split_line) < 3:
						errors.append("Line {} in trace {} has wrong format".format(line, cat + "traces/{}{}.log".format(trace_name, index + 1)))
						continue
					if split_line[1] == "" or split_line[2] == "": # Maybe needs 'and' here instead ?
						continue
					else:
						reduced_trace.append(line)
				if len(reduced_trace_list) == 0:
					del_index.append(index)
				else:
					trace_list[cat][index] = reduced_trace_list

			for i, ind in enumerate(del_index):
				del trace_list[cat][ind - i]
			del_index = []

		for error in errors:
			print(error)

		return trace_list

	def reduce_traces_exclude_keyword(this, trace_list, excluded_keywords):
		
		del_index = []

		if len(excluded_keywords) == 0:
			return trace_list

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				reduced_trace_list = []
				for line in trace:
					if any(keyword in line for keyword in excluded_keywords):
						continue
					else:
						reduced_trace_list.append(line)

				if len(reduced_trace_list) == 0:
					del_index.append(index)
				else:
					trace_list[cat][index] = reduced_trace_list

			for i, ind in enumerate(del_index):
				del trace_list[cat][ind - i]
			del_index = []

		return trace_list

	def reduce_traces_keep_front_back(this, trace_list, start_size, end_size):

		if start_size == 0 and end_size == 0:
			return trace_list

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				if len(trace) > start_size + end_size:
					trace_list[cat][index] = trace[:start_size] + trace[-end_size:]
				else:
					continue 
		return trace_list

	# Reducing function for roper's methodology
	def reduce_traces_keep_callees(this, trace_list, trace_name):

		errors = []

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				reduced_trace_list = []
				for line in trace:
					split_line = line.split(', ')
					if len(split_line) < 3:
						errors.append("Line {} in trace {} has wrong format".format(line, cat + "traces/{}{}.log".format(trace_name, index + 1)))
						continue
					split_pair = split_line[0].split(' ')
					if len(split_pair) != 2:
						errors.append("Caller Callee pair has wrong format: {} in trace {}".format(line, cat + "traces/{}{}.log".format(trace_name, index + 1)))
					else:
						reduced_trace_list.append(split_pair[1] + "\n")
				trace_list[cat][index] = reduced_trace_list

		return trace_list

	# Deprecated-Compatibility function for ethereum.
	# Converts trace to postorder after keyword
	def reduce_traces_convert_postorder(this, trace_list, trace_name, caller_key, callee_key):

		errors = []
		del_index = []



		if caller_key == "" and callee_key == "":
			return trace_list
		if caller_key == "" or callee_key == "":
			assert False, "Only caller or only callee provided for postorder conversion!"

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				post_trace = []
				pre_trace = []
				switch = False
				for line in trace:
					stripped_line = line.replace('\n', "")
					split_line = stripped_line.split(', ')
					# if len(split_line) < 3:
					# 	errors.append("Line {} in trace {} has wrong format".format(line, cat + "traces/{}{}.log".format(trace_name, index + 1)))
					# 	continue

					caller = split_line[0].split(' ')[0]
					callee = split_line[0].split(' ')[1]
					if caller_key in caller and callee_key in callee:
						switch = True
						hacked_line = []
						for item in line.split(' '):
							if item != '0':
								hacked_line.append(item)
						post_trace.append(' '.join(hacked_line))
						continue

					if switch == False or ("main" in caller and "ret" in callee):
						post_trace.append(line)
					else:
						pre_trace.append(line)

				for line in post_trace:
					pre_trace.append(line)

				if len(pre_trace) == 0:
					del_index.append(index)
				else:
					trace_list[cat][index] = pre_trace

			for i, ind in enumerate(del_index):
				del trace_list[cat][ind - i]
			del_index = []

		for error in errors:
			print(error)

		return trace_list


	def create_trace_map(this, trace_list, encoding_size, one_hot_vec):

		trace_map = {'function_map': {}, 'function_size': 0}

		for trace_cat in trace_list:
			for index, tr in enumerate(trace_list[trace_cat]):
				for tr_line in tr:
					line_spl = (tr_line.replace(' \n', '\n').split('\n'))[0].split(', ')
					if len(line_spl) != 3: # Global variable
						continue
					func_names = line_spl[0]
					caller = func_names.split(' ')[0]
					called = func_names.split(' ')[1]

					if caller not in trace_map['function_map']:
						trace_map['function_map'][caller] = {'index': 0, 'frequency': 1}
					else:
						trace_map['function_map'][caller]['frequency'] += 1

					if called not in trace_map['function_map']:
						trace_map['function_map'][called] = {'index': 0, 'frequency': 1}
					else:
						trace_map['function_map'][called]['frequency'] += 1

		if one_hot_vec % 2 == 1:
			assert False, ("One hot vec size provided for two function names should be an even number")

		if len(trace_map['function_map']) < int(one_hot_vec / 2):
			print("One hot vec size is larger than the size of the function names set")
			print("Switching to max, one bit per discrete function: {} bits per name vector".format(len(trace_map['function_map'])))
			one_hot_vec = 2*len(trace_map['function_map'])

		trace_map['function_size'] = int(one_hot_vec / 2)

		sorted_freq = []
		for func_name in trace_map['function_map']:
			sorted_freq.append(trace_map['function_map'][func_name]['frequency'])
		sorted_freq = sorted(sorted_freq, reverse = True)

		del_keys = []
		for func_name in trace_map['function_map']:
			if trace_map['function_map'][func_name]['frequency'] < sorted_freq[int(one_hot_vec / 2) - 1]:
				del_keys.append(func_name)
		for key in del_keys:
			del trace_map['function_map'][key]

		remove_equals = len(trace_map['function_map']) - (int(one_hot_vec / 2) - 1)

		del_keys = []
		for func_name in trace_map['function_map']:
			if trace_map['function_map'][func_name]['frequency'] == sorted_freq[int(one_hot_vec / 2) - 1] and remove_equals != 0:
				del_keys.append(func_name)
				remove_equals -= 1
		for key in del_keys:
			del trace_map['function_map'][key]

		one_hot_index = 0
		for func in trace_map['function_map']:
			trace_map['function_map'][func]['index'] = one_hot_index
			one_hot_index += 1

		trace_map['function_map']['other'] = {'index': one_hot_index, 'frequency': 0}

		print(len(trace_map['function_map']))
		for item in trace_map['function_map']:
			print(trace_map['function_map'][item])

		return trace_map

	def encode_binary_traces(this, trace_map, trace_list, encode_caller, encode_callee, encode_ret, encode_args, encode_globals, discard_half):

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				trace_list[cat][index] = this.encode_single_trace(trace_map, trace, encode_caller, encode_callee, encode_ret, encode_args, encode_globals, discard_half)

		return trace_list

	def encode_single_trace(this, trace_map, trace, encode_caller, encode_callee, encode_ret, encode_args, encode_globals, discard_half):

		encoded_trace = []

		for line in trace:
			encoded_line = []
			if len(line.split(', ')) < 2: #That's not a  valid func_call line

				if len(line.split('\n')[0].split(' ')) > 1:
					converted_vec = this.convert_to_bin_vec(line.replace(' \n', '\n').split('\n'))
					if len(converted_vec) > 0:
						encoded_line.append(converted_vec)
						encoded_trace.append(encoded_line)
				continue
			line_spl = (line.replace(', ', ',').replace(' \n', '\n').split('\n'))[0].split(',')
			func_names = line_spl[0] #

			caller = func_names.split(' ')[0]
			called = func_names.split(' ')[1]

			if encode_caller == True:
				if caller not in trace_map['function_map']:
					encoded_line.append(this.return_encoded_vector(trace_map['function_size'], trace_map['function_map']['other']['index']))
				else:
					encoded_line.append(this.return_encoded_vector(trace_map['function_size'], trace_map['function_map'][caller]['index']))
			else:
				encoded_line.append(this.return_encoded_vector(trace_map['function_size'], 0))

			if encode_callee == True:
				if called not in trace_map['function_map']:
					encoded_line[-1] += this.return_encoded_vector(trace_map['function_size'], trace_map['function_map']['other']['index'])
				else:
					encoded_line[-1] += this.return_encoded_vector(trace_map['function_size'], trace_map['function_map'][called]['index'])
			else:
				encoded_line[-1] += this.return_encoded_vector(trace_map['function_size'], 0)

			ret_list = line_spl[1].replace('   ', ' ').replace('  ', ' ').split(' ') # is -1 right ? TODO

			try:
				arg_list = line_spl[2].replace('   ', ' ').replace('  ', ' ').split(' ')		#load to the list the ret and arg parts
			except IndexError: # This index error means that the arg list is empty and the stupid external lib will not print an extra comma TODO!
				arg_list = ['0'] #Zero pad it

			#Fucking whitespaces
			delete_me = []
			for item in ret_list:
				if (item == ''):
					delete_me.append(item)
			for item in delete_me:
				ret_list.remove(item)
			delete_me = []
			for item in arg_list:
				if item == '':
					delete_me.append(item)
			for item in delete_me:
				arg_list.remove(item)

			if len(ret_list) == 0:
				ret_list.append('0')
			if len(arg_list) == 0:
				arg_list.append('0')

			for index, item in enumerate(ret_list):
				try:
					float(item)
				except ValueError:
					ret_list[index] = this.encode_string_to_bytes(item)

			for index, item in enumerate(arg_list):
				try:
					float(item)
				except ValueError:
					arg_list[index] = this.encode_string_to_bytes(item)

			if encode_ret == True:
				encoded_line.append(this.convert_to_bin_vec(ret_list))
			else:
				encoded_line.append(this.convert_to_bin_vec(['0']))
			if encode_args == True:
				encoded_line.append(this.convert_to_bin_vec(arg_list))
			else:
				encoded_line.append(this.convert_to_bin_vec(['0']))

			padded_ret = this.convert_to_bin_vec(ret_list)
			padded_arg = this.convert_to_bin_vec(arg_list)
			assert(len(padded_ret) % 64 == 0)
			assert(len(padded_arg) % 64 == 0)

			encoded_trace.append(",".join([" ".join(x) for x in encoded_line]) + "\n")

		if discard_half == True:
			return encoded_trace[:int(len(encoded_trace) / 2)]
		else:
			return encoded_trace

	def encode_roper_arg_traces(this, trace_list):

		trace_map = this.create_trace_map(trace_list, 64, 32)

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				# for line in trace:
				encoded_trace = []
				enc_trace = this.encode_single_trace(trace_map, trace, False, False, False, True, False, False)
				for line in enc_trace:
					encoded_trace.append(line.split(',')[2].replace("\n", "").replace(" ", ""))
				# print("\n\n\n\n\n\n")
				# print(type(encoded_trace[0]))
				# print((encoded_trace[0][0:5]))

				trace_list[cat][index] = ["".join(encoded_trace)]
				# sys.exit(1)
		# sort so that event that occurs more will be encoded as a shorter string
		# callee_freq_sorted = sorted(callee_count_map, key=callee_count_map.get, reverse=True)
		# available_callee_keys = this.generate_event_short_names(len(callee_freq_sorted))
		# # build the mapping
		# ee_map = {}
		# for index,callee in enumerate(callee_freq_sorted):
		# 	ee_map[callee] = available_callee_keys[index]

		# for cat in trace_list:
		# 	for index, trace in enumerate(trace_list[cat]):
		# 		reduced_trace_list = []
		# 		for line in trace:
		# 			callee = line.replace("\n", "").strip()
		# 			reduced_trace_list.append(ee_map[callee])
		# 		trace_list[cat][index] = [",".join(reduced_trace_list)]

		return trace_list

	def encode_roper_traces(this, trace_list):

		callee_list = []
		callee_count_map = defaultdict(int)
		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				for line in trace:
					callee = line.replace("\n", "").strip()
					if callee not in callee_list:
						callee_list.append(callee)
					callee_count_map[callee] = callee_count_map.setdefault(callee, 0) + 1

		# sort so that event that occurs more will be encoded as a shorter string
		callee_freq_sorted = sorted(callee_count_map, key=callee_count_map.get, reverse=True)
		available_callee_keys = this.generate_event_short_names(len(callee_freq_sorted))
		# build the mapping
		ee_map = {}
		for index,callee in enumerate(callee_freq_sorted):
			ee_map[callee] = available_callee_keys[index]

		for cat in trace_list:
			for index, trace in enumerate(trace_list[cat]):
				reduced_trace_list = []
				for line in trace:
					callee = line.replace("\n", "").strip()
					reduced_trace_list.append(ee_map[callee])
				trace_list[cat][index] = [",".join(reduced_trace_list)]

		return trace_list

	#Helper functions
	def return_encoded_vector(this, size, index):
		encoded_list = ['0'] * size
		encoded_list[index] = '1'
		return encoded_list

	def encode_string_to_bytes(this, input_string):

		encoded_string = []
		for char in input_string:
			encoded_string.append(str(ord(char)))

		assert(len(encoded_string) == len(input_string))
		return " ".join(encoded_string)

	def convert_to_bin_vec(this, input_list):

		bin_list = []

		for item in input_list:
			try:
				item_list = item.split(' ')
				for num in item_list:
					if isinstance(num, int):
						str_num = str(bin(abs(int(num))))
					else:
						str_num = bin(struct.unpack('!i',struct.pack('!f', float(num)))[0]).replace("-", "")

					for i in range(64 - len(str_num[2:])):
						bin_list.append('0')

					for char in str_num[2:]:
						if char == 'b' or 'b' in char:
							print(char)
							print(str_num)
						# else:
						# 	print(str_num)
						bin_list.append(char)
			except ValueError:
				# print("Bin value not a number")
				pass

		assert(len(bin_list) % 64 == 0)
		return bin_list

	def generate_event_short_names(this, size):
		alphabets = ['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']#,'G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
		new_names = []
		
		# estimate max number of combinations
		max_combinations = 1
		while len(alphabets)**max_combinations < size:
			max_combinations = max_combinations + 1 

		current_size = 0
		for i in range(1, max_combinations + 1):
			for tupl in itertools.product(alphabets, repeat = i):
				if (current_size < size):
					current_size = current_size + 1
					new_names.append("".join(tupl))
					if current_size == size:
						return new_names	
