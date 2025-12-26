#!/usr/bin/python3
# -*- coding: utf-8 -*-

####
# Copyright (C) 2017-2020 Kim Gerdes
# kim AT gerdes. fr
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU Affero General Public License (the "License")
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# See the GNU General Public License (www.gnu.org) for more details.
#
# You can retrieve a copy of of version 3 of the GNU Affero General Public License
# from http://www.gnu.org/licenses/agpl-3.0.html 
####

# dependencies:
# pip3 install pandas seaborn matplotlib tqdm psutil
# pip3 install psutil tqdm pandas

#import datetime, codecs, time, sys, os, glob, re, numpy, multiprocessing, psutil, tqdm
import time, sys, os, re, multiprocessing, psutil, tqdm, collections
from numpy.lib.arraysetops import isin
from pathlib import Path
import pandas as pd
import numpy as np 

import conll

# from Menzerath import newmenzerath,dataAnalysis  # Moved to old/ - only needed for legacy functions


def readInLanguageNames():
	"""
	Read language names and groups from TSV files.
	Returns empty dicts if files don't exist (notebooks will use Google Sheets data instead).
	"""
	langNames = {}
	langnameGroup = {}
	
	# Read languageCodes.tsv (main ISO language codes)
	try:
		with open("languageCodes.tsv") as langcodef:
			langcodef.readline()  # skip header
			for li in langcodef:
				lis = li.strip().split('\t')
				if len(lis) >= 2:
					langNames[lis[0]] = lis[-1]
	except FileNotFoundError:
		print("Warning: languageCodes.tsv not found")
	
	# Read myLanguageCodes.tsv (custom overrides for languages with spaces)
	try:
		with open('myLanguageCodes.tsv') as f:
			mylangNames = {li.split('\t')[0]: li.split('\t')[1] for li in f.read().strip().split('\n') if '\t' in li}
			langNames = dict(langNames, **mylangNames)  # merge, with custom names overriding
	except FileNotFoundError:
		pass  # optional file
	
	# Read languageGroups.tsv (language family/group assignments)
	try:
		with open('languageGroups.tsv') as f:
			langnameGroup = {li.split('\t')[0]: li.split('\t')[1] for li in f.read().strip().split('\n') if '\t' in li}
	except FileNotFoundError:
		pass  # optional file
	
	return langNames, langnameGroup

# Load language data at module import time (can be overridden by notebooks using Google Sheets)
langNames, langnameGroup = readInLanguageNames()


def getAllConllFilesGroup(basefolder):
	"""
	for a given basefolder, 
	gives back a dictionary code -> list of files under the code
	{"en":["/dqsdf/en.partut.conllu", ...] }
	"""
	langConllFiles = {}
	doc_list = [d for d in sorted(os.listdir(basefolder))]
	for doc_name in doc_list:
		conll_ls = [os.path.join(basefolder, doc_name,f) for f in os.listdir(os.path.join(basefolder, doc_name)) if f.endswith(".conllu") and "not-to-release" not in doc_name]
		doc_name_to_la = {
			'parisstories': 'fr',
			'SUD_French-Sequoia': 'fr',
			'SUD_Naija-NSC': 'pcm',
			'SUD_Chinese-PatentChar': 'zh',
			'chinese-beginner.a2.msud.conllu': 'zh',
			'chinese-beginner.b1.sud.conllu': 'zh',
			'corpushaitien-24.conllu': 'ht'
		}
		
		if conll_ls:
			la = os.path.basename(conll_ls[0]).split('_', 1)[0].lower()
			la = doc_name_to_la.get(la, la)
			la = doc_name_to_la.get(doc_name, la)
			langConllFiles[la] = langConllFiles.get(la, []) + conll_ls
	return langConllFiles


def checkLangCode(langConllFiles, langNames=None, verbose=False):
	if verbose:
		for lang, files in sorted(langConllFiles.items()):
			print(lang, files)
	my_lang_names = langNames or readInLanguageNames()[0]
	
	to_add = [la for la in langConllFiles if la not in my_lang_names ]
	names_with_space = [f"{la}: {my_lang_names.get(la, la)}" for la in langConllFiles if ' ' in my_lang_names.get(la, la)]
	
	print('Language with space:\n', '\n'.join(names_with_space))
	print('Language to add:', to_add)
	if langNames: # function called from the notebook, where langNames is taken from the gg sheet
		return names_with_space, to_add
	else:
		assert(len(to_add) == 0)

