# -*- coding: utf-8 -*-

import os
import re
import copy
import csv

class FileConverter:
	def __init__(self, homePath, exportPath = None):
		self.HOME_PATH = homePath
		self.EXPORT_ROOT_DIRNAME = 'ProcessedData'
		if exportPath == None:
			self.EXPORT_PATH = os.path.join(homePath, os.pardir)
		else:
			self.EXPORT_PATH = exportPath

		## below Regex are use for triming needless strings in '.prj' and '.trj' data #####

		self.TOP_SPACE_PATTERN = '^\s(?<=\s)(?=[\d\w])'
		self.VECTOR_SPACE_PATTERN = '(?<=\d)(?<!,) +(?!=-)(?=[-\d])'
		self.END_SPACE_PATTERN = '\s+(?!=\w\d)'

		###################################################################################

		## attribution name pattern #######################################################

		self.IPOTHER_PATTERN = 'ImpactPoint(?!\d)'
		self.IPMMR_PATTERN = 'ImpactPointM(ax|in)Radius'
		self.IBP_PATTERN = 'ImpactBouncemarkPoints\d+'
		self.AMAT_PATTERN = 'ArcSvaMatrix\d'
		self.BALLINFO_PATTERN = '(Type|Arc|Time|Confidence|ImpactPoint)(?P<Num>\d+)'

		###################################################################################

		## below pattern are use for processing file name #################################

		self.EXPORT_GENERAL_FILENAME = 'GeneralInfo.csv'
		self.EXPORT_IMPACTINFO_FILENAME = 'ImpactInfo.csv'
		self.EXPORT_IMPACTVECTOR_FILENAME = 'ImpactVector.csv'
		self.EXPORT_BALLVECTOR_FILENAME = 'BallVector.csv'
		self.EXPORT_BALLINFO_FILENAME = 'BallInfo.csv'
		self.EXPORT_PLAYERVECTOR_FILENAME = 'PlayerVector.csv'

		###################################################################################

	def export(self):
		exPath = os.path.join(self.EXPORT_PATH, self.EXPORT_ROOT_DIRNAME)
		os.mkdir(exPath)

		rootFilePaths = self.getFilePaths(self.HOME_PATH)
		rootFileNames = self.getFileName(self.HOME_PATH)

		## GAME LOOP
		for i in range(0, len(rootFilePaths)):
			tmpOutGamePath = os.path.join(exPath, rootFileNames[i])
			os.mkdir(tmpOutGamePath)

			tmpInDirPath = rootFilePaths[i] + '/' + self.getFileName(rootFilePaths[i])[0]

			tmpInFilePaths = self.getFilePaths(tmpInDirPath)
			tmpInFileNames = self.getFileName(tmpInDirPath)
			
			exportPlayerVectorRows = []
			PlayerHeader = self.getPlayerHeader()
			exportPlayerVectorRows.append(PlayerHeader)
			
			exportGeneralRows = []
			GeneralHeader = self.getGeneralInfoHeader()
			exportGeneralRows.append(GeneralHeader)

			exportImpactInfoRows = []
			ImpactInfoHeader = self.getImpactInfoHeader()
			exportImpactInfoRows.append(ImpactInfoHeader)

			exportImpactVectorRows = []
			ImpactVectorHeader = self.getImpactVectorHeader()
			exportImpactVectorRows.append(ImpactVectorHeader)

			exportBallVectorRows = []
			BallVectorHeader = self.getBallVectorHeader()
			exportBallVectorRows.append(BallVectorHeader)

			exportBallInfoRows = []
			BallInfoHeader = self.getBallInfoHeader()
			exportBallInfoRows.append(BallInfoHeader)

			#loop in a game folder (have a lot of .trj files and players dir)
			for j in range(0, len(tmpInFileNames)):
				if j == 0:
					tmpFile = open(tmpInFilePaths[j])
					ids = self.getID(tmpInFileNames[j])
					vec = tmpFile.readlines()
					vec = self.processData(vec)
					tmpRepos = ids[:]
					for v in range(0, len(vec)):
						if v == 25:
							tmpRepos.append(vec[v])
							tmpRepos.append(0)
							tmpRepos.append(0)
							tmpRepos.append(0)
							tmpRepos.append(0)
						elif v % 2 == 1:
							tmpRepos.append(vec[v])
					tmpRepos.append(0)
					exportGeneralRows.append(tmpRepos)

				elif tmpInFileNames[j] == 'Players':					
					tmpInPlayersDataRepos = self.getFilePaths(tmpInFilePaths[j])
					tmpInPlayersDataInfo = self.getFileName(tmpInFilePaths[j])

					#loop in each file.prj
					for k in range(0, len(tmpInPlayersDataRepos)):
						tmpFile = open(tmpInPlayersDataRepos[k])

						tmpDataRepos = tmpFile.readlines()
						tmpDataRepos = self.processData(tmpDataRepos)
						tmpInFileName = tmpInPlayersDataInfo[k]
						ids = self.getID(tmpInFileName)
						for line in tmpDataRepos:
							vec = line.split(',')
							row = ids + vec
							exportPlayerVectorRows.append(row)
				else:
					tmpFile = open(tmpInFilePaths[j])

					tmpDataRepos = tmpFile.readlines()
					tmpDataRepos = self.processData(tmpDataRepos)
					ids = self.getID(tmpInFileNames[j])

					tmpGeneralRow = ids[:]
					tmpImpactInfoRow = []
					tmpBallInfoRow = []
					tmpBallVectorRow = []

					rallyID = 0
					tmpEndTime = ''
					tmpHitpointType = ''
					tmpArcCTIndex = 0
					tmpBounceConfidence = 0
					tmpSkidArc = 0
					tmpImpactPoint = False

					for line in range(0, len(tmpDataRepos)):
						typeFlag = self.typeChecker(tmpDataRepos[line])

						## export type : General information
						if typeFlag == 1:
							tmpGeneralRow.append(tmpDataRepos[line + 1])

						## export type : Impact information
						elif typeFlag == 2:
							if re.search('ImpactPointIn\d+', tmpDataRepos[line]) != None:
								for v in tmpDataRepos[line + 1].split(','):
									tmpImpactInfoRow.append(v)
							elif re.search('ImpactPointVelIn\d+', tmpDataRepos[line]) != None:
								for v in tmpDataRepos[line + 1].split(','):
									tmpImpactInfoRow.append(v)
							else:
								tmpImpactInfoRow.append(tmpDataRepos[line + 1])

						## export type : ImpactBouncemarkPoint vector
						elif typeFlag == 3:
							tmpVectorRepos = tmpDataRepos[line + 1].split(',')
							x = []
							y = []
							for v in range(0, len(tmpVectorRepos)):
								if v % 2 == 0:
									x.append(tmpVectorRepos[v])
								else:
									y.append(tmpVectorRepos[v])
							for d in range(0, len(x)):
								tmpRepos = ids[:]
								tmpRepos.append(rallyID)
								tmpRepos.append(d + 1)
								tmpRepos.append(x[d])
								tmpRepos.append(y[d])
								exportImpactVectorRows.append(tmpRepos)

						## export type : Ball geo vector
						elif typeFlag == 4:
							x = tmpDataRepos[line + 1].split(',')
							y = tmpDataRepos[line + 2].split(',')
							z = tmpDataRepos[line + 3].split(',')
							for d in range(0, len(x)):
								if x[d] != '0.00000000000000e+000':
									tmpRepos = ids[:]
									tmpRepos.append(rallyID)
									tmpRepos.append(d + 1)
									tmpRepos.append(x[d])
									tmpRepos.append(y[d])
									tmpRepos.append(z[d])
									exportBallVectorRows.append(tmpRepos)

						## export type : Ball information
						elif typeFlag == 5:
							match = re.search('StartTime(?P<Num>\d+)', tmpDataRepos[line])
							## first rally.
							if match != None:
								rallyID = match.group('Num')
								if rallyID > 0:
									tmpBallInfoRow.append(tmpEndTime)
									tmpBallInfoRow.append(tmpHitpointType)
									tmpBallInfoRow.append(tmpArcCTIndex)
									tmpBallInfoRow.append(tmpBounceConfidence)
									tmpBallInfoRow.append(tmpSkidArc)
									tmpBallInfoRow.append(tmpImpactPoint)
									if len(tmpBallInfoRow) == 13:
										exportBallInfoRows.append(tmpBallInfoRow)

									## initialize temporary ball information
									tmpEndTime = ''
									tmpHitpointType = ''
									tmpArcCTIndex = 0
									tmpBounceConfidence = 0
									tmpSkidArc = 0
									tmpImpactPoint = False

								if len(tmpImpactInfoRow) > 6:
									exportImpactInfoRows.append(tmpImpactInfoRow)
								tmpImpactInfoRow = ids[:]
								tmpImpactInfoRow.append(rallyID)

								tmpImpactVectorRow = ids[:]
								tmpImpactVectorRow.append(rallyID)

								tmpBallInfoRow = ids[:]
								tmpBallInfoRow.append(rallyID)
								tmpBallInfoRow.append(tmpDataRepos[line + 1])

								tmpBallVectorRow = ids[:]
								tmpBallVectorRow.append(rallyID)
							elif re.search('EndTime\d+', tmpDataRepos[line]) != None:
								tmpEndTime = tmpDataRepos[line + 1]
							elif re.search('HitpointType\d+', tmpDataRepos[line]) != None:
								tmpHitpointType = tmpDataRepos[line + 1]
							elif re.search('Arc\d+CTIndex', tmpDataRepos[line]) != None:
								tmpArcCTIndex = tmpDataRepos[line + 1]
							elif re.search('BounceConfidence\d+', tmpDataRepos[line]) != None:
								tmpBounceConfidence = tmpDataRepos[line + 1]
							elif re.search('SkidArc\d+', tmpDataRepos[line]) != None:
								tmpSkidArc = tmpDataRepos[line + 1]
							elif re.search('ImpactPoint\d+', tmpDataRepos[line]) != None:
								tmpImpactPoint = tmpDataRepos[line + 1]

						## export type : Error!
						else:
							if re.search('<\w+>', tmpDataRepos[line]) != None:
								print tmpDataRepos[line]

					if len(tmpGeneralRow) == 26:
						exportGeneralRows.append(tmpGeneralRow)

					## export last rally's data 
					tmpBallInfoRow.append(tmpEndTime)
					tmpBallInfoRow.append(tmpHitpointType)
					tmpBallInfoRow.append(tmpArcCTIndex)
					tmpBallInfoRow.append(tmpBounceConfidence)
					tmpBallInfoRow.append(tmpSkidArc)
					tmpBallInfoRow.append(tmpImpactPoint)
					if len(tmpBallInfoRow) == 13:
						exportBallInfoRows.append(tmpBallInfoRow)

			## export process
			playerVectorFileName = os.path.join(tmpOutGamePath, self.EXPORT_PLAYERVECTOR_FILENAME)
			self.writeFile(exportPlayerVectorRows, playerVectorFileName)

			generalInfoFileName = os.path.join(tmpOutGamePath, self.EXPORT_GENERAL_FILENAME)
			self.writeFile(exportGeneralRows, generalInfoFileName)

			impactInfoFileName = os.path.join(tmpOutGamePath, self.EXPORT_IMPACTINFO_FILENAME)
			self.writeFile(exportImpactInfoRows, impactInfoFileName)

			impactVectorFileName = os.path.join(tmpOutGamePath, self.EXPORT_IMPACTVECTOR_FILENAME)
			self.writeFile(exportImpactVectorRows, impactVectorFileName)

			ballVectorFileName = os.path.join(tmpOutGamePath, self.EXPORT_BALLVECTOR_FILENAME)
			self.writeFile(exportBallVectorRows, ballVectorFileName)

			ballInfoFileName = os.path.join(tmpOutGamePath, self.EXPORT_BALLINFO_FILENAME)
			self.writeFile(exportBallInfoRows, ballInfoFileName)


