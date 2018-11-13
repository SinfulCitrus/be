# -*- coding: utf-8 -*-


from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

import json

from .utils import parseCSVFileFromDjangoFile, isNumber, returnTestChartData
from .getInsight import getReviewScoreInfo, getAuthorInfo, getReviewInfo, getSubmissionInfo, getMultipleFilesInfo

# Create your views here.
# Note: a view is a func taking the HTTP request and returns sth accordingly

def index(request):
	return HttpResponse("Hello, world. You're at the polls index.")

def test(request):
	return HttpResponse("<h1>This is the very first HTTP request!</h1>")

# Note: csr: cross site request, adding this to enable request from localhost
@csrf_exempt
def uploadCSV(request):
	print("Inside the upload function")

	# handling a single file, original code
	if len(request.FILES.getlist('file')) == 1:
		csvFile = request.FILES['file']
		fileName = str(csvFile.name)
		rowContent = ""

		if "author.csv" in fileName:
			rowContent = getAuthorInfo(csvFile)
		elif "score.csv" in fileName:
			rowContent = getReviewScoreInfo(csvFile)
		elif "review.csv" in fileName:
			rowContent = getReviewInfo(csvFile)
		elif "submission.csv" in fileName:
			rowContent = getSubmissionInfo(csvFile)
		else:
			rowContent = returnTestChartData(csvFile)

		if request.POST:
	# current problem: request from axios not recognized as POST
			# csvFile = request.FILES['file']
			print("Now we got the csv file")
			
		res = HttpResponse(json.dumps(rowContent[0]))
		return res
		# return HttpResponse("Got the CSV file.")

	# handling multiple files
	elif len(request.FILES.getlist('file')) > 1:
		rowContent = ""
		
		#print request.FILES.getlist('file')
		
		rowContent = getMultipleFilesInfo(request.FILES.getlist('file'))
		res = HttpResponse(json.dumps(rowContent))
		return res

	else:
		print("Not found the file!")
		return HttpResponseNotFound('Page not found for CSV')