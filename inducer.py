import getopt

class Grammar:
	"""
	A class for LCFRS-grammars.
	
	Attributes:
	 self.rules: a list of Rule objects
	
	Functions:
	 self.__init__(f): from an inputfile "f" in NeGra-format collect a list of trees, then for each tree call the function self.induce
	 self.induce(tree): induce LCFRS rules from a tree "tree" and add them to self.rules if they are not a duplicate of a rule already in there
	 self.pprint(): print the form of each rule in self.rules in alphabetical order
	 self.pwrite(output): write the form of each rule in self.rules on outputfile "output" in alphabetical order
	"""
	def __init__(self,f):
		"""
		Collects a list of trees from a treebank file, then calls the function self.induce for each tree.
		
		Input: a treebank file "f" in NeGra-format
		"""
		self.rules = []
		with open(f, 'r') as fileObject:
			lines = fileObject.read().splitlines()
		trees = []
		for line in lines:
			if line[:4] == "#BOS":
				tree = [] #Initializing a new treelist at beginning of sequence (#BOS)
			elif line[:4] == "#EOS":
				index = line[5:] 
				trees.append(tree) #Appending the tree to the list of trees at end of sequence (#EOS)
			else:
				tree.append(line) #Putting nodes (lines) in the treelist
		count = 0
		for tree in trees:
			self.induce(tree)
			count +=1
			if count%100==0: #counter to check the progress
				print(str(count)+" trees complete")
		print("induction complete")

	def induce(self,tree):
		"""
		Induces LCFRS rules from a tree "tree" and add them to self.rules if they are not a duplicate of a rule already in there.
		
		Input: a list of lines representing nodes from a tree in NeGra-format
		"""
		nodes = {} #we put the nodes in a dictionary so it becomes easy to look them up by their id
		leaves = []
		for line in tree:
			node = Node(line.split("\t"))
			if node.id[0] == "#":
				nodes[node.id[1:]]=node #the "#" is sliced off since it also doesn't appear in node.mother
			else: #if the nodeID doesn't start with "#", the nodeID is instead the word on the input string, and therefore this node is a leaf node
				leaves.append(node)
		for s in range(len(leaves)):
			leaves[s].strID=[s] 
			"""Since we're looping over the leaves anyway, we're setting the string ID right here.
			Since the words are in order of their appearance the string ID matches the position in the list of leaves"""
			mother = nodes[leaves[s].mother]
			mother.daughters.append(leaves[s]) #As should be obvious, a node is one of its mother's daughter nodes
		for node in nodes.values():
			if node.mother != "0": #O is the ID of a root node's mother. Since a root node is not the daugther of any node, the following lines do not apply to them
				mother = nodes[node.mother]
				mother.daughters.append(node)
		nodes2 = [] #now that we have found the mother nodes, we don't need a dictionary anymore, so we are going to collect our nodes in a list
		nodesval = list(nodes.values()) #We go from a dict to a list because we want to edit the data structure while looping
		while nodesval != []: #only stop this loop if we are sure that all nodes have their string ID
			for node in nodesval:
				if node.allDaughtersHaveStrID(): #Do not get the string ID until all daughter nodes have their string ID's
					node.getStrID()
					nodes2.append(node)
					#When the string ID is obtained, move the node from nodesval to nodes2
					nodesval.remove(node)
		for leaf in leaves:
			newrule = Rule(leaf)
			if self.rules ==[]: #if this is the first rule, we don't need to check if it's a duplicate
				self.rules.append(newrule)
			else:
				isDupl = False
				for rule in self.rules:
					if newrule.form == rule.form: #if two rules have the same form, they are duplicates of eachother, so the new one should not be added to the grammar
						isDupl = True
						break
				if not isDupl:
					self.rules.append(newrule)
		for node in nodes2:
			newrule = Rule(node)
			if self.rules ==[]:
				self.rules.append(newrule)
			else:
				isDupl = False
				for rule in self.rules:
					if newrule.form == rule.form:
						isDupl = True
						break
				if not isDupl:
					self.rules.append(newrule)

	def pprint(self):
		"""
		Prints the form of each rule in self.rules in alphabetical order
		"""
		prules=[] #We make a list so that we can sort the rules
		for rule in self.rules:
			prules.append(rule.form)
		prules.sort()
		for rule in prules:
			print(rule)
			
	def pwrite(self, output):
		"""
		Writes the form of each rule in self.rules on outputfile "output" in alphabetical order
		
		Input: a file to write the rules onto
		"""
		prules=[] #We make a list so that we can sort the rules
		for rule in self.rules:
			prules.append(rule.form)
		prules.sort()
		with open(output, 'w') as fileObject:
			for rule in prules:
				fileObject.write(rule+"\n")

