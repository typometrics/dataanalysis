#!/usr/bin/python3
# -*- coding: utf-8 -*-

####
# Copyright (C) 2009-2020 Kim Gerdes
# kim AT gerdes. fr
# http://arborator.ilpga.fr/
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

import collections, re
#debug=False
debug=True


class Tree(dict):
	"""
	just a dictionary that maps nodenumber->{"t":"qsdf", ...}
	moreover: 
		sentencefeatures is a dictionary with sentence wide information, eg "comments":"comment line content"
			there is a special key: _comments used for comments that are not of the form x = yyy, they are stored as such
		words is not necessarily a list of tokens: it contains the actual correctly spelled words, ie. the hyphen (1-2) lines
	"""
	def __init__(self, *args, **kwargs):
		self.update(*args, **kwargs)
		self.sentencefeatures={}
		self.rooti=None
		self.words=[]
		

	def __getitem__(self, key):
		val = dict.__getitem__(self, key)
		#print 'GET', key
		return val

	def __setitem__(self, key, val):
		#print 'SET', key, val
		dict.__setitem__(self, key, val)

	def __repr__(self):
		#dictrepr = dict.__repr__(self)
		#return '%s(%s)' % (type(self).__name__, dictrepr)
		return self.conllu()
		#return "\n".join(["Tree: "+self.sentence()]+[f+": "+v for f,v in self.sentencefeatures.items()]+[str(i)+": "+self[i].get("t","")+"\t"+str(self[i]) for i in self])
	
	def update(self, *args, **kwargs):
		#print 'update', args, kwargs
		for k, v in dict(*args, **kwargs).items():
			self[k] = v
	
	def sentence(self):
		if self.words==[]:
			self.words = [self[i].get("t","") for i in sorted(self)]
		return " ".join(self.words)
	
	def conllu(self):
		morphoSynt= ['Abbr', 'AbsErgDatNumber', 'AbsErgDatPerson', 'AbsErgDatPolite', 'AdpType', 'AdvType', 'Animacy', 'Aspect', 'Case', 'Clusivity', 'ConjType', 'Definite', 'Degree', 'Echo', 'ErgDatGender', 'Evident', 'Foreign', 'Gender', 'Hyph', 'Mood', 'NameType', 'NounClass', 'NounType', 'NumForm', 'NumType', 'NumValue', 'Number', 'PartType', 'Person', 'Polarity', 'Polite', 'Poss', 'PossGender', 'PossNumber', 'PossPerson', 'PossedNumber', 'Prefix', 'PrepCase', 'PronType', 'PunctSide', 'PunctType', 'Reflex', 'Style', 'Subcat', 'Tense', 'Typo', 'VerbForm', 'VerbType', 'Voice']
		specialFeatures=["t", "lemma", "tag", "tag2", "xpos", "egov", "id", "index", "gov", "kids", "govrel", "span", "bastards", "direct_span", "all_kids"]
		treestring = ""
		for stftkey in sorted(self.sentencefeatures):
			if stftkey=="_comments":
				if self.sentencefeatures[stftkey].endswith("#"): self.sentencefeatures[stftkey]=self.sentencefeatures[stftkey][:-1]
				treestring+="# "+self.sentencefeatures[stftkey]
			else:
				treestring+="# "+stftkey+" = "+self.sentencefeatures[stftkey]+"\n"	
		for i in sorted(self):
			node = self[i]                        
			govs=node.get("gov",{})
			govk = sorted(govs)
			if govk:
				gk,gv = str(govk[0]),govs.get(govk[0],"_")
			else:
				gk,gv = "_","_"
			treestring+="\t".join([
				str(i), 
				node.get("t","_"), 
				node.get("lemma",""), 
				node.get("tag","_"), 
				node.get("xpos","_"), 
				"|".join( [ a+"="+v for a,v in sorted(node.items()) if a in morphoSynt]) or "_", 
				gk,
				gv,
				"|".join( [ str(g)+":"+govs.get(g,"_") for g in govk[1:] ] + [ str(a)+":"+v for a,v in node.get("egov",{}).items() ] ) or "_", 
				"|".join( [ a+"="+v for a,v in sorted(node.items()) if a not in morphoSynt+specialFeatures])  or "_" 
				])+ "\n"
				
		return treestring
	
	def addkids(self, exclude=[]):
		"""
		adds dictionary to each node: 'kids': {1: 'dobj', 2: 'aux', 3: 'nsubj', 5: 'prep', 9: 'punct'}
		adds self.rootnode
		"""
		for i in self:
			self[i]['kids'] = {}
		for i in self:
			for g,f in self[i].get("gov",{}).items():
				if f in exclude: continue
				if g>0: self[g]["kids"][i]=f #g = HEAD, i = ID, f = DEPREL 
				else: self.rootnode=i
					
				
	def addspan(self, exclude=[], compute_bastards=False):
		"""
		adds the list of direct and indirect dependents to each node
		needs that kids have been added first
		if compute_bastards is True:
			adds 'bastards', 'direct_span', 'all_kids' to each node
		"""
		self.addkids(exclude)
		for i in self:
			self[i]['span'] = sorted(self.span(i)) #all direct & indirect dependents of node i
			
		if compute_bastards:
			# Initialize new fields
			for i in self:
				self[i]['bastards'] = []
				self[i]['direct_span'] = list(self[i]['span'])
				self[i]['all_kids'] = list(self[i]['kids'].keys())

			# Process bottom-up (post-order)
			# We can use tree height or just sort by ID if we assume projectivity? 
			# No, dependency trees are not necessarily projective or ordered by ID.
			# We need a proper post-order traversal.
			# Or we can just iterate by depth?
			# Let's compute depth first.
			
			# Simple post-order: children before parents.
			# Since we have 'kids', we can do a recursive visit.
			visited = set()
			post_order = []
			
			def visit(n):
				if n in visited: return
				visited.add(n)
				for k in self[n]['kids']:
					visit(k)
				post_order.append(n)
				
			if self.rooti:
				visit(self.rooti)
			else:
				# Fallback if no root identified or multiple roots (fragments)
				for i in self: visit(i)
				
			for n in post_order:
				# We check children of n
				# Note: we iterate over a copy because we might modify all_kids of n? 
				# No, we modify all_kids of n by adding, but we check children c.
				# We modify all_kids of c by removing.
				
				current_kids = list(self[n]['all_kids'])
				for c in current_kids:
					# Check if c's direct_span is discontinuous
					dspan = self[c]['direct_span']
					if not dspan: continue
					
					# Check for gaps in dspan relative to the full range
					dspan_set = set(dspan)
					min_s, max_s = dspan[0], dspan[-1]
					full_range = set(range(min_s, max_s + 1))
					gaps = full_range - dspan_set
					
					if not gaps: continue
					
					# Check if gaps are real (contain non-excluded nodes)
					real_gaps = False
					for g in gaps:
						# Check if g is excluded
						# If g has ANY relation not in exclude, it is real.
						is_excluded = True
						for gov_id, rel in self[g].get('gov', {}).items():
							if rel not in exclude:
								is_excluded = False
								break
						if not is_excluded:
							real_gaps = True
							break
					
					if not real_gaps: continue
					
					# If gaps exist, check if they are "foreign" (not belonging to c)
					# Actually, direct_span only contains c's stuff.
					# So any gap in range is foreign.
					# So c is discontinuous.
					
					# Identify fragments
					fragments = []
					if dspan:
						current_frag = [dspan[0]]
						for i in range(1, len(dspan)):
							if dspan[i] != dspan[i-1] + 1:
								fragments.append(current_frag)
								current_frag = []
							current_frag.append(dspan[i])
						fragments.append(current_frag)
					
					# Find main fragment (containing c)
					main_frag = None
					bastard_frags = []
					for frag in fragments:
						if c in frag:
							main_frag = frag
						else:
							bastard_frags.append(frag)
							
					if not main_frag:
						# Should not happen if c is in its own span
						continue
						
					# For each bastard fragment, find the head (child of c)
					for frag in bastard_frags:
						frag_set = set(frag)
						# Find k in all_kids[c] that is in this fragment
						# We assume the fragment is a subtree of some k
						found_bastard = None
						for k in self[c]['all_kids']:
							if k in frag_set:
								# Check if k's span is fully in this fragment?
								# Or just if k is in it.
								# If k is in it, k is the head of that part (relative to c)
								found_bastard = k
								break
						
						if found_bastard:
							b = found_bastard
							# Lift b to n
							self[n]['bastards'].append(b)
							self[n]['all_kids'].append(b)
							
							# Remove b from c
							if b in self[c]['all_kids']:
								self[c]['all_kids'].remove(b)
							
							# Remove b's original span from direct_span of c and n
							# We use b's current direct_span? 
							# Or b's original span?
							# If b has its own bastards, they are already gone from b's direct_span.
							# We want to remove b and its remaining subtree.
							# So we remove b's direct_span.
							
							b_span_set = set(self[b]['direct_span'])
							
							self[c]['direct_span'] = sorted(list(set(self[c]['direct_span']) - b_span_set))
							self[n]['direct_span'] = sorted(list(set(self[n]['direct_span']) - b_span_set))

			
	def span(self, i):
		"""
		recursive function going down the tree
		"""
		sp = [i]
		for j in self[i]['kids']:
			sp += self.span(j)
		return sp
	
	def addflux(self):
		flux = {}
		for i in self:
			for g,f in self[i].get("gov",{}).items():
				#if f in exclude: continue
				if g>0: 
					#print(i,g)
					for ii in range(min(i,g),max(i,g)):
						#print(ii)
						flux[ii]=flux.get(ii,0)+1
					#self[g]["kids"][i]=f
		self.flux=[f for i,f in sorted(flux.items())]

	def correctNumbering(self):
		"""
		if numbering is not consistent, not 1,2,3, ... this function corrects this
		"""
		indexcorrection = {0:0} # old index --> new index
		problem = False
		for c, ind in enumerate(sorted(self.keys())):
			indexcorrection[ind]=c+1
			if c+1 != ind:
				problem = True
		if problem:
			correctTree = Tree()
			for i, node in list(self.items()):
				node["id"]=indexcorrection[i]
				newgov={}
				for gi,f in node["gov"].items():
					newgov[indexcorrection[gi]]=f
				node["gov"]=newgov
				correctTree[indexcorrection[i]]=node
				del self[i]
			for i, node in correctTree.items():
				self[i]=correctTree[i]
	
	#tree height
	def __headOfList(self,idlist):
		hdlist = []
		if len(idlist):
			for i in idlist:
				for hd in self[i]['gov'].keys():
					if hd != -1:	hdlist.append(hd)  #if i not an empty node
		return hdlist
	
	def __haveCousin(self, hdset):
		hdset.remove(0) #we are going to find head of headset while 0 haven't head
		#find head of headset, an id can appears more than once if there are multiple heads in one stage 
		hdofhdList = self.__headOfList(hdset)
		hdofhdSet = set(hdofhdList) #eliminate duplication
		return len(hdofhdList)!= len(set(hdofhdSet)), hdofhdSet

	def treeHeight(self):
		"""
		find tree height with different head id. For each 'stage' of tree, we compte only one head. 
		if one node is a head, it means there is one more stage for its son (dependent). 
		while in one stage, maybe there are more than one head(who has branche), so we need delete the others
		"""
		height = -1
		headset = set(self.__headOfList(self.keys())) #all head id in current tree
		#print("head id of current tree:", headset)
		
		branch = 0
		cousin = True #if there are cousins in headset
		while(cousin):
			cousin, headset = self.__haveCousin(headset) 
			branch += 1
			#print("\nheadset == ", headset,"\nbranch: ", branch)
			
			if(not cousin):
				height = len(headset)+ branch
		#print("treeHeight = ",height)
		return height

	def __getHeadId(self,idx):
		for hd in tree[idx]['gov'].keys():#hd is unique for each node
			return hd
	
	#dep length
	#for one node, find the depth by track back to the root
	def depLength(self, nodeId):
		length = 1 #every node have at least length 1 to the node 0
		head = self.__getHeadId(nodeId)
		while(head != 0):
			idx = head
			head = self.__getHeadId(idx)
			length += 1
		return length
		
	def oldreplaceNodes(self, idsequence, instree, headid=0, hook=1):
		"""
		idsequence: ids to be replaced
		headid: headid has to be in idsequence, dangling links are attached here
		instree: treestructure to be inserted. can be dict, list or string
		"""
		if isinstance(instree, str):instree = {i+1:{'t':t} for (i,t) in enumerate(instree.split())}
		elif isinstance(instree, list):instree = {i+1:{'t':t} for (i,t) in enumerate(instree)}
		
		insinds = sorted(instree.keys())
		id2newid = {0:0}
		for ind in sorted(self.keys()):
			if ind<idsequence[0]: id2newid[ind]=ind # before insertion
			elif ind in idsequence: # the nodes to be replaced
				if instree.rooti:
					id2newid[ind]=idsequence[0]+instree.rooti-1
				else:
					if idsequence.index(ind) < len(instree): # align as long as possible
						id2newid[ind]=ind
					else: # spurious ones point to the headid
						id2newid[ind]=headid
			else: # behind insertion
				id2newid[ind]=ind+len(instree)-len(idsequence);	
		print(id2newid)
		
		newtree = {}
		for ind in sorted(self.keys()):
			# spurious nodes just get kicked out (more elements to be kicked out than to be inserted):
			if ind in idsequence and idsequence.index(ind) >= len(instree): continue
			node = self[ind]
			node['id']=id2newid[ind]
			for gg in ['gov','egov']:
				newgov={}
				for gi,gf in node[gg].items(): newgov[id2newid[gi]]=gf
				node[gg]=newgov
			if ind in idsequence: # now i got to insert the matching nodes
				insnode = instree[insinds[idsequence.index(ind)]]
				for gg in ['gov','egov']:
					nngov = {}
					for gi,gf in insnode.get(gg,{}).items(): # just in case the instree contains govs
						if gi in instree: # not touching root relations and no outgoing relations
							nngov[gi+idsequence[0]-1]=gf
					if nngov: insnode[gg]=nngov
					elif gg in insnode: del insnode[gg]
				if 'id' in insnode: del insnode['id']
				node = {**node, **insnode}
			newtree[id2newid[ind]]=node
		for i in insinds:
			insnode = instree[i]
			if instree.rooti:
				for gg in ['gov','egov']:
					nngov = {}
					
				
			elif i>len(idsequence): # [len(idsequence):]
				
				for gg in ['gov','egov']:
					nngov = {}
					for gi,gf in insnode.get(gg,{}).items(): # just in case the instree contains govs
						if gi in instree: # not touching root relations and no outgoing relations
							nngov[gi+idsequence[0]-1]=gf
					if nngov: insnode[gg]=nngov
					elif gg in insnode: del insnode[gg]
				newtree[i+idsequence[0]-1]=insnode
		sf = self.sentencefeatures
		self.__init__(newtree)
		sf['text'] = self.sentence()
		self.sentencefeatures = sf

	
	
	def replaceNodesByTree(self, idsequence, instree, hook=1, headid=0, keepExtpos=True):
		"""
		idsequence: ids to be replaced
		headid: headid has to be in idsequence, dangling links are attached here
		instree: treestructure to be inserted. can be dict, list or string
		"""
		if isinstance(instree, str):instree = {i+1:{'t':t} for (i,t) in enumerate(instree.split())}
		elif isinstance(instree, list):instree = {i+1:{'t':t} for (i,t) in enumerate(instree)}
		
		
		
		id2newid = {0:0}
		for ind in sorted(self.keys()):
			if ind<idsequence[0]: id2newid[ind]=ind # before insertion
			elif ind in idsequence: # the nodes to be replaced
				id2newid[ind] = hook # all nodes that have a governor in idsequence get hooked to hook
			else: # behind insertion
				id2newid[ind]=ind+len(instree)-len(idsequence);	
		print(id2newid)
		
		newtree = {}
		for ind in sorted(self.keys()):
			if ind in idsequence: continue
			node = self[ind]
			node['id']=id2newid[ind]
			for gg in ['gov','egov']:
				newgov={}
				for gi,gf in node[gg].items(): newgov[id2newid[gi]]=gf
				node[gg]=newgov
			if keepExtpos: node['extpos']=node['tag']
			newtree[id2newid[ind]]=node
			
		print('newtree',Tree(newtree))
		
		insgov = 0
		for i in idsequence:
			for gi,gf in self[i]['gov'].items():pass
			if gi not in idsequence: 
				insgov = gi
				break
		print('found insgov:',insgov)
		
		insid2newid = {oi:oi+idsequence[0]-1 for oi in idsequence}
		insid2newid[0]=insgov
		for i in instree:
			insnode = instree[i]
			for gg in ['gov','egov']:
				nngov = {}
				for gi,gf in insnode.get(gg,{}).items(): # just in case the instree contains govs
					if gi in instree: # not touching root relations and no outgoing relations
						nngov[gi+idsequence[0]-1]=gf
					else:
						nngov[insgov]=gf # hooking all outgoing relations to insgov
				insnode[gg]=nngov
				newtree[i+idsequence[0]-1]=insnode
		
		print('newtre2',len(Tree(newtree)),Tree(newtree))
		
		
		
		
		sf = self.sentencefeatures
		inssf = instree.get('sentencefeatures',{})
		self.__init__({})
		self.__init__(newtree)
		sf['text'] = Tree(newtree).sentence()
		self.sentencefeatures = {**sf, **inssf}
		
		print('newtre3',len(Tree(newtree)),Tree(newtree))
		print('self',len(self),self)
	

