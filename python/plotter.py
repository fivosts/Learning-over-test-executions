#!/usr/bin/env python
import os, sys
import matplotlib
# matplotlib.use('GTK3Cairo')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

class plotter:

	def __init__(this):
		return

	def plot_cluster_bars(this, cluster_distrib, file_path = "", metadata = {},
																		binary_class = False,
																		plot_only_labels = [],
																		show_file = False, 
																		save_file = False,
																		file_extension = "png",
																		plot_title = "",
																		legend = False,
																		figsize = (11, 7),
																		x_rotation = 45,
																		transparent_frame = False,
																		bar_annotations = False, 
																		show_xlabels = False):

		bar_length = min(40, len(cluster_distrib))
		label_order = ["pass"]
		labels = set("pass")

		if binary_class == True:
			label_order.append("fail")
		else:
			for item in cluster_distrib[:bar_length]:
				for label in item[1]:
					if "fail" in label and label not in labels:
						labels.add(label)
						label_order.append(label)
		del labels

		x_axis = [str(x[0]) for x in cluster_distrib[:bar_length]]
		datapoints = []

		for label in label_order:
			y_points = []
			for cluster in cluster_distrib[:bar_length]:
				if binary_class == True:
					label_sum = 0
					for key in cluster[1]:
						if label in key:
							label_sum += cluster[1][key]
					y_points.append(label_sum)
				else:
					if label in cluster[1]:
						y_points.append(cluster[1][label])
					else:
						y_points.append(0)
			datapoints.append({'x': [x_axis], 'y': [y_points], 'label': [label]})

		## This point below must be generalized TODO

		this.plot_bars(datapoints, file_path = file_path, metadata = metadata, figsize = figsize, show_file = show_file, 
						save_file = save_file, file_extension = file_extension, 
						plot_title = plot_title, legend = legend, x_rotation = x_rotation,
						transparent_frame = transparent_frame, bar_annotations = bar_annotations,
						show_xlabels = False)

		"""
		I need:
				A) The cluster IDs and their count (in cluster_distrib)
				B) Their size (in cluster_distrib)
			C) The type of points they hold (pass, fail or multi-labels if that is the case) (in dataset)
			D) Colours of the bars
			E) Colour discrimination between passing and failing clusters
			F) The threshold upon which the discrimination happens (Could be multiple categories)
				G) The title of the diagram
				H) If you want it to be saved
				I) If you want it to be printed on the screen
				J) The path on which you want it to be saved
				K) Algorithm to create the folders and set appropriately the names (you have to provide linkage, clustering algo, distance algo etc. etc.)
		"""

		return



	# [ { 'x': [] int, 'y': [], 'label_point': str } ] 
	def plot_bars(this, point_set, metadata = {}, figsize = (11, 7), show_file = False, 
																	save_file = False,
																	x_rotation = 45,
																	file_extension = "png",
																	file_path = "",
																	plot_title = "", 
																	legend = False, 
																	transparent_frame = False, 
																	bar_annotations = False, 
																	show_xlabels = False):

		color_stack = [] # TODO

		fig,ax = plt.subplots(figsize = figsize)
		# sns.set_style('whitegrid', {'legend.frameon': True, 'font.family': [u'serif']})

		bars = []   # Bar plots here
		x_count = point_set[0]['x'][0]
		group_count = point_set[0]['x']
		bar_height_offset = [[0] * len(x_count)] * len(group_count)
		bar_width = 0.2

		for group_index, datapoint in enumerate(point_set):

			bar_width_offset_range = 2 * bar_width * ( float(len(datapoint['x'])) / 2 - 0.5)
			member_index = 0
			for x_group, y_group, label_group in zip(datapoint['x'], datapoint['y'], datapoint['label']): # if datapoint['y'] is a list of lists, then it means grouping

				member_ind_count = member_index + min(0.5, (len(datapoint['x']) + 1) % 2) - int(len(datapoint['x']) / 2)
				if group_index != 0:
					bars.append(ax.bar(np.arange(len(x_group)) + member_ind_count * bar_width_offset_range, 
										y_group, 
										bar_width, 
										bottom = bar_height_offset[member_index], 
										label = label_group))
				else:
					bars.append(ax.bar(np.arange(len(x_group)) + member_ind_count * bar_width_offset_range, 
										y_group, 
										bar_width, 
										label = label_group))
				bar_height_offset[member_index] = [x + y for x,y in zip(bar_height_offset[member_index], y_group)]
				member_index += 1

		# TODO
		if bar_annotations == True:
			pass

		ax.set_ylim([0, bar_height_offset[0][0] * 1.02])
		plt.xticks(np.arange(len(x_count)), (x for x in x_count), rotation = x_rotation)
		ax.set_xticklabels((x for x in x_count))

		####### Fix that with arguments
		if transparent_frame == True:
			ax.spines["top"].set_visible(False)
			ax.spines["left"].set_visible(False)
			ax.spines["right"].set_visible(False)
			ax.spines["bottom"].set_visible(False)

		if show_xlabels == False:
			ax.tick_params(
			    axis='x',          # changes apply to the x-axis
			    which='both',      # both major and minor ticks are affected
			    bottom=False,      # ticks along the bottom edge are off
			    top=False,         # ticks along the top edge are off
			    labelbottom=False)  # labels along the bottom edge are off


		for dt in metadata:
			if dt == "criterion":
				ax.axvline(((metadata[dt]['value'] - 1) * 2 + 1) / 2, linestyle = metadata[dt]['linestyle'], label = metadata[dt]['type'], color = metadata[dt]['color'])
			elif dt == "title":
				ax.set_title(metadata[dt]['value'], fontsize = metadata[dt]['fontsize'], fontname = 'serif')
			elif dt == "xlabel":
				ax.set_xlabel(metadata[dt]['value'], fontsize = metadata[dt]['fontsize'], fontname = 'serif')
			elif dt == "ylabel":
				ax.set_ylabel(metadata[dt]['value'], fontsize = metadata[dt]['fontsize'], fontname = 'serif')
			elif dt == "grid":
				ax.grid(which = metadata[dt]['which'], alpha = metadata[dt]['alpha'], linestyle = metadata[dt]['linestyle'], axis = metadata[dt]['axis'])

			"""
			Types of metadata: Linkage, cluster count, name of project, clustering algorithm
			"""

		if legend == True:
			handles, labels = ax.get_legend_handles_labels()
			plt.legend(handles, labels)

		if save_file == True:
			plt.savefig(file_path + file_extension.replace(".", ""), bbox_inches='tight')

		if show_file == True:
			plt.show()


		plt.clf()
		plt.cla()
		plt.close('all')
		plt.close(fig)

		return


	# plot_line(precision, recall, ['5', '10', '15', '20', '30'], base_path + "/pr_train_charts/pr_train_size_chart_" + str(epoch), dual_axis = True, plot_label = "Ethereum")
	#Generic function. Plots single line, plots, two lines on dual axis, or two lines on 1 axis
	def plot_line(this, pr, rec, x_axis, plot_name, single_line = False, dual_axis = False, plot_label = ""):

		fig,ax = plt.subplots(figsize=(11,7))
		sns.set_style('whitegrid', {'legend.frameon': True, 'font.family': [u'serif']})

		ax.spines["top"].set_visible(False)    
		ax.spines["bottom"].set_visible(False)    
		ax.spines["right"].set_visible(False)    
		ax.spines["left"].set_visible(False)  

		ax.get_xaxis().tick_bottom()    
		ax.get_yaxis().tick_left()

		if single_line == True:
			ax.plot(pr, rec, '--xb')		
			ax.set_ylabel('Precision', fontsize = 13)
			ax.set_ylabel('Recall', fontsize = 13)
			ax.set_xlabel('Recall', fontsize = 13)
			print(pr)
			print(rec)
			annotation = ['50', '100', '200', '400', '800', '1200']
			for i in range(len(pr)):
				ax.annotate(annotation[i], (pr[i], rec[i]), xycoords = 'data', fontsize = 11)
		elif dual_axis == True:
			ax2 = ax.twinx()
			ax.set_title(plot_label, fontsize = 34)
			ax.title.set_position([.5, 1.02])
			ax.plot(x_axis, pr, '-x', color = '#006d2c', label='precision', linewidth = 2, mew=2, ms=7)
			ax2.plot(x_axis, rec, '-x', color = '#fc9272', label='recall', linewidth = 2, mew=2, ms=7)
			ax.tick_params(labelsize = 21)
			ax2.tick_params(labelsize = 21)
			ax.set_ylabel('Precision', color = '#006d2c', fontsize = 28)
			ax2.set_ylabel('Recall', color = '#fc9272', fontsize = 28)
			ax.set_xlabel("% traces used in training", fontsize = 28, labelpad = 10)

			ax.yaxis.grid(False) #horizontal grid
			ax.xaxis.grid(False) #horizontal grid

		else:
			x_axis1 = np.arange(len(pr))
			ax.plot(pr, x_axis1, '-x', color = 'green', label='precision', linewidth = 2, mew=2, ms=7)
			ax.plot(rec, x_axis1, '-x', color = 'coral', label='recall', linewidth = 2, mew=2, ms=7)
			ax.set_ylabel('%')
			ax.set_xlabel('Epochs')
			ax.legend(loc='lower right', fontsize = 12, markerfirst = False, frameon = False)

		ax.set_ylim([0.3, 1.05])
		# limit = round(max(0, min(0.3, min(min(pr), min(rec)) - 0.1)), 1)
		# plt.yticks(np.arange(0.4, 1.0, 0.2))
		# ax.grid(which='major', alpha=0.7, linestyle = '-', axis = 'y')

		if dual_axis == True:
			ax2.set_ylim([0.3, 1.05])
			# limit2 = round(max(0, min(0.3, min(min(pr), min(rec)) - 0.1)), 1)
			# plt.yticks(np.arange(0.0, 1.1, 0.1))
			# ax2.set_yticks(np.arange(0.4, 1.0, 0.2))
			# ax2.grid(which='major', alpha=0.7, linestyle = '--', axis = 'y')

		# plt.show()
		plt.savefig(plot_name + '.png', bbox_inches="tight", format='png')

		return