def checkLangGroups(langConllFiles, langNames=None, langnameGroup=None):
	my_lang_names = langNames or readInLanguageNames()[0]
	my_langname_groups = langnameGroup or readInLanguageNames()[1]
	# langNames, langnameGroup = readInLanguageNames()
	to_add = [(la, my_lang_names.get(la, la)) for la in langConllFiles if my_lang_names[la] not in my_langname_groups ]
	# print(333, to_add)
	# print(langConllFiles)
	print(len(to_add),'language groups to add:\n', '\n'.join([f"{la[0]}: {langNames.get(la[0], la[0])}" for la in to_add]))
	if langnameGroup:
		return to_add
	else:
		assert(len(to_add) == 0)

def getAllConllFiles(basefolder, groupByLanguage=True):
	"""
	for a given basefolder, 
	gives back a dictionary code -> list of files under the code
	{"en":["/dqsdf/en.partut.conllu", ...] }
	"""
	if groupByLanguage:
		return getAllConllFilesGroup(basefolder)
	langConllFiles={}
	for dirpath, dirnames, files in os.walk(basefolder):
		for f in files:
			if f.endswith(".conllu") and "not-to-release" not in dirpath:
				# if groupByLanguage:	lcode=re.split(r"\W|_",f)[0] # now all different treebanks for iso-639-3english are under 'en'	
				lcode=re.split(r"\-",f)[0] # now the codes are for example 'en', 'en_partut', 'en_lines'				
				#if lcode in langConllFiles: print lcode,f
				langConllFiles[lcode]=langConllFiles.get(lcode,[])+[os.path.join(dirpath,f)]
	#print langConllFiles
	return langConllFiles

relationsplit = re.compile(r'[:|@|$|/]')
# relationsplit = re.compile(r'[:|$]')


# TODO: add this combination
 #elif x_type == "nominal":
        #data = df[df["headpos"].isin(["NOUN", "PROPN"])]
    #elif x_type == "content":
        #data = df[df["headpos"].isin(["NOUN", "PROPN", "ADJ", "ADV", "VERB"])]




def average(lis, rounding):
	try:
		return round(sum(lis)*1.0/len(lis),rounding)
	except:
		return 0

#types=["cat","func","f","f-dist","f-dist-SD","f-dist-noroot","f-dist-noroot-SD","cfc","cf","fc","funcTIMESdist","positive-direction", "cfc-dist", "cf-dist", "posdircfc", "posdircf", "abs-f-dist-noroot"]
types=[ "cat",
	"f",
	"f-dist",
	"f-dist-abs",
	"f-dist-noroot",
	"cfc",
	"cf",
	"fc",
	"positive-direction", 
	"posdircfc", 
	"posdircf", 
	"cfc-dist", 
	"cf-dist",
	"abs-f-dist-noroot",
	"height"]


distancetypes={"f-dist":"f", "f-dist-abs": "f","f-dist-noroot":"f","funcTIMESdist":"f", "cfc-dist":"cfc", "cf-dist":"cf", "abs-f-dist-noroot":"f"} # pointing to the corresponding frequency type
distancetypes={t:distancetypes[t] for t in distancetypes if t in types}
sdtypes={"f-dist-SD":"f-dist","f-dist-noroot-SD":"f-dist-noroot"}
sdtypes={t:sdtypes[t] for t in sdtypes if t in types}
multypes={"funcTIMESdist":"f", "positive-direction":"f", "posdircfc":"cfc", "posdircf":"cf"} # pointing to the corresponding frequency type
multypes={t:multypes[t] for t in multypes if t in types}

udcats="ADJ ADP PUNCT ADV AUX SYM INTJ CCONJ X NOUN DET PROPN NUM VERB PART PRON SCONJ".split()

udfuncs="nsubj obj iobj csubj ccomp xcomp obl vocative expl dislocated advcl advmod discourse aux cop mark nmod appos nummod acl amod det clf case conj cc fixed flat compound list parataxis orphan goeswith reparandum punct root dep".split()
sudfuncs="appos vocative expl dislocated discourse dep mot comp subj mod unk udep det clf case conj cc fixed flat compound list parataxis orphan goeswith reparandum punct root aff".split() # dep_SUD FAIL_advcl _ #add aff for sud2.8/beja

#thesefuncs = sudfuncs
#thesefuncs = udfuncs

verbose=True
#verbose=False

errorfile = open("errors.tsv",'w')