def update(d, u):
	for k, v in u.items():
		if isinstance(v, collections.abc.Mapping):
			r = update(d.get(k, {}), v)
			d[k] = r
		else:
			d[k] = u[k]
	return d


def conll2tree(conllstring):
	""" 
	takes the conll string (or malt) representation of a single tree and creates a Tree (dictionary) for it
	"""
	tree=Tree()
	nr=1
	skipuntil=0 # only used to get the right "words" sequence, doesn't touch the actual tokens
	for line in conllstring.split('\n'):
		#print line
		if line.strip():
			if line.strip().endswith('# sent_id = D_ENU_13_School-life_1'):
				line=line[1:]
			if line.strip()[0]=="#": # comment of conllu
				if "=" in line:
					tree.sentencefeatures[line.split("=")[0].strip()[1:].strip()]="=".join(line.split("=")[1:]).strip()
				else:
					tree.sentencefeatures["_comments"]=tree.sentencefeatures.get("_comments","")+line.strip()[1:]+"\n#"
				continue
			
			cells = line.split('\t')
			nrCells = len(cells)
			
			if nrCells in [4,10,14]:
				
				if nrCells == 4: # malt!
					t, tag, govid, rel = cells
					if govid=="_": govid=-1
					else:govid = int(govid)
					newf={'id':nr,'t': t, 'tag': tag,'gov':{govid: rel}}
					tree[nr]=update(tree.get(nr,{}), newf)
					nr+=1

				elif nrCells == 10: # standard conll 10 or conllu
					nr, t, lemma , tag, xpos, features, govid, rel, edeps, misc = cells
					if "-" in nr: 
						try:	skipuntil=int(nr.split("-")[-1])
						except:	skipuntil=float(nr.split("-")[-1])
						tree.words+=[t]
						continue
					try:	nr = int(nr)
					except:	nr = float(nr) # handling the 3.1 format for "emtpy nodes"
					if govid.strip()=="_": govid=-1
					else:
						try:	govid = int(govid)
						except:	
							try:	govid = float(govid)
							except: 
								try:	assert(govid[0]=='$') # for transconll
								except: raise FormatError("not number or variable: "+govid)
					egov={}
					if ":" in edeps: # the enhanced graph is used
						egov=dict([(gf.split(":")[0],gf.split(":")[-1]) for gf in edeps.split("|")])					
					
					newf={'id':nr,'t': t,'lemma': lemma, 'tag': tag, 'xpos': xpos, 'gov':{govid: rel}, 'egov':egov, 'misc': misc}
					if "=" in features:
						mf=dict([(av.split("=")[0],av.split("=")[-1]) for av in features.split("|")])
						#print("\n features :", mf)
						newf=update(mf,newf)
						#print("new f ", newf)
					if "=" in misc:
						mf=dict([(av.split("=")[0],av.split("=")[-1]) for av in misc.split("|")])
						newf=update(mf,newf)
						del newf['misc']
					elif misc=="_":
						del newf['misc']
					tree[nr]=update(tree.get(nr,{}), newf)
					
					# to be removed:
					#if 'Glose' in tree[nr]: 
						#tree[nr]['Gloss']=tree[nr]['Glose']
						#del tree[nr]['Glose']
					#if 'startali' in tree[nr]: 
						#tree[nr]['AlignBegin']=tree[nr]['startali']
						#del tree[nr]['startali']
					#if 'endali' in tree[nr]: 
						#tree[nr]['AlignEnd']=tree[nr]['endali']
						#del tree[nr]['endali']
					# end to be removed
					
					if nr>skipuntil: tree.words+=[t]
					
				elif nrCells == 14:
					#mate:
					#6, inscriptions, _, inscription, _, N, _, pl|masc, -1, 4, _, dep, _, _
					nr, t, lemma, lemma2, tag, xpos, morph, morph2, govid, govid2, rel, rel2, _, _ = cells
					nr = int(nr)
					if govid.strip()=="_": govid=-1
					else:govid = int(govid)
					if govid2.strip()=="_": govid2=-1
					else:govid2 = int(govid2)
					if lemma=="_" and lemma2!="_":lemma=lemma2
					if tag=="_" and xpos!="_":tag=xpos
					if morph=="_" and morph2!="_":morph=morph2
					if rel=="_" and rel2!="_":
						rel=rel2
						govid=govid2
					newf={'id':nr,'t': t,'lemma': lemma,'lemma2': lemma2, 'tag': tag, 'xpos': xpos, 'morph': morph, 'morph2': morph2, 'gov':{govid: rel}, 'egov':{govid2: rel2} }
					
					
					
					tree[nr]=update(tree.get(nr,{}), newf)
					
					
			elif debug:
				print("strange conll:",nrCells,"columns!",line)
				print(ord(line[0]))
				print(line[0].encode('utf-8'))
				print(line[1])
	
	return tree