class Rule:
	"""
	A class for LCFRS-rules.
	
	Attributes:
	 self.lhs: a Predicate object representing the left-hand side of the rule
	 self.rhs: a list of Predicate objects, or the string "eps" representing the right-hand side of the rule
	 self.form: a string representation of the rule
	
	Functions:
	 self.__init__(node): From a node object, set the lhs as a predicate with the node lable as its name and the node's arguments as its argument. Set the rhs as a list of predicates based on the node's daughters in a similar fashion. Then contract the lhs and rhs arguments according to the induction algorithm, and finally set self.form as the string representation of the rule by calling self.makeform().
	 self.mkform(): Sets self.form the string representation of the rule
	"""
	def __init__(self,node):
		"""
		Sets, from a node object, the lhs as a predicate with the node lable as its name and the node's arguments as its argument, then sets the rhs as a list of predicates based on the node's daughters in a similar fashion, then contracts the lhs and rhs arguments according to the induction algorithm, and finally sets self.form as the string representation of the rule by calling self.makeform()
		
		Input: a Node object that either is a leaf node or has all of its daughters listed
		"""
		if node.id[0]!="#": #Again, we check if the node is a leaf node
			self.lhs = Predicate(node.label,[node.id]) #The left hand side of an LCFRS rule consits of a predicate, with the node label as their name. For terminal rules, the argument is the word on the input string
			self.rhs = "eps" #Terminal rules have an empty string (represented by "eps" for epsilon) as their right-hand side
		else:
			args = node.findArgs()
			self.lhs = Predicate(node.label,args)
			self.rhs = []
			for daughter in node.daughters: #The right-hand side of non-terminal rules consists of a list of predicates that are based on the predicates of the daughter nodes.
				args = daughter.findArgs()
				self.rhs.append(Predicate(daughter.label,args))
			count = 0 #We start a new counter to make sure the variables in the arguments of a rule have different names
			for pred in self.rhs:
				"""Each right-hand side argument needs only to be represented by a single variable.
				We then need to make sure that same variable appears on the left-hand side at the same position"""
				for i in range(len(pred.args)):
					for j in range(len(self.lhs.args)):
						if pred.args[i] in self.lhs.args[j]:
							self.lhs.args[j]+="|" #We add "|" as an end of string marker"
							self.lhs.args[j]=self.lhs.args[j].replace(pred.args[i]+"Y","X_"+str(count)+"Y")
							self.lhs.args[j]=self.lhs.args[j].replace(pred.args[i]+"X","X_"+str(count)+"X")
							self.lhs.args[j]=self.lhs.args[j].replace(pred.args[i]+"|","X_"+str(count)+"|")
							#We check the next symbol to make sure it's not another numeric symbol
							self.lhs.args[j]=self.lhs.args[j][:-1] #We remove the end of string marker again
							pred.args[i] = "X_"+str(count) #We now replace the right hand side argument with the same variable
							count+=1
		self.mkform()

	def mkform(self):
		"""
		Sets self.form as the string representation of the rule
		"""
		form = ""
		form += self.lhs.mkform()
		form += "->" #By convention, left-hand side and right-hand side are separated by an arrow symbol
		if self.rhs == "eps":
			form += self.rhs #if the right-hand side is already a string, we can append it immediately
		else:
			for pred in self.rhs:
				form += pred.mkform() #By convention, right-hand side predicates are not separated by a symbol
		self.form = form
			
			
