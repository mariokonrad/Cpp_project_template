#!/usr/bin/python3

import sys
import os
import shutil
import argparse
from inspect import isfunction
from collections import defaultdict
from itertools import takewhile, count

# infrastructure

# from: http://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
# because shutil.copytree is annoying regarding the existance of the destination directory.
# shutils.copytree calls mkdir and fails unncesseraly
def copytree(src, dst, symlinks = False, ignore = None):
	if not os.path.exists(dst):
		os.makedirs(dst)
		shutil.copystat(src, dst)
	lst = os.listdir(src)
	if ignore:
		excl = ignore(src, lst)
		lst = [x for x in lst if x not in excl]
	for item in lst:
		s = os.path.join(src, item)
		d = os.path.join(dst, item)
		if symlinks and os.path.islink(s):
			if os.path.lexists(d):
				os.remove(d)
			os.symlink(os.readlink(s), d)
			try:
				st = os.lstat(s)
				mode = stat.S_IMODE(st.st_mode)
				os.lchmod(d, mode)
			except:
				pass # lchmod not available
		elif os.path.isdir(s):
			copytree(s, d, symlinks, ignore)
		else:
			shutil.copy2(s, d)

def install_file(src, dst):
	"""
	Installs the file specified by src. If the target destination directory does
	not exist, it will be created.
	"""
	dst_dir = os.path.dirname(dst)
	if not os.path.exists(dst_dir):
		print("    ... creating directory: " + os.path.relpath(dst_dir))
		os.makedirs(dst_dir)
	try:
		shutil.copy2(src, dst_dir)
		print("    ... done")
	except shutil.Error as e:
		print("    ... ERROR: file not copied. errror: '%s'" % e)
	except OSError as e:
		print("    ... ERROR: file not copied. errror: '%s'" % e)

def intall_dir(src, dst):
	"""
	Installs entire directory tree.
	"""
	try:
		copytree(src, dst)
		print("    ... done")
	except shutil.Error as e:
		print("    ... ERROR: directory not copied. errror: '%s'" % e)
	except OSError as e:
		print("    ... ERROR: directory not copied. errror: '%s'" % e)

def install(filename):
	"""
	Installs/copies files and directories from the repository
	to the current working directory.
	"""
	src = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
	dst = os.path.join(os.path.realpath('.'), filename)
	if not os.path.exists(src):
		print("    ... ERROR: source does not exist: " + src)
		return
	if os.path.exists(dst):
		print("    ... already exists.")
		return

	if os.path.isfile(src):
		install_file(src, dst)
	elif os.path.isdir(src):
		install_dir(src, dst)
	else:
		print("error: unable to handle source: " + src)

# feature specific functions

def sonar():
	print("    ... executing stuff for sonar")

#
# features list
#
# format:
#
#   feature-id: string, unique
#   - dependencies: list of feature ids which this feature depends
#     on (optional, prequisite)
#   - content: list of items (optional), possible types:
#     - string: a filename or directory name to copy
#     - function: a function to execeute during install
#
# note: feature also can work as 'packages', containing only dependencies
#
# TODO: this data could be in a JSON file, but let's not overcomplicate things for now
#
features = {
	'base' : {
		'content' : [
			'CMakeLists.txt',
			'LICENSE',
			'README.md',
		],
	},
	'doxygen' : {
		'content' : [
			'doxygen',
		],
	},
	'linux-build-script' : {
		'dependencies': [ 'base' ],
		'content' : [
			'build.sh',
			'configure.sh',
		],
	},
	'windows-build-script' : {
		'dependencies': [ 'base' ],
		'content' : [
			'build.bat',
			'setup-environment.bat',
		],
	},
	'visual-studio' : {
		'content' : [
			'create_VS_solution.bat.bat',
		],
	},
	'sonar' : {
		'content' : [
			'sonar-project.properties',
			sonar,
		],
	},
	'coverage' : {
		'content' : [
			'coverage.ignore',
			'cmake/modules/CodeCoverage.cmake',
		],
	},

	# packages
	'linux' : {
		'dependencies': [
			'linux-build-script',
		],
	},
	'windows' : {
		'dependencies': [
			'windows-build-script',
			'visual-studio',
		],
	},
}

# feature related functions

def check_features_existance(keys):
	"""
	Checks if the specified keys exist in the features list.
	If one or more features do not exist, they will be printed
	and the function return False.
	If all exist, the function returns True.
	"""
	errors = 0
	for key in keys:
		if not key in features:
			print("error: unknown feature: " + key)
			errors += 1
	if errors > 0:
		print("abort")
		return False
	return True

def prepare_dependency_graph(keys):
	"""
	Prepares the dependency graph from the list of keys.
	Rhis implementation cannot handle cyclic dependencies (stack overflow)
	"""
	graph = {}
	for key in keys:
		if 'dependencies' in features[key]:
			deps = features[key]['dependencies']
			if not check_features_existance(deps):
				exit(-1)
			graph[key] = deps
			graph.update(prepare_dependency_graph(deps))
		else:
			graph[key] = []
	return graph

# from http://stackoverflow.com/questions/15038876/topological-sort-python
def sort_topologically(graph):
	levels_by_name = {}
	names_by_level = defaultdict(set)

	def walk_depth_first(name):
		if name in levels_by_name:
			return levels_by_name[name]
		children = graph.get(name, None)
		level = 0 if not children else (1 + max(walk_depth_first(lname) for lname in children))
		levels_by_name[name] = level
		names_by_level[level].add(name)
		return level

	for name in graph:
		walk_depth_first(name)

	return list(takewhile(lambda x: x is not None, (names_by_level.get(i, None) for i in count())))

def warning_dangerous_working_directory():
	"""Prints warning about the danger of executing the script in its root directory."""
	print()
	print("error: not allowed to execute script with a potentionally")
	print("       operation in this directory. this script is supposed")
	print("       to be executed from the destination directory.")
	print()
	print("  example:")
	print()
	print("  $ mkdir project")
	print("  $ cd project")
	print("  $ ' + os.path.realpath(__file__) + ' --add linux sonar")
	print()
	exit(-1)

### main

dangerous_directory = os.path.dirname(os.path.realpath(__file__)) == os.path.realpath(os.getcwd())

parser = argparse.ArgumentParser(description='Project Template Creator')
parser.add_argument(
	'-l', '--list-features',
	help='lists features',
	action='store_true')
parser.add_argument(
	'-a', '--add',
	nargs='+',
	help='add features')
parser.add_argument(
	'-r', '--remove',
	nargs='+',
	help='removes features')

args = parser.parse_args()

if args.list_features:
	print("Features:")
	for f in features:
		print("- " + f)
	exit(0)

if args.remove:
	if dangerous_directory:
		warning_dangerous_working_directory()
	print("remove NOT IMPLEMENTED")
	exit(-1)

if args.add:
	if dangerous_directory:
		warning_dangerous_working_directory()
	print("add features")

	# topological sort and check of dependencies
	graph = prepare_dependency_graph(args.add)
	graph = sort_topologically(graph)

	# action, regrading topological sort/level
	for level in graph:
		for key in level:
			print("- adding: " + key)
			if 'content' in features[key]:
				for item in features[key]['content']:
					if isinstance(item, str):
						print("  - installing:", item)
						install(item)
					elif isfunction(item):
						print("  - calling:", item)
						item()