def conllFile2trees(path):
	"""
	file with path -> list of trees
	
	important function!	
	called from enterConll, treebankfiles, and uploadConll in treebankfiles.cgi
	
	"""
	trees=[]
	with open(path,"r") as f:
		conlltext=""
		for li in f:
			li=li.strip()
			if li: 	conlltext+=li+"\n"
			elif conlltext: # emptyline, sentence is finished
				tree=conll2tree(conlltext)
				trees+=[tree]
				del tree
				conlltext=""
		f.close()
		if conlltext.strip(): # last tree may not be followed by empty line
			tree=conll2tree(conlltext)
			trees+=[tree]
		return trees


def trees2conllFile(trees, outfile, columns="u"): # changed default from 10 to u!
	"""
	exports a list of treedics into outfile
	used after tree transformations...
	in conll14 format, the lemma position contains a duplicated t if lemma is not available
	"""
	treestrings=[]
	with open(outfile,"w") as f:
		for tree in trees:
			if columns=="u": # conllu format
				treestring = tree.conllu()
			else:
				
				treestring = ""
				for stftkey in sorted(tree.sentencefeatures):
					if stftkey=="_comments":
						treestring+=tree.sentencefeatures[stftkey]
					else:
						treestring+=stftkey+" = "+tree.sentencefeatures[stftkey]				
				for i in sorted(tree):					
					node = tree[i] 
					gov = list(node.get("gov",{}).items())
					govid = -1
					func = "_"
					if gov:
						for govid,func in gov:
							if columns==10:
								treestring+="\t".join([str(i), node.get("t","_"), node.get("lemma",""), node.get("tag","_"), node.get("xpos","_"), "_", str(govid),func,"_","_"])+"\n"
							elif columns==14:
								lemma = node.get("lemma","_")
								if lemma == "_": lemma = node.get("t","_")
								treestring+="\t".join([str(i), node.get("t","_"), lemma, lemma or node.get("t","_"), node.get("tag","_"), node.get("tag","_"), node.get("morph","_"), node.get("morph","_"), str(govid),str(govid),func,func,"_","_"])+"\n"
					else:
						if columns==10:
							treestring+="\t".join([str(i), node.get("t","_"), node.get("lemma",""), node.get("tag","_"), node.get("xpos","_"), "_", str(govid),func,"_","_"])+"\n"
							
						elif columns==14:
							lemma = node.get("lemma","_")
							if lemma == "_": lemma = node.get("t","_")
							treestring+="\t".join([str(i), node.get("t","_"), lemma, lemma, node.get("tag","_"), node.get("tag","_"), node.get("morph","_"), node.get("morph","_"), str(govid),str(govid),func,func,"_","_"])+"\n"
			treestrings+=[treestring]
		f.write("\n".join(treestrings))