class Predicate:
	"""
	A class for LCFRS predicates
	
	Attributes:
	 self.name: a string representing the predicate's name
	 self.args: a list of strings representing the predicate's arguments
	 
	Functions:
	 self.__init__(name,args): set self.name and self.args
	 self.mkform(): return the form of the predicate as a string
	"""
	def __init__(self,name,args):
		"""
		Sets self.name and self.args
		
		Input:
		 name: a string representing the predicate's name
		 args: a list of strings representing the predicate's arguments
		"""
		self.name = name
		self.args = args

	def mkform(self):
		"""
		Returns the form of the predicate as a string
		
		Output: the form of the predicate as a string
		"""
		form = ""
		form += self.name
		form += "(" #By convention, the arguments of a predicate appear in between parentheses
		for arg in self.args:
			form += arg
			if arg == self.args[-1]: #if this is the last argument, the next symbol needs to be the closing bracket
				form += ")"
			else:
				form += "," #By convention, arguments are separated by a comma
		return form

class Node:
	"""
	A class for node objects obtained from a treebank in NeGra-format
	
	Attributes:
	 self.id: a string representing the node id, or the word on the input string in case of a leaf node
	 self.label: a string representing the node label
	 self.mother: a string matching the node lable of this node's mother node
	 self.strID: a list of integers representing the positions of words on the input string dominated by this node
	 self.daughters: a list of node objects that are daughter nodes of this node
	 
	functions:
	 self.init(l): set self.id, self.label and self.mother based on the inputted node as a list of strings, then initialize self.strID and self.daughters as empty lists.
	 self.allDaughtersHaveStrID(): return False if there is a daughter whose string ID is empty, otherwise, return True
	 self.getStrID(): set self.strID based on the string ID's of this node's daughters
	 self.findArgs(): make a list of arguments from self.strID, and return this list
	"""
	def __init__(self,l):
		"""
		Sets self.id, self.label and self.mother based on the inputted node, then initialize self.strID and self.daughters as empty lists
		
		Input: A node in Negra-Format as a list, obtained from splitting its string on tabs
		"""
		self.id = l[0] #For leaf nodes, this is the word on the input string
		self.label = l[2]
		self.mother = l[5]
		self.strID = []
		self.daughters = []
		
	def allDaughtersHaveStrID(self):
		"""
		Checks if all daughters have a nonempty string ID
		
		Output: False if there is a daughter with an empty string ID, True otherwise
		"""
		for daughter in self.daughters:
			if daughter.strID == []:
				return False
		return True
		
	def getStrID(self):
		"""
		Sets self.strID based on the string ID's of this node's daughters
		"""
		if len(self.daughters) == 1: #if the node has only one daughter, its string ID is the same as its daughter's
			self.strID = self.daughters[0].strID
		else:
			strID = []
			for daughter in self.daughters:
				strID += daughter.strID #if the node has multiple daughters, its string ID is the concatenation of its daughters' string ID's
			strID.sort()  #We sort the string ID so that we can check if there are any gaps later on
			self.strID = strID
				
	def findArgs(self):
		"""
		Makes a list of arguments from self.strID
		
		Output: a list of strings, representing the arguments for the LCFRS rule based on this node
		"""
		args = []
		arg = ""
		for i in range(len(self.strID)):
			if i != 0:
				if self.strID[i]-1 != self.strID[i-1]: 
				#If the previous integer in the string ID is not one lower than the current one, there is a gap. We introduce an argument boundary at every gap. 
					args.append(arg)
					arg = ""
			arg += "Y_"+str(self.strID[i])
		args.append(arg)
		return args

def helptext():
	t="\n A program for inducing an LCFRS-grammar from a treebank in NEGRA format.\n\n Usage: python3 inducer.py [-h] [-o outputfile] inputfile\n\n Input:\n  -h: display this help message and exit\n  -o outputfile: file to write the induced grammar on\n  inputfile: treebank in NeGra format to induce from\n\n Output: the grammar rules of the induced grammar on the outputfile if specified, and otherwise printed in the terminal"
	return(t)

def main(args):
	opts, args = getopt.getopt(args,'ho:')
	f_out = None
	for o, a in opts:
		if o == "-h":
			return(helptext())
		if o == "-o":
			f_out = a
	grammar = Grammar(args[0])
	print("grammar made")
	if f_out == None:
		grammar.pprint()
	else:
		grammar.pwrite(f_out)
	

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