### Methods for making headers#######################################

	def getPlayerHeader(self):
		header = ['timeStamp','setID', 'gameID', 'pointID', 'serveID']
		header.append('time')
		header.append('p1x')
		header.append('p1y')
		header.append('p1z')
		header.append('p2x')
		header.append('p2y')
		header.append('p2z')
		return header

	def getGeneralInfoHeader(self):
		header = ['timeStamp', 'setID', 'gameID', 'pointID', 'serveID']
		header.append('ParticipantServer')
		header.append('ParticipantReceiver')
		header.append('Server')
		header.append('Receiver')
		header.append('Playerat+veX')
		header.append('DrillType')
		header.append('ServeClassification')
		header.append('Stats')
		header.append('Score(Raw)')
		header.append('Score(Normal)')
		header.append('Scorer')
		header.append('Winner')
		header.append('BigPoint')
		header.append('TimeCodeStartTime')
		header.append('TimeCodeStartTimeHH:MM:SS:FF')
		header.append('NumArcs')
		header.append('ZeroTime')
		header.append('Scoreboard1')
		header.append('Scoreboard2')
		header.append('MaxNumSets')
		header.append('End')
		return header

	def getImpactInfoHeader(self):
		header = ['timeStamp', 'setID', 'gameID', 'pointID', 'serveID']
		header.append('rallyID')
		header.append('PointInX')
		header.append('PointInY')
		header.append('PointInZ')
		header.append('PointVelInX')
		header.append('PointVelInY')
		header.append('PointVelInZ')
		header.append('PointMinRadius')
		header.append('PointMaxRadius')
		header.append('PointOffset')
		return header

	def getImpactVectorHeader(self):
		header = ['timeStamp', 'setID', 'gameID', 'pointID', 'serveID']
		header.append('rallyID')
		header.append('dimNo')
		header.append('x')
		header.append('y')
		return header

	def getBallVectorHeader(self):
		header = ['timeStamp', 'setID', 'gameID', 'pointID', 'serveID']
		header.append('rallyID')
		header.append('dimNo')
		header.append('x')
		header.append('y')
		header.append('z')
		return header

	def getBallInfoHeader(self):
		header = ['timeStamp', 'setID', 'gameID', 'pointID', 'serveID']
		header.append('rallyID')
		header.append('StartTime')
		header.append('EndTime')
		header.append('HitPointType')
		header.append('ArcCTIndex')
		header.append('BounceConfidence')
		header.append('SkidArc')
		header.append('ImpactPoint')
		return header