def makeStatsOneThread(info):
	"""
	computes the stats for one language
	
	"""
	lcode, conllfile, skipFuncs, rounding = info
	if verbose: 
		print(lcode, "...")
		print(multiprocessing.current_process())
	
	
	typesDics={} # temp dico for each language: {"func"(type) ->  {"subj":33, ...}  } - later stored in combined typesDics[ty]["lang"][lcode] :::
	for ty in types:
		typesDics[ty]={}
		typesDics[ty]["all"]={}
		typesDics[ty]["lang"]={lcode:{}}
	typesDics["height"]["all"]["treeHeight"] = None #register treeHeight in typesDics

	# 1. collects all the information from the trees:
	# for current conllfile for the current language
	print('\n',conllfile, '\n')
	if verbose: print('processing',conllfile, multiprocessing.current_process())
	trees = conll.conllFile2trees(conllfile)
	langcode=lcode.split("_")[0]
	if verbose: print("doing",len(trees),"trees of",lcode,langNames[langcode], multiprocessing.current_process()) # [:2]
	titi=time.time()
		

	for tree in trees:  #current sentence
		typesDics["height"]["lang"][lcode]["treeHeight"] = typesDics["height"]["lang"][lcode].get("treeHeight",[])+[tree.treeHeight()]
		
		for ni,node in tree.items(): #id, info(t,lemma tag etc) for current token
			# POS tag = ExtPos if ExPos exist else upos
			tag = node.get('ExtPos', node["tag"] ).strip()
			if tag in udcats:
				typesDics["cat"]["all"][tag]=typesDics["cat"]["all"].get(tag,0)+1
				typesDics["cat"]["lang"][lcode][tag]=typesDics["cat"]["lang"][lcode].get(tag,0)+1
			else:
				tag="X"
			for gi in node["gov"]:#root id of current sentence
				func=node["gov"][gi] #DEPREL
				#print("\n in node gov : \n gi = ",gi, "\n node gov gi = ", func )
				#print("ni-gi = ", ni-gi) #position of current token in relation to the root
				syntfunc = func.split("@")[0]

				simpfunc=relationsplit.split(func)[0] #DEPREL
				funcs = [simpfunc]
				if syntfunc!=simpfunc: #difference between syntfunc & simpfunc?
					funcs+=[syntfunc]
				if simpfunc in skipFuncs:
					break
				if simpfunc not in thesefuncs: #udfuncs+sudfuncs:
					print(type(ni))
					if '.' in str(ni) and simpfunc == '_':
						break
					print("\nweird simple function",simpfunc,"    id == ", ni)
					errorfile.write('\t'.join([simpfunc,conllfile])+'\n')
					# print("\ntoken id == ", ni, "\nin this sentences: \n ", tree.conllu())
					#skip=True
					break
				for f in funcs:
					#typesDics["func"]["lang"][lcode][func]=typesDics["func"]["lang"][lcode].get(func,0)+1
					typesDics["f"]["lang"][lcode][f]=typesDics["f"]["lang"][lcode].get(f,0)+1

					typesDics["f-dist"]["lang"][lcode][f]=typesDics["f-dist"]["lang"][lcode].get(f,[])+[ni-gi]
					typesDics["f-dist-abs"]["lang"][lcode][f]=typesDics["f-dist-abs"]["lang"][lcode].get(f,[])+[abs(ni-gi)]

					if gi: 
						typesDics["f-dist-noroot"]["lang"][lcode][f]=typesDics["f-dist-noroot"]["lang"][lcode].get(f,[])+[ni-gi]
						typesDics["abs-f-dist-noroot"]["lang"][lcode][f]=typesDics["abs-f-dist-noroot"]["lang"][lcode].get(f,[])+[abs(ni-gi)]
						
					# POS tag = ExtPos if ExPos exist else upos
					gtok = tree.get(gi,{"tag":"ROOT"})
					gc = gtok.get('ExtPos' , gtok["tag"]).strip() 

					#print("\n tree gi tag root = ", tree.get(gi,{"tag":"ROOT"})) #info(t,lemma tag etc) of root
					if gc not in udcats: gc="X"
						
					fc = f+"-"+tag
					cfc = gc+"-" +fc
					cf = gc+"-" +f
						
					typesDics["cfc"]["lang"][lcode][cfc]=typesDics["cfc"]["lang"][lcode].get(cfc,0)+1
					typesDics["fc"]["lang"][lcode][fc]=typesDics["fc"]["lang"][lcode].get(fc,0)+1
					typesDics["cf"]["lang"][lcode][cf]=typesDics["cf"]["lang"][lcode].get(cf,0)+1
					typesDics["cfc-dist"]["lang"][lcode][cfc]=typesDics["cfc-dist"]["lang"][lcode].get(cfc,[])+[ni-gi]
					typesDics["cf-dist"]["lang"][lcode][cf]=typesDics["cf-dist"]["lang"][lcode].get(cf,[])+[ni-gi]
					#typesDics["func"]["all"][func]=None 
					typesDics["f"]["all"][f]=None 
					typesDics["f-dist"]["all"][f]=None
					typesDics["f-dist-abs"]["all"][f]=None
					typesDics["cfc-dist"]["all"][cfc]=None
					typesDics["cf-dist"]["all"][cf]=None
					#typesDics["f-dist-SD"]["all"][f]=None 
					if gi: typesDics["f-dist-noroot"]["all"][f]=None 
					if gi: typesDics["abs-f-dist-noroot"]["all"][f]=None 
					#if gi: typesDics["f-dist-noroot-SD"]["all"][f]=None 
					typesDics["cfc"]["all"][cfc]=None 
					typesDics["fc"]["all"][fc]=None 
					typesDics["cf"]["all"][cf]=None 
					#typesDics["funcTIMESdist"]["all"][f]=None
					typesDics["positive-direction"]["all"][f]=None
					typesDics["posdircfc"]["all"][cfc]=None
					typesDics["posdircf"]["all"][cf]=None

				
	if verbose: 
		print("current speed:",int((time.time()-titi)/len(trees)*1000000),"seconds per mtrees of",langNames[langcode])
		print('\t\t',lcode, "done",multiprocessing.current_process())
	#for ty in sdtypes: # compute sd (before computing averages)
		#for simpfunc in sorted(typesDics[ty]["all"]):
			#typesDics[ty]["lang"][lcode][simpfunc]=round(numpy.std(typesDics[sdtypes[ty]]["lang"][lcode].get(simpfunc,[])),rounding)
	
	# 2. compute pourcentages of right-pointing links and averages
	
	return typesDics, lcode

