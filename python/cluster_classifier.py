#!/usr/bin/env python
import plotter, utils
import os.path
import torch
import torch.nn as nn
import torch.optim as optim
from random import shuffle
from sklearn.cluster import AgglomerativeClustering
import numpy as np
import operator
import json

class cluster_classifier:

	def __init__(this):
		return

	def initialize_architecture(this, project_name, base_path = "/home/trace_classification/", trace_name = "trace_",
																										encoded_trace_folder = "encoded_roper_traces",
																										excluded_labels = [],
																										clustering_algorithm = 'Agglomerative',
																										criterion = "distinct_ave_threshold",
																										affinity = 'euclidean', compute_full_tree = 'auto',
																										connectivity = None, distance_threshold = None,
																										linkage='average', memory = None, n_clusters = 40.0,
																										bit_feature_encoding = False,
																										make_new_folder = "",
																										write_cluster_log = False,
																										print_cluster_log = True,
																										print_cluster_stats = False,
																										plot_clusters = True,
																										save_cluster_bars = False,
																										show_cluster_bars = False,
																										plot_binary = False,
																										analyze_results = False,
																										analyze_only_keywords = [],
																										exclude_keys = [],
																										write_analysis_to_file = False,
																										print_analysis = True,
																										plot_analysis = True): # TODO this

		if project_name[-1] != "/":
			project_name += "/"
		trace_path_list, label_set = utils.set_trace_path(base_path + project_name, encoded_trace_folder, excluded_labels)

		print("Performing clustering on {}".format(project_name))

		if len(trace_path_list) == 2 and plot_binary == False:
			print("Multi class labelling not supported. Switching to binary")
			plot_binary = True


		dataset = this.create_dataset(trace_path_list, excluded_labels, trace_name, bit_feature_encoding = bit_feature_encoding)	
		dataset = this.flatten_dataset_dimension(dataset)

		cluster_distrib, dataset = this.cluster_dataset(dataset, affinity = affinity, compute_full_tree = compute_full_tree,
																connectivity = connectivity, distance_threshold = distance_threshold,
																linkage = linkage, memory = memory, n_clusters = n_clusters)

		if print_cluster_stats == True:
			this.cluster_stats(cluster_distrib, dataset)

		clustering_criterion, results = this.evaluate_clustering(cluster_distrib, dataset, label_set, criterion)

		if write_cluster_log == True or print_cluster_log == True:
			results = utils.add_perc_metrics(results)
			if write_cluster_log == True:
				if make_new_folder != "":
					utils.mkdirs(base_path + project_name + "/clustering_logs/", make_new_folder.replace("/", ""), subfolders = ["plots"])
				this.write_results_to_file(results, base_path + project_name + "/clustering_logs/{}clustering_results.json".format(make_new_folder + "/"), criterion, clustering_algorithm, linkage, n_clusters)
				if analyze_results == True:
					this.analyze_clustering_results(base_path + project_name + "/clustering_logs/{}".format(make_new_folder + "/"), "clustering_results.json", search_only = analyze_only_keywords, 
																																exclude_keys = exclude_keys, write_to_file = write_analysis_to_file,
																																print_optimals = print_analysis, plot_optimals = plot_analysis, 
																																show_plots = show_cluster_bars)
			if print_cluster_log == True:
				for res in results:
					if isinstance(results[res], (dict, list, set)):
						for cat in results[res]:
							print("{} {}: {}".format(res, cat, results[res][cat]))
					else:
						print(str(res) + ": " + str(results[res]))
				print("\n")

		if plot_clusters == True:
			pl = plotter.plotter()
			if plot_binary == True:
				bin_label = "bin"
			else:
				bin_label = "multi"

			pl.plot_cluster_bars(cluster_distrib, file_path = "{}/clustering_logs/{}plots/{}_{}_{}_{}_{}.".format(base_path+project_name, make_new_folder + "/", criterion.split('_')[1], clustering_algorithm[:3], linkage[:3], (str(n_clusters)).replace(".", ""), bin_label), 
															metadata = {'criterion': {'type': criterion, 'value': clustering_criterion, 'linestyle': '--', 'color': 'r'}, 
																		'title': {'value': project_name.replace("/", " "), 'fontsize': 20},
																		'xlabel': {'value': "Cluster ID", 'fontsize': 16},
																		'ylabel': {'value': "Datapoints", 'fontsize': 16},
																		'grid': {'which': 'major', 'alpha': 0.7, 'linestyle': '-', 'axis': 'y'}}, 
															save_file = save_cluster_bars, show_file = show_cluster_bars,
															binary_class = plot_binary, legend = True,
															figsize = (12, 7), transparent_frame = True)



		return

	def create_dataset(this, trace_path_list, excluded_train_labels, trace_name, bit_feature_encoding = False):

		dataset = []

		for category in trace_path_list:
			for tr in range(1, category['num_traces'] + 1):
				datapoint = this.process_trace(category['path'] + trace_name + str(tr) + category['extension'], bit_feature = bit_feature_encoding)
				datapoint['label'] = category['label']
				datapoint['index'] = tr
				if datapoint['label'] not in excluded_train_labels:
					dataset.append(datapoint)

		return dataset

	def process_trace(this, trace_path, bit_feature = False):

		datapoint = []
		global_values = []

		with open(trace_path, 'r') as f:
			first_line = f.readline()

		line_split = first_line.replace("\n", "").split(',')
		feature_vector = []

		if bit_feature == False:
			for index, num in enumerate(line_split):
				if num == "":
					continue
				feature_vector.append(int(num, 16))  # Try a) one hex or dec = feature b) one bit of bin -> feature
		else:
			for index, num in enumerate(line_split):
				if num == "":
					continue
				bin_num_str = (str(bin(int(num, 16)))).replace("0b", "")
				for bit in bin_num_str:
					feature_vector.append(int(bit))

		f.close()
		return {'value': feature_vector}

	def flatten_dataset_dimension(this, dataset):

		max_length = 0
		for datapoint in dataset:
			if len(datapoint['value']) > max_length:
				max_length = len(datapoint['value'])

		for datapoint in dataset:
			for i in range(len(datapoint['value']), max_length):
				datapoint['value'].append(0)

		return dataset

	def cluster_dataset(this, dataset, affinity, compute_full_tree, connectivity, distance_threshold, linkage, memory, n_clusters):

		flattened_values = [ x['value'] for x in dataset ]
		raw_input = np.array(flattened_values)

		if isinstance(n_clusters, (int)):
			normalized_cluster_count = n_clusters
		elif isinstance(n_clusters, (float)):
			normalized_cluster_count = int(n_clusters * len(dataset))
		else:
			assert False, ("Unsupported type for n_clusters: {}".format(n_clusters))

		clusters = AgglomerativeClustering(affinity = affinity, compute_full_tree = compute_full_tree,
											connectivity = connectivity, distance_threshold = distance_threshold,
											linkage = linkage, memory = memory, n_clusters = normalized_cluster_count,
											pooling_func = 'deprecated').fit(raw_input)

		if len(dataset) != len(clusters.labels_):
			print("Error in Input/Output dimensions")

		cluster_distrib = {}
		for cl, dp in zip(clusters.labels_, dataset):
			dp['cluster_id'] = cl
			if cl not in cluster_distrib:
				cluster_distrib[cl] = {'total': 1}
			else:
				cluster_distrib[cl]['total'] += 1

			if dp['label'] not in cluster_distrib[cl]:
				cluster_distrib[cl][dp['label']] = 1
			else:
				cluster_distrib[cl][dp['label']] += 1

		return sorted(cluster_distrib.items(), key = lambda x: x[1]['total'], reverse = True), dataset

	def cluster_stats(this, cluster_distrib, dataset):

		total_points = len(dataset)
		out = "Total occurences: {}\nCluster ID\tNumber of points\tPercentage\n".format(total_points)
		for cluster in cluster_distrib:
			out += "{}:\t\t{}\t\t\t{}%\n".format(cluster[0], cluster[1]['total'], round(float(100*(cluster[1]['total'] / total_points)), 4))
		return

	def evaluate_clustering(this, cluster_distribution, dataset, label_set, criterion = "distinct_ave_threshold", label_class = "binary"):

		if criterion == "distinct_ave_threshold":
			pass_threshold = len(dataset) / len(cluster_distribution)
			pass_cluster_ids = []
			for cluster in cluster_distribution:
				if cluster[1]['total'] > pass_threshold:
					pass_cluster_ids.append(cluster[0])

		elif criterion == "distinct_largest":
			pass_cluster_ids = [cluster_distribution[0][0]]
			pass_threshold = cluster_distribution[0][1]['total']

		else:
			assert False, ("{} is an unknown clustering criterion".format(criterion))
			
		label_precision = {}
		if label_class == "binary":
			label_precision['pass'] = {'total': 0, 'matches': 0}
			label_precision['fail'] = {'total': 0, 'matches': 0}
			
			for datapoint in dataset:
				if "pass" in datapoint['label']:
					label_precision['pass']['total'] += 1
					if datapoint['cluster_id'] in pass_cluster_ids:
						label_precision['pass']['matches'] += 1
				elif "fail" in datapoint['label']:
					label_precision['fail']['total'] += 1
					if datapoint['cluster_id'] not in pass_cluster_ids:
						label_precision['fail']['matches'] += 1

				else:
					assert False, ("Unknown type of label: {}".format(datapoint['label']))
		elif label_class == "multi" or label_class == "multi-class":
			for label in label_set:
				label_precision[label] = {'total': 0, 'matches': 0}
			for datapoint in dataset:
				label_precision[datapoint['label']]['total'] += 1
				if datapoint['label'] == cluster_distribution['expected_label']: # TODO for multi-class clustering
					label_precision['label']['matches'] += 1

		return len(pass_cluster_ids), label_precision

	def add_perc_metrics(this, results, label_class = "binary", fail_as_positives = True):

		if label_class == "binary":
			pass_match, pass_total, fail_match, fail_total = results['pass']['matches'], results['pass']['total'], 0, 0
			for category in results:
				if "fail" in category:
					fail_match += results[category]['matches']
					fail_total += results[category]['total']

			if fail_as_positives == True:
				try:
					results['precision'] = "{}%".format(round(100*float(fail_match / (fail_match + pass_total - pass_match)), 2))
				except ZeroDivisionError:
					results['precision'] = "-0.0%"
					print("Everything is classified as passing trace")
				try:
					results['recall'] = "{}%".format(round(100*float(fail_match / fail_total), 2))
				except ZeroDivisionError:
					results['recall'] = "-inf"
					assert False, "No failing traces in dataset"
				try:
					results['true_neg_rate'] = "{}%".format(round(100*float(pass_match / pass_total), 2))
				except ZeroDivisionError:
					results['true_neg_rate'] = "-inf"
					assert False, "No passing traces in dataset"
			else:
				try:
					results['precision'] = "{}%".format(round(100*float(pass_match / (pass_match + fail_total - fail_match)), 2))
				except ZeroDivisionError:
					results['precision'] = "-0.0%"
					print("Everything is classified as passing trace")
				try:
					results['recall'] = "{}%".format(round(100*float(pass_match / pass_total), 2))
				except ZeroDivisionError:
					results['recall'] = "-inf"
					assert False, "No failing traces in dataset"
				try:
					results['true_neg_rate'] = "{}%".format(round(100*float(fail_match / fail_total), 2))
				except ZeroDivisionError:
					results['true_neg_rate'] = "-inf"
					assert False, "No passing traces in dataset"

		return results

	def write_results_to_file(this, results, file_path, criterion, clustering_algorithm, linkage, num_clusters):

		if not os.path.isfile(file_path):
			outf = open(file_path, 'w')
			outf.close()

		outf = open(file_path, 'r+')

		# print(results)
		crit_key = 'criterion: {}'.format(criterion)
		alg_key = 'algorithm: {}'.format(clustering_algorithm)
		link_key = 'linkage: {}'.format(linkage)
		cl_count_key = 'cluster_count: {}'.format(num_clusters)

		out_dict = [{crit_key: 
						[{alg_key: 
							[{link_key: 
								[{cl_count_key: [results]}]}]}]}]


		# TODO recursive function here
		with open(file_path, 'r') as outf:
			try:
				data = json.load(outf)

				crit_index, alg_index, link_index, cl_index = -1, -1, -1, -1
				for i, key in enumerate(data):
					if crit_key in key:
						crit_index = i
						break
				if crit_index >= 0:
					for i, key in enumerate(data[crit_index][crit_key]):
						if alg_key in key:
							alg_index = i
							break							
					if alg_index >= 0:
						for i, key in enumerate(data[crit_index][crit_key][alg_index][alg_key]):
							if link_key in key:
								link_index = i
								break
						if link_index >= 0:
							for i, key in enumerate(data[crit_index][crit_key][alg_index][alg_key][link_index][link_key]):
								if cl_count_key in key:
									cl_index = i
									break
							if cl_index >= 0:
								if results not in data[crit_index][crit_key][alg_index][alg_key][link_index][link_key][cl_index][cl_count_key]:
									data[crit_index][crit_key][alg_index][alg_key][link_index][link_key][cl_index][cl_count_key].append(results)
							else:
								data[crit_index][crit_key][alg_index][alg_key][link_index][link_key].append({cl_count_key: [results]})
						else:
							data[crit_index][crit_key][alg_index][alg_key].append({link_key: [{cl_count_key: [results]}]})
					else:
						data[crit_index][crit_key].append({alg_key: [{link_key: [{cl_count_key: [results]}]}]})
				else:
					data.append( {crit_key: [{alg_key: [{link_key: [{cl_count_key: [results]}]}]}]} )

				out_dict = data
			except json.decoder.JSONDecodeError:
				pass

		with open(file_path, 'w') as outf:
			json.dump(out_dict, outf, indent = 4)
		
		return

	def analyze_clustering_results(this, base_path, file = "/clustering_results.json", search_only = [], exclude_keys = [], 
										write_to_file = False, print_optimals = True, plot_optimals = False, show_plots = False, file_name = ""):

		try:
			with open(base_path + file, 'r') as f:
				try:
					data = json.load(f)

				except json.decoder.JSONDecodeError:
					assert False, ("Problem reading the json file")

			res_list = this.json_res_to_list(data, search_only, exclude_keys, [])
			sorted_precision = sorted(res_list, key = lambda x : float(x['precision'].replace("%", "")), reverse = True )

			optimal_points = [sorted_precision[0]]
			pr_reference = sorted_precision[0]['precision']
			rec_reference = sorted_precision[0]['recall']

			for item in sorted_precision[1:]:
				if item['recall'] > rec_reference or (item['recall'] == rec_reference and item['precision'] == pr_reference):
					optimal_points.append(item)
					pr_reference = item['precision']
					rec_reference = item['recall'] 

			if print_optimals == True:
				print("Optimal configurations\n------------------------------\n")
				for point in optimal_points:
					print("Precision: {}, Recall: {}, TNR: {}, Configuration: {}".
						format(point['precision'], point['recall'], point['true_neg_rate'], ', '.join(point['configuration'])))

			if write_to_file == True:

				if file_name == "":
					outf_name = "/optimal_points"
					for key in search_only:
						outf_name += "_{}".format(key)
					for key in exclude_keys:
						outf_name += "_no-{}".format(key)
				else:
					outf_name = file_name
					if file_name[0] != "/":
						outf_name = "/" + outf_name

				with open(base_path + outf_name + ".log", 'w') as out:
					out.write("Optimal configurations\n------------------------------\n")
					for point in optimal_points:
						out.write("Precision: {}, Recall: {}, TNR: {}, Configuration: {}\n".
							format(point['precision'], point['recall'], point['true_neg_rate'], ', '.join(point['configuration'])))

			if plot_optimals == True:
				datapoints = []
				pr_list = []
				rec_list = []
				for item in optimal_points:
					pr_list.append(float(item['precision'].replace("%", "")))
					rec_list.append(float(item['recall'].replace("%", "")))
				datapoints.append({'label': ['Precision', 'Recall'], 'x': [["-".join(item['configuration'])], ["-".join(item['configuration'])]], 'y': [pr_list, rec_list]})
				pl = plotter.plotter()
				pl.plot_bars(datapoints, file_path = base_path + "optimal_points", legend = True, show_xlabels = True, show_file = show_plots, save_file = plot_optimals)
			
			return optimal_points

		except FileNotFoundError:
			print("Result subfolder {} not found. Skipping...".format(base_path + file))
			return

	def json_res_to_list(this, data, search_only, exclude_keys, config):

		ret_list = []
		for item in data:
			if 'precision' in item and 'recall' in item:
				accepted_dict = False

				truth_count = 0
				for keyword in search_only:
					for word in config:
						if keyword in word:
							truth_count += 1
							break

				found_excl = False
				for keyword in exclude_keys:
					for word in config:
						if keyword in word:
							found_excl = True
							break

				if truth_count == len(search_only) and found_excl == False:
					accepted_dict = True

				if accepted_dict == True:
					t = item
					t['configuration'] = config
					ret_list.append(item)
			else:
				for key in item:
					ret_list += this.json_res_to_list(item[key], search_only, exclude_keys, config + [key])

		return ret_list

	def test_tensor(this, tensor):
		assert torch.isnan(tensor).any() == 0
		return