######################################################################

## methods for processing data #######################################

	def getFileName(self, dirPath):
		#result = []
		result = [tmpDir for tmpDir in os.listdir(dirPath)]
		'''
		for tmpDir in os.listdir(dirPath):
			if tmpDir[0] != '.':
				result.append(tmpDir)
		'''
		return result

	def getFilePaths(self, dirPath):
		#result = []
		result = [dirPath + '/' + tmpDir for tmpDir in os.listdir(dirPath) if tmpDir[0] != '.']
		'''
		for tmpDir in os.listdir(dirPath):
			if tmpDir[0] != '.':
				result.append(dirPath + '/' + tmpDir)
		'''
		return result

#######################################################################

## methods for trimming needles strings in '.prj' and '.trj' data ################

	def processData(self, textList):
		return self.removeVECTOR_SPACE(self.removeNoneLine(self.removeCRLF(textList)))

	def removeCRLF(self, textList):
		resultList = []
		crlfPattern = re.compile('\r\n')
		while '\r\n' in textList : textList.remove('\r\n')
		while ' ' in textList : textList.remove(' ')
		for line in textList:
			resultList.append(crlfPattern.sub('', line))
		return resultList

	def removeNoneLine(self, textList):
		while textList.count(' ') > 0: textList.remove(' ')
		return textList

	def removeVECTOR_SPACE(self, textList):
		resultList = []
		topSpacePattern = re.compile(self.TOP_SPACE_PATTERN)
		endSpacePattern = re.compile(self.END_SPACE_PATTERN)
		spacePattern = re.compile(self.VECTOR_SPACE_PATTERN)
		for line in textList:
			line = topSpacePattern.sub('', line)
			line = spacePattern.sub(',', line)
			line = endSpacePattern.sub('', line)
			resultList.append(line)
		return resultList