def sentences2emptyConllFile(infile, outfile):
	"""
	transforms a list of sentences into conll format without trees
	"""
	inf=open(infile)
	outf=open(outfile,"w")
	counter=0
	for line in inf:
		line=line.strip()
		if line:
			for i,word in enumerate(line.split()):
				outf.write("\t".join([str(i+1),word,word,"_","_","_","-1","","_","_"])+"\n")
				## nr, t, lemma , tag, xpos, _, govid, rel, _, _ = cells
			outf.write("\n")
			counter+=1
	inf.close()
	outf.close()
	print(counter, "sentences")


def textFiles2emptyConllFiles(infolder, outfolder):
	import glob, os
	sentenceSplit=re.compile(r"(\s*\n+\s*|(?<!\s[A-ZÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÄËÏÖÜÃÑÕÆÅÐÇØ])[\?\!？\!\.。！……]+\s+|\s+\|\s+|[？。！……]+)(?!\d)", re.M+re.U)
	resentence=re.compile(r"[\?\!？\!\.。！……]+", re.M+re.U)
	retokenize=re.compile("(\W)",re.U+re.I)
	redoublespace=re.compile("(\s+)",re.U+re.I)
	renumber=re.compile("(\d) \. (\d)",re.U+re.I)
	rewhite=re.compile("\w",re.U+re.I)
	try:os.mkdir(outfolder)
	except:print("folder exists")
	for infile in glob.glob(os.path.join(infolder, '*.*')):
		print(infile)
		outfile=open(outfolder+"/"+infile.split("/")[-1],"w")
		for line in open(infile):
			line=line.strip()
			for s in sentenceSplit.split(line):
				s=s.strip()
				if resentence.match(s):
					outfile.write(str(count)+"\t"+s+"\n")
					outfile.write("\n")
				else:
					count=1
					s = retokenize.sub(r" \1 ",s)
					s = redoublespace.sub(r" ",s)
					s = renumber.sub(r"\1.\2",s)
					for token in s.split():
						if token.strip()=='\ufeff':continue # TODO: find out why this anti BOM shit is needed...
						outfile.write(str(count)+"\t"+token+"\n")
						count +=1