def getStatLang(typesDics, lcode, rounding):
	for f in sorted(typesDics["positive-direction"]["all"]): # average percentage of simple relations going to the right
		dists = typesDics["f-dist"]["lang"][lcode].get(f,[])
		if len(dists): posdir=100.0*len([d for d in dists if d>0])/len(dists)
		else: posdir= np.nan#-1
		typesDics["positive-direction"]["lang"][lcode][f]=posdir

	for cfc in sorted(typesDics["posdircfc"]["all"]): # average percentage of cfc going to the right
		dists = typesDics["cfc-dist"]["lang"][lcode].get(cfc,[])
		if len(dists): posdir=100.0*len([d for d in dists if d>0])/len(dists)
		else: posdir= np.nan #-1
		typesDics["posdircfc"]["lang"][lcode][cfc]=posdir

	for cf in sorted(typesDics["posdircf"]["all"]): # average percentage of cf going to the right
		dists = typesDics["cf-dist"]["lang"][lcode].get(cf,[])
		if len(dists): posdir=100.0*len([d for d in dists if d>0])/len(dists)
		else: posdir= np.nan #-1
		typesDics["posdircf"]["lang"][lcode][cf]=posdir
		
	for ty in distancetypes: # compute average of distances. before: list of values, after: average
		for f in sorted(typesDics[ty]["all"]):
			typesDics[ty]["lang"][lcode][f]=average(typesDics[ty]["lang"][lcode].get(f,[]),rounding)
	
	#treeHeight average
	typesDics["height"]["lang"][lcode]["treeHeight"] = average(typesDics["height"]["lang"][lcode].get("treeHeight",[]),rounding)
	
	# if verbose: print("____",lcode,"done",multiprocessing.current_process())
	
def _append_res(d,u):
	# combine d and u, values in d and u are list or None
	for k, v in u.items():
		if isinstance(v, collections.abc.Mapping):
			r = _append_res(d.get(k, {}), v)
			d[k] = r
		else:
			if isinstance(u[k], list):
				d[k] = d.get(k, [])+ u[k]
			elif isinstance(u[k], int):
				d[k] = d.get(k, 0)+ u[k]
			elif u[k] is None or np.isnan(u[k]):
				d[k] = d.get(k, np.nan)
			else:
				print('unknown type:',type(u[k]))
	return d


