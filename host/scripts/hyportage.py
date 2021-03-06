#!/usr/bin/python

import sys
import os
import utils
import logging
import multiprocessing
import click

import hyportage_db
import hyportage_translation
import smt_encoding
import reconfigure


__author__ = "Michael Lienhardt & Jacopo Mauro"
__copyright__ = "Copyright 2017, Michael Lienhardt & Jacopo Mauro"
__license__ = "GPL3"
__version__ = "0.5"
__maintainer__ = "Michael Lienhardt & Jacopo Mauro"
__email__ = "michael.lienhardt@laposte.net & mauro.jacopo@gmail.com"
__status__ = "Prototype"


def usage():
	"""Print usage"""
	print(__doc__)


@click.command()
@click.argument(
	'dir_portage',
	#help="the directory containing the portage files",
	type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=False, readable=True, resolve_path=True))
@click.argument(
	'dir_hyportage',
	#help="the directory containing the hyportage files (generate by this tool)",
	type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True, readable=True, resolve_path=True))
@click.argument(
	'dir_install',
	#help="the directory containing the hyportage files (generate by this tool)",
	type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True, readable=True, resolve_path=True))
@click.option(
	'--portage_files', '-i',
	nargs=2,
	default=("config.pickle", "packages"),
	help='the configuration file in which are stored the portage configuration data, plus the folder in which the egencache portage files can be found')
@click.option(
	'--hyportage_file', '-o',
	default="hyportage.pickle",
	help='the file in which are saved the hyportage data')
@click.option(
	'--generated_install_files', '-u',
	default=("emerge.sh", "package.use", "package.unmask", "package.accept_keywords"),
	help='the file in which are saved the installation script and use flag configuration')
@click.option(
	'--verbose', '-v',
	count=True,
	help="Print debug messages.")
@click.option(
	'--par', '-p',
	type=click.INT, default=-1,
	help='Number of process to use for translating the dependencies. Default all processors available - 1.')
@click.option(
	'--force',
	default=False,
	help='force the translation of the given packages.')
@click.option(
	'--simplify-mode',
	type=click.Choice(["default","individual"]), default="default",
	help='Simplify the dependencies together of just one by one (useful for getting explanations.')
@click.option(
	'--save-modality',
	type=click.Choice(["json", "gzjson", "marshal", "pickle"]), default="pickle",
	help='Saving modality. Currently, only pickle is supported, as "marshal does not support objects, and json is simply not efficient')
@click.option(
	'--mode',
	type=click.Choice(["update", "emerge"]), default="update",
	help='Temporary option that states if the tool is used in translate mode or reconfigure mode.')
@click.option(
	'--explain-modality',
	is_flag=True,
	help='Execution modality that tried to explain why a request can not be satisfied.')
@click.option(
	'--exploration',
	default="",
	help='enable the exploration mode of the tool. Valid values are lists of exploration modes, separated by commas. Valid exploration mode are "use", "mask" and "keywords"')
@click.option(
	'--hyvarrec-url',
	default="",
	help='Speficies the url (e.g., http://localhost:9000) to reach an instance of hyvar-rec. If not specified it is assumed that hyvar-rec is installed locally.')
@click.option(
	'--local-solver',
	default="",
	help='Specifies the command to call the solver on the local computer')

@click.argument(
	'atoms',
	nargs=-1)