###################################################################################

## methods for utilities ##########################################################
	def getID(self, fileName, flag = True):
		result = []
		# if flag == true then result's 1st element is Time of data
		if flag:
			time = fileName[10:16]
			time = time[:2] + ':' + time[2:4] + ':' + time[4:]
			result.append(time)
		result.append(fileName[0])
		result.append(fileName[2:4])
		result.append(fileName[5:7])
		result.append(fileName[8])
		return result

	def typeChecker(self, line):
		attrNames = self.getGeneralAttrName()
		# flag 1's data(attribution) is exported to GeneralAttr.csv
		if line in attrNames:
			flag = 1
			return flag
		# flag 2's data is exported to ImpactInfo.csv
		elif re.search(self.IPOTHER_PATTERN, line) != None:
			flag = 2
			return flag
		# flag 3's data is exported to ImpactVactor.csv
		elif re.search(self.IBP_PATTERN, line) != None:
			flag = 3
			return flag
		# flag 4's data is exported to BallVector.csv
		elif re.search(self.AMAT_PATTERN, line) != None:
			flag = 4
			return flag
		elif re.search(self.BALLINFO_PATTERN, line) != None:
			flag = 5
			return flag
		else:
			flag = 0
			return flag

	def getGeneralAttrName(self):
		attr = []
		attr.append('<ParticipantServer>')
		attr.append('<ParticipantReceiver>')
		attr.append('<Server>')
		attr.append('<Receiver>')
		attr.append('<Playerat+veX>')
		attr.append('<DrillType>')
		attr.append('<ServeClassification>')
		attr.append('<Stats>')
		attr.append('<Score(Raw)>')
		attr.append('<Score(Normal)>')
		attr.append('<Scorer>')
		attr.append('<Winner>')
		attr.append('<BigPoint>')
		attr.append('<TimeCodeStartTime>')
		attr.append('<TimeCodeStartTimeHH:MM:SS:FF>')
		attr.append('<NumArcs>')
		attr.append('<ZeroTime>')
		attr.append('<Scoreboard1>')
		attr.append('<Scoreboard2>')
		attr.append('<MaxNumSets>')
		attr.append('<End>')
		return attr

	def writeFile(self, exportList, fileName):
		tmpFile = open(fileName, 'w')
		csvWriter = csv.writer(tmpFile)
		csvWriter.writerows(exportList)
		tmpFile.close()

#################################################################################