def makeStatsThreaded(langConllFiles, skipFuncs=['root','compound','fixed','flat','conj'], skipLangs=['kk','sa','ug','lt','be','cop','ta'], rounding=5, colons="langname", analysisfolder='.'):
	
	ti = time.time()
	Path(analysisfolder).mkdir(parents=True, exist_ok=True)

	#pool = multiprocessing.Pool(psutil.cpu_count()) # *2 -1
	typesDics={} # global dic: {"func" -> { "all":{ "subj":234, ... }, "lang":{"en":{"subj":33, ...}} }
	for ty in types:
		typesDics[ty]={}
		typesDics[ty]["all"]={}
		typesDics[ty]["lang"]={}

	# count file numbers for each language
	langFcount = {}
	
	# infotodo contains all the information to be computed: (lcode, fpath, skipFuncs, rounding), fpath is the path of a single conll file
	infotodo = [
        (lcode, fpath, skipFuncs, rounding) \
            for lcode in langConllFiles.keys() for fpath in langConllFiles[lcode] if lcode not in skipLangs
            ]

	pbar = tqdm.tqdm(total=len(infotodo))
	# results = []
	
	with multiprocessing.Pool(psutil.cpu_count()) as pool:
		for res_la in pool.imap_unordered(makeStatsOneThread, infotodo):
			pbar.update()
			res, lcode = res_la
			_append_res(typesDics, res)
			# results.append(res)
			langFcount[lcode] = langFcount.get(lcode,0) + 1

			# if all files of lcode are computed
			if langFcount[lcode] == langITEM.get(lcode):
				getStatLang(typesDics, lcode, rounding)
		
	print("it took",time.time()-ti,"seconds")
	print("\n\n\n====================== finished reading in. \n combining...")

	# combining special type dictionaries:
	specdic=distancetypes.copy()
	specdic.update(sdtypes)
	specdic.update(multypes)
	# for tdi in results:
	# 	_append_res(typesDics, tdi)
	# 	print(typesDics['f']['lang'].keys())
	
	print("it took",time.time()-ti,"seconds")
	print("writing...")
	
	

	# for lcode in sorted(langConllFiles):
	# 	getStatLang(typesDics, lcode, rounding)
	
	for ty in types:
		print(ty)
		with open(os.path.join(analysisfolder,ty+".tsv"),"w") as out:
			if colons=="langname": idcolon=["name"]
			#elif colons=="langcode": idcolon=["lang"]
			else: idcolon=["lang","name"]
			out.write("\t".join(idcolon+sorted(typesDics[ty]["all"])+["total"])+"\n") # title line
			for lcode in sorted(langConllFiles): # for each language
				if lcode in typesDics[ty]["lang"]:
					langname=langNames[lcode.split("_")[0]]
					if colons=="langname": idcolon=[langname]
					else: idcolon=[lcode,langname]
					if ty in specdic: # distances are already averages, they are written as such. only the "total" is complicated:
						# total: rather average direction/distance of functions. to compute it:
						# for each function: get number of times the simpfunc exists * average distance of this simpfunc
						# add all that and divide by number of relations in total. total is not necessarily useful for sdtypes
						weighted = [typesDics[specdic[ty]]["lang"][lcode].get(x,0)*typesDics[ty]["lang"][lcode].get(x,0) for x in sorted(typesDics[ty]["all"])]
						# type(np.nan) is float, apply np.isnan to exclude nan
						# if sum(np.isnan(weighted)>0):
						sum_w = sum(weighted)
						if np.isnan(sum_w):
							total=sum([i if not np.isnan(i) else 0 for i in weighted])/sum(typesDics[specdic[ty]]["lang"][lcode].values())
						else:
							total= sum_w /sum(typesDics[specdic[ty]]["lang"][lcode].values())
						out.write("\t".join(idcolon+[str(typesDics[ty]["lang"][lcode].get(x,float('nan'))) for x in sorted(typesDics[ty]["all"])]+[str(total)])+"\n")
					elif ty == "height": #average tree height of each language
						height = str(typesDics[ty]["lang"][lcode].get("treeHeight", float('nan')))
						total = height #there is only a measure "height" in treeHeight so total == height
						out.write("\t".join(idcolon+ [height, total])+"\n")	
					else:# frequencies (relative frequencies because divided by total number of links)
						total=sum(typesDics[ty]["lang"][lcode].values())
						out.write("\t".join(idcolon+[str(round(typesDics[ty]["lang"][lcode].get(x,float('nan'))*1.0/total,rounding)) for x in sorted(typesDics[ty]["all"])]+[str(total)])+"\n")
					
	print("it took",time.time()-ti,"seconds =",(time.time()-ti)/60,"minutes",(time.time()-ti)/60/60,"hours in total")
	