def main(
		dir_portage,
		dir_hyportage,
		dir_install,
		portage_files,
		hyportage_file,
		generated_install_files,
		verbose,
		par,
		force,
		simplify_mode,
		save_modality,
		mode,
		explain_modality,
		exploration,
		hyvarrec_url,
		local_solver,
		atoms):

	##########################################################################
	# 1. OPTIONS
	##########################################################################

	# 1.1. verbose option
	log_level = logging.ERROR
	if verbose == 1: log_level = logging.WARNING
	elif verbose == 2: log_level = logging.INFO
	elif verbose >= 3: log_level = logging.DEBUG
	logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)
	logging.info("Verbose Level: " + unicode(verbose))
	logging.basicConfig(level=log_level)

	# 1.2. parallel process option
	if par != -1: available_cores = min(par, multiprocessing.cpu_count())
	else: available_cores = 1
	logging.info("number of available cores: " + str(available_cores))

	if available_cores > 1:
		concurrent_map = multiprocessing.Pool(available_cores).map
	else: concurrent_map = map

	todo_update_hyportage = mode == "update"
	todo_emerge = mode == "emerge"

	# 1.3. simplify_mode
	hyportage_db.simplify_mode = simplify_mode

	# 1.4. Exploration mode:
	exploration_use = "use" in exploration
	exploration_mask = "mask" in exploration
	exploration_keywords = "keywords" in exploration
	exploration_license = "license" in exploration
	if exploration_use: logging.info("  USE exploration enabled")
	if exploration_mask: logging.info("  MASK exploration enabled")
	if exploration_keywords: logging.info("  KEYWORDS exploration enabled")
	if exploration_license: logging.info("  LICENSE exploration enabled")

	# 1.5. Solver selection
	if local_solver:
		reconfigure.run_hyvar = lambda json_data: reconfigure.run_local_hyvar(
			json_data, explain_modality, local_solver.split(), par)
	elif hyvarrec_url: reconfigure.run_hyvar = lambda json_data: reconfigure.run_remote_hyvar(
			json_data, explain_modality, hyvarrec_url)
	else: reconfigure.run_hyvar = lambda json_data: reconfigure.run_local_hyvar(
			json_data, explain_modality, ["hyvar-rec"], par)

	##########################################################################
	# 2. SET THE FILE PATHS
	##########################################################################

	dir_portage = os.path.abspath(dir_portage)
	dir_hyportage = os.path.abspath(dir_hyportage)
	dir_install = os.path.abspath(dir_install)

	file_configuration, file_egencache_packages = portage_files
	path_configuration = os.path.join(dir_portage, file_configuration)
	path_egencache_packages = os.path.join(dir_portage, file_egencache_packages)

	path_db_hyportage = os.path.join(dir_hyportage, hyportage_file)

	file_install_script, file_use_flag_configuration, file_mask_configuration, file_keywords_configuration = generated_install_files
	path_install_script = os.path.join(dir_install, file_install_script)
	path_use_flag_configuration = os.path.join(dir_install, file_use_flag_configuration)
	path_mask_configuration = os.path.join(dir_install, file_mask_configuration)
	path_keywords_configuration = os.path.join(dir_install, file_keywords_configuration)

	##########################################################################
	# 3. COMPUTE WHAT TO DO
	##########################################################################

	# 3.1. load config
	hyportage_db.load_config(path_configuration, save_modality)

	# 3.2. compute what to update
	spl_name_set = set()
	loaded_spls = []
	if todo_update_hyportage:
		last_db_hyportage_update = os.path.getmtime(path_db_hyportage) if os.path.exists(path_db_hyportage) else 0.0
		egencache_files_to_load, spl_name_set = hyportage_translation.compute_to_load(
			last_db_hyportage_update, force, path_egencache_packages)
		loaded_spls = hyportage_translation.load_spl_to_load(concurrent_map, egencache_files_to_load)

	##########################################################################
	# 4. LOAD THE HYPORTAGE DATABASE
	##########################################################################

	hyportage_db.load_hyportage(path_db_hyportage, save_modality)

	##########################################################################
	# 5. UPDATE THE HYPORTAGE DATABASE IF NECESSARY
	##########################################################################

	if todo_update_hyportage:
		logging.info("updating hyportage...")

		# update the hyportage spl database
		spl_added_list, spl_removed_list, spl_groups_added, spl_groups_updated, spl_groups_removed =\
			hyportage_translation.update_mspl_and_groups(hyportage_db.mspl, hyportage_db.spl_groups, spl_name_set, loaded_spls)

		# update the hyportage pattern repository
		pattern_added, pattern_updated_containing, pattern_updated_content, pattern_removed =\
			hyportage_translation.update_pattern_repository(hyportage_db.pattern_repository, spl_added_list, spl_removed_list)

		# update the revert dependencies
		changed_ids_spl_set = set(spl_added_list)
		pattern_added_updated = pattern_added | pattern_updated_containing | pattern_updated_content
		changed_ids_spl_set.update(hyportage_translation.update_revert_dependencies(
			hyportage_db.pattern_repository, pattern_added_updated, pattern_removed))

		# reset the implicitly added use flags
		changed_ids_spl_set.update(hyportage_translation.reset_implicit_features(
			hyportage_db.mspl,
			hyportage_db.mspl_config.new_use_declaration_eapi4, hyportage_db.mspl_config.new_use_declaration_eapi5))

		# update the id repository
		hyportage_translation.update_id_repository(hyportage_db.id_repository, changed_ids_spl_set, spl_removed_list)

		# update the visibility information
		hyportage_translation.update_visibility(
			hyportage_db.mspl, spl_added_list,
			hyportage_db.mspl_config.new_masks, hyportage_db.mspl_config.new_keywords_config, hyportage_db.mspl_config.new_licenses_config)

		# check if the main config of the spl must be regenerated
		# COMMENTED OUT: the USE variable is changed every time the tool is called,
		#  so it is efficiency-damaging to store the use selection of every spl
		#hyportage_translation.update_use_flag_selection(
		#	hyportage_db.mspl, spl_added_list,
		#	hyportage_db.mspl_config.new_keywords_config, hyportage_db.mspl_config.new_use_flag_config)

		# update the smt
		implicit_use_flag_changed = hyportage_db.mspl_config.new_use_declaration_eapi4 or hyportage_db.mspl_config.new_use_declaration_eapi5
		pattern_added_updated_content = pattern_added | pattern_updated_content
		hyportage_translation.update_smt_constraints(
			hyportage_db.pattern_repository, hyportage_db.mspl, hyportage_db.spl_groups,
			pattern_added_updated_content, spl_added_list, implicit_use_flag_changed)

		# save the hypotage database
		has_changed_config = implicit_use_flag_changed or hyportage_db.mspl_config.new_masks or\
			hyportage_db.mspl_config.new_keywords_config or hyportage_db.mspl_config.new_licenses_config or\
			hyportage_db.mspl_config.new_use_flag_config
		has_changed_hyportage = bool(spl_added_list) or bool(spl_removed_list) or has_changed_config

		if has_changed_config: hyportage_db.save_configuration(path_configuration, save_modality)
		if has_changed_hyportage: hyportage_db.save_hyportage(path_db_hyportage, save_modality)


	##########################################################################
	# 6. RUN RECONFIGURE IF NECESSARY
	##########################################################################

	if todo_emerge:
		logging.info("computing a new system configuration... " + str(atoms))
		# cleaning the atoms from the repository annotation
		clean_atoms = set()
		for atom in atoms:
			if "::" in atom:
				logging.warning("the atom \"" + atom + "\" is tagged with a repository annotation. trimming it")
				clean_atoms.add(atom.split("::", 1)[0])
			else: clean_atoms.add(atom)
		atoms = clean_atoms
		# compute what to install
		root_spls, request_constraint = reconfigure.process_request(
			hyportage_db.pattern_repository, hyportage_db.id_repository, hyportage_db.config, atoms)

		if not bool(root_spls):
			logging.info("nothing to do")
			sys.exit(0)

		# get the transitive closure of the spls
		all_spls = reconfigure.get_dependency_transitive_closure(
			hyportage_db.pattern_repository, hyportage_db.mspl, root_spls)

		# solve these spl, with the request constraint
		solution = reconfigure.solve_spls(
			hyportage_db.id_repository, hyportage_db.config, hyportage_db.mspl, hyportage_db.spl_groups,
			all_spls, request_constraint, exploration_use, exploration_mask, exploration_keywords,
			explain_modality)

		if solution is None:
			logging.error("Non valid configuration found")
			logging.error("exiting")
			sys.exit(-1)

		if verbose >= 3:
			path_new_configuration = os.path.join(dir_install, "new_configuration.pickle")
			logging.debug("Saving the generated configuration in \"" + path_new_configuration + "\"")
			utils.store_data_file(path_new_configuration, solution)

		# write the installation files
		reconfigure.generate_installation_files(
			hyportage_db.mspl,
			path_install_script, path_use_flag_configuration, path_mask_configuration, path_keywords_configuration,
			hyportage_db.config.installed_packages, solution)

	logging.info("Execution succesfully terminated")

	# cleanup, because of Python GC bugs...
	concurrent_map = None
	smt_encoding.cleanup()
	sys.exit(0)


##

if __name__ == "__main__":
	if os.name == 'nt':
		multiprocessing.freeze_support()
	main()