if __name__ == "__main__":
	pass
	#trees = conllFile2trees("sudcorrected/ONI_26_News-Highlights_MG.conllu")
	#trees = conllFile2trees("/home/kim/Downloads/ABJ_GWA_03_Cost-Of-Living-In-Abuja_MG.conllu")
	trees = conllFile2trees("/home/sylviepeng/typometrics/datapreparation/sud-treebanks-v2.8/SUD_Beja-NSC/bej_BEJ_MV_NARR_01_shelter.conllu")
	print(len(trees))
	print(trees[2].conllu())

	
	#replaceNodesByTree(idsequence, instree, hook=1, headid=0, keepExtpos=True)
	#trees[0].replaceNodes([2,3], 2, {1:{'t':'oh'}})
	#trees[0].replaceNodes([2,3], 2, {1:{'t':'oh'},2:{'t':'là','gov':{1:'mylink'}},3:{'t':'làaa','gov':{2:'mylink'}}})
	#trees[0].replaceNodes([2,3], 2, ["oh", "là", "là"])

	#trees[2].replaceNodesByTree([2,3], {}, 2) enleve # 

	#trees[0].replaceNodes([2,3], 2, "oh là là")

	#print(trees[2]) enleve # 

	#print(trees[0].sentencefeatures)
	#trees[0].correctNumbering()
	#print(trees[0].conllu())
	#open("test.conllu","w").write(trees[0].conllu())
	