#syntactic = "nsubj csubj subj obj iobj ccomp xcomp aux cop case mark cc advmod advcl obl dislocated vocative expl nummod nmod amod discourse acl det clf".split()
#skipFuncs=['root']	
	
def simpleStat(tree):
	"""
	takes a conll tree
	returns 
	- total nb of relations
	- nb of syntactic relations
	- total average dep dist
	- average syntactic dep dist
	- total % right branching
	- syntactic % right branching
	"""
	
	totdist, depdist, totright, depright = [], [], 0, 0
	for ni,node in tree.items():
		for gi in node["gov"]:
			func=node["gov"][gi]
			simpfunc=func.split(":")[0]
		if simpfunc not in skipFuncs:
			totdist += [abs(ni-gi)]
			if ni>gi: totright += 1
			if simpfunc in syntactic:
				depdist += [abs(ni-gi)]
				if ni>gi: depright += 1
	return len(totdist), len(depdist), sum(totdist)/len(totdist), sum(depdist)/len(depdist), len(totright)/len(totdist)*100.0, len(depright)/len(depdist)*100.0



def addfilePrefix(foldername, prefix):
	for dirpath, dirnames, files in os.walk(foldername):
		for f in files:
			os.rename(dirpath + f, dirpath + prefix + "_"+f)

def maincomputation(analysisfolder, langConllFiles):
	""" 
	langCode2compute must be part of langConllFiles.keys() 
	"""
	# analysisfolder = conlldatafolder + '-analysis'
	if len(langConllFiles) == 0:
		print("empty folder error ", langConllFiles, "\n")
		return
	
	for code in langConllFiles.keys():
		if code not in langNames : 
			print("can't find", code, langConllFiles[code]) #ajouter dans les tsv
		if ' ' in langConllFiles[code]:
			print('consider replacing this language name:',code,langConllFiles[code])

	#return #print the unknown codes and ' ' at once then stop before makeStatsThreaded, uncomment if nothing printed 
	makeStatsThreaded(langConllFiles, skipFuncs=['root'], skipLangs=[], analysisfolder=analysisfolder)
	#makeStatsThreaded(langConllFiles, skipFuncs=['root','compound','fixed','flat','conj','appos', 'vocative', 'expl', 'dislocated', 'discourse', 'dep', 'mot', 'comp','aff', 'list', 'parataxis', 'orphan', 'goeswith', 'reparandum', 'punct', 'mod', 'unk', 'udep', 'det', 'clf', 'case'], skipLangs=[], analysisfolder=analysisfolder)
	
def computeMenzerath(langConllFiles, analysisfolder, version):
	#menzerath
	print("\nmenzerath begin: \n")
	menzFile = "Menzerath/longfile/abc.languages.longfile.v{}.tsv".format(version)
	newmenzerath.newnewheavymenz(langConllFiles, menzFile)
	#transform to typometrics format
	main_dataframe = pd.read_csv(menzFile, sep="\t")
	outfile = analysisfolder + "/abc.languages.v{}_typometricsformat.tsv".format(version)
	dataAnalysis.makeLargeTable(main_dataframe, outfile)
	
	
if __name__ == "__main__":
	#check if thesefuncs = udfuncs or sudfuncs to adapte with input folder
	#dict in which key = abbr of langue name, val=relevant files' names 
	conlldatafolder = "ud-treebanks-v2.14"
	langConllFiles = getAllConllFiles(conlldatafolder, groupByLanguage=True) 
	checkLangCode(langConllFiles)
	langList = sorted(langConllFiles.keys())
	langITEM = {la: len(langConllFiles[la]) for la in langList }
	analysisfolder = conlldatafolder + '-analysis'
	
	thesefuncs = sudfuncs
	assert(len(set(thesefuncs)) == len(thesefuncs)) # no duplicates
	# maincomputation("SUD_Beja-NSC", version = "2.8_sud")
	maincomputation( analysisfolder, langConllFiles)
	computeMenzerath(langConllFiles, analysisfolder, version = "2.13_sud" )

	# thesefuncs = udfuncs
	#maincomputation("weirdfct",version = "2.8_ud_test")
	#maincomputation("UD_Afrikaans-AfriBooms",version = "2.9_ud_test")
	
	# maincomputation("ud-treebanks-v2.10",version = "2.10_ud")
	#langConllFiles = {a:v for a,v in langConllFiles.iteritems() if "fr" in a}
