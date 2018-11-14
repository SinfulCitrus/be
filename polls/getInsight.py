import csv
import codecs
from collections import Counter

from .tests import ppdict
from .utils import parseCSVFile, testCSVFileFormatMatching, isNumber, parseSubmissionTime, index_containing_sub



def getMultipleFilesInfo(file_list):
    """
    Parses any combination of author.csv, review.csv, submission.csv
    """
    parsedResult = {}
    parsedFiles = {}
    u_files = []  # list of uploaded files

    for f_csv in file_list:
        if str(f_csv.name) == 'author.csv':
            u_files.append('author')
            parsedResult['author'], parsedFiles['author.csv'] = getAuthorInfo(f_csv)

        elif str(f_csv.name) == 'score.csv':
            u_files.append('score')
            parsedResult['score'], parsedFiles['score.csv'] = getReviewScoreInfo(f_csv)

        elif str(f_csv.name) == 'review.csv':
            u_files.append('review')
            parsedResult['review'], parsedFiles['review.csv'] = getReviewInfo(f_csv)

        elif str(f_csv.name) == 'submission.csv':
            u_files.append('submission')
            parsedResult['submission'], parsedFiles['submission.csv'] = getSubmissionInfo(f_csv)

        else:
            print("Files dont match a known format.")
            return None

    parseCombined = parseCombinedFiles(parsedFiles)

    parseAll = []
    parseR = []
    for ele in [*parsedResult]:
        parseR.append(parsedResult[ele])

    for ele in parseR:
        parseAll.append(ele['infoData'])

    for ele in [*parseCombined]:
        parseAll.append(parseCombined[ele])

    name = ''
    if 'author' in u_files and 'review' in u_files and 'submission' in u_files:
        name = 'author_review_submission'
    elif 'author' in u_files and 'review' in u_files and 'submission' not in u_files:
        name = 'author_review'
    elif 'author' in u_files and 'review' not in u_files and 'submission' in u_files:
        name = 'author_submission'
    elif 'author' not in u_files and 'review' in u_files and 'submission' in u_files:
        name = 'review_submission'

    dict_result = {'infoType': name, 'infoData': [ele for ele in parseAll]}
    ppdict(dict_result)

    return dict_result


def parseCombinedFiles(parsedFiles):
    parsedResult = {}

    # visualisations for different combinations of files
    if 'author.csv' in parsedFiles and 'submission.csv' in parsedFiles:

        authorList = []
        submissionList = []

        for authorInfo in parsedFiles['author.csv']:
            authorList.append({'collaborators': authorInfo[0], 'organisations': authorInfo[5]})

        for submissionInfo in parsedFiles['submission.csv']:
            submissionList.append({'submission': submissionInfo[0], 'title': submissionInfo[3], 'acc/rej': submissionInfo[9]})

        # submissions with most collaborators / authors
        collaborators = [ele['collaborators'] for ele in authorList if ele]
        topCollaborators = Counter(collaborators).most_common(10)
        parsedResult['topCollaborators'] = {
            'labels': [submissionList[int(ele[0])]['title'] for ele in topCollaborators],
            'data': [ele[1] for ele in topCollaborators]}

        # organisations with most submission with highest accepted : rejected ratios
        organisations = []
        for i, ele in enumerate(authorList):
            organisations.append([i,ele['organisations']])

        topOrganisations = Counter([ele[1] for ele in organisations]).most_common(10)
        indOrg = {}
        for org in topOrganisations:
            indOrg[org[0]] = [ele[0] for ele in organisations if ele[1] == org[0]]

        orgRatios = []
        for ele in [*indOrg]:
            acc = 0
            rej = 0
            for inx in indOrg[ele]:
                if submissionList[index_containing_sub(submissionList,inx)]['acc/rej'] == 'reject':
                    rej+=1
                else:
                    acc+=1
            orgRatios.append([ele,acc,rej])

        orgRatiosAdj = []
        for ele in orgRatios:
            if int(ele[2]) is not 0:
                orgRatiosAdj.append([ele[0],ele[1]/ele[2]])
            else:
                orgRatiosAdj.append([ele[0],ele[1]])

        parsedResult['topAcceptReject'] = {'labels': [ele[0] for ele in orgRatiosAdj], 'data': [ele[1] for ele in orgRatiosAdj]}

    if 'author.csv' in parsedFiles and 'review.csv' in parsedFiles:

        authorList = []
        reviewList = []

        # most collaborators / authors vs review scores
        for authorInfo in parsedFiles['author.csv']:
            authorList.append({'collaborators': authorInfo[0]})

        for reviewInfo in parsedFiles['review.csv']:
            reviewList.append({'submission': reviewInfo[1], 'score': reviewInfo[7]})

        collaborators = [ele['collaborators'] for ele in authorList if ele]
        topCollaborators = Counter(collaborators).most_common(10)

        sums = []
        for sub in [ele[0] for ele in topCollaborators]:
            sums.append(sum([int(ele['score']) for ele in reviewList if ele['submission'] == sub]) / len(
                [int(ele['score']) for ele in reviewList if ele['submission'] == sub]))

        parsedResult['reviewCollaborators'] = {'labels': [ele[0] for ele in topCollaborators],
                                               'data': [ele for ele in sums]}

    if 'submission.csv' in parsedFiles and 'review.csv' in parsedFiles:

        submissionList = []
        reviewList = []

        # least reviewed submissions
        for reviewInfo in parsedFiles['review.csv']:
            reviewList.append({'submission': reviewInfo[1]})

        for submissionInfo in parsedFiles['submission.csv']:
            submissionList.append({'title': submissionInfo[3]})

        reviewSub = [ele['submission'] for ele in reviewList if ele]
        leastReviewSub = Counter(reviewSub).most_common()[:-11:-1]  # format for least common n results = [:-n-1:-1]
        parsedResult['leastCommonReviews'] = {
            'labels': [submissionList[int(ele[0])]['title'] for ele in leastReviewSub if ele],
            'data': [ele[1] for ele in leastReviewSub]}

    return parsedResult


def getAuthorInfo(inputFile):
    """
    author.csv: header row, author names with affiliations, countries, emails
    data format:
    submission ID | f name | s name | email | country | affiliation | page | person ID | corresponding?
    """
    parsedResult = {}

    lines = parseCSVFile(inputFile)[1:]
    lines = [ele for ele in lines if ele]

    authorList = []
    for authorInfo in lines:
        # authorInfo = line.replace("\"", "").split(",")
        # print authorInfo
        authorList.append(
            {'name': authorInfo[1] + " " + authorInfo[2], 'country': authorInfo[4], 'affiliation': authorInfo[5]})

    authors = [ele['name'] for ele in authorList if
               ele]  # adding in the if ele in case of empty strings; same applies below
    topAuthors = Counter(authors).most_common(10)
    parsedResult['topAuthors'] = {'labels': [ele[0] for ele in topAuthors], 'data': [ele[1] for ele in topAuthors]}

    countries = [ele['country'] for ele in authorList if ele]
    topCountries = Counter(countries).most_common(10)
    parsedResult['topCountries'] = {'labels': [ele[0] for ele in topCountries],
                                    'data': [ele[1] for ele in topCountries]}

    countries_set = set(countries)
    parsedResult['avgCountry'] = len(authorList) / len(countries_set)

    affiliations = [ele['affiliation'] for ele in authorList if ele]
    topAffiliations = Counter(affiliations).most_common(10)
    parsedResult['topAffiliations'] = {'labels': [ele[0] for ele in topAffiliations],
                                       'data': [ele[1] for ele in topAffiliations]}

    affil_set = set(affiliations)
    parsedResult['avgAffiliation'] = len(authorList) / len(affil_set)

    dict_result = {'infoType': 'author', 'infoData': parsedResult}
    ppdict(dict_result)

    return dict_result, lines


def getReviewScoreInfo(inputFile):
    """
    review_score.csv
    data format:
    review ID | field ID | score
    File has header

    e.g. 1,1,3 - score (can be negative)
         1,2,5 - confidence
         1,3,no - recommended
    """
    parsedResult = {}
    lines = parseCSVFile(inputFile)[1:]
    lines = [ele for ele in lines if ele]
    scores = []
    confidences = []
    isRecommended = []

    scores = [int(line[2]) for line in lines if int(line[1]) == 1]
    confidences = [int(line[2]) for line in lines if int(line[1]) == 2]
    isRecommended = [str(line[2]).replace("\r", "") for line in lines if int(line[1]) == 3]

    parsedResult['yesPercentage'] = float(isRecommended.count('yes')) / len(isRecommended)
    parsedResult['meanScore'] = sum(scores) / float(len(scores))
    parsedResult['meanConfidence'] = sum(confidences) / float(len(confidences))
    parsedResult['totalReview'] = len(confidences)

    dict_result = {'infoType': 'reviewScore', 'infoData': parsedResult}
    ppdict(dict_result)

    return dict_result, lines


def getReviewInfo(inputFile):
    """
    review.csv
    data format:
    review ID | paper ID? | reviewer ID | reviewer name | unknown | text | scores | overall score | unknown | unknown | unknown | unknown | date | time | recommend?
    File has NO header

    score calculation principles:
    Weighted Average of the scores, using reviewer's confidence as the weights

    recommended principles:
    Yes: 1; No: 0; weighted average of the 1 and 0's, also using reviewer's confidence as the weights
    """

    parsedResult = {}
    lines = parseCSVFile(inputFile)
    lines = [ele for ele in lines if ele]
    evaluation = [str(line[6]).replace("\r", "") for line in lines]
    submissionIDs = set([str(line[1]) for line in lines])

    topReviewers = Counter([ele[3] for ele in lines if ele]).most_common(10)

    scoreList = []
    recommendList = []
    confidenceList = []

    submissionIDReviewMap = {}

    # Idea: from -3 to 3 (min to max scores possible), every 0.25 will be a gap
    scoreDistributionCounts = [0] * int((3 + 3) / 0.25)
    recommendDistributionCounts = [0] * int((1 - 0) / 0.1)

    scoreDistributionLabels = [" ~ "] * len(scoreDistributionCounts)
    recommendDistributionLabels = [" ~ "] * len(recommendDistributionCounts)

    for index, col in enumerate(scoreDistributionCounts):
        scoreDistributionLabels[index] = str(-3 + 0.25 * index) + " ~ " + str(-3 + 0.25 * index + 0.25)

    for index, col in enumerate(recommendDistributionCounts):
        recommendDistributionLabels[index] = str(0 + 0.1 * index) + " ~ " + str(0 + 0.1 * index + 0.1)

    for submissionID in submissionIDs:
        reviews = [str(line[6]).replace("\r", "") for line in lines if str(line[1]) == submissionID]
        # print reviews
        confidences = [float(review.split("\n")[1].split(": ")[1]) for review in reviews]
        scores = [float(review.split("\n")[0].split(": ")[1]) for review in reviews]

        confidenceList.append(sum(confidences) / len(confidences))
        # recommends = [1.0 for review in reviews if review.split("\n")[2].split(": ")[1] == "yes" else 0.0]
        try:
            recommends = [1.0 if review.split("\n")[2].split(": ")[1] == "yes" else 0.0 for review in reviews]
        except:
            recommends = [0.0 for n in range(len(reviews))]
        weightedScore = sum(x * y for x, y in zip(scores, confidences)) / sum(confidences)
        weightedRecommend = sum(x * y for x, y in zip(recommends, confidences)) / sum(confidences)

        scoreColumn = min(int((weightedScore + 3) / 0.25), 23)
        recommendColumn = min(int((weightedRecommend) / 0.1), 9)
        scoreDistributionCounts[scoreColumn] += 1
        recommendDistributionCounts[recommendColumn] += 1
        submissionIDReviewMap[submissionID] = {'score': weightedScore, 'recommend': weightedRecommend}
        scoreList.append(weightedScore)
        recommendList.append(weightedRecommend)

    parsedResult['topReviewers'] = {'labels': [ele[0] for ele in topReviewers], 'data': [ele[1] for ele in topReviewers]}
    parsedResult['IDReviewMap'] = submissionIDReviewMap
    parsedResult['scoreList'] = scoreList
    parsedResult['meanScore'] = sum(scoreList) / len(scoreList)
    parsedResult['meanRecommend'] = sum(recommendList) / len(recommendList)
    parsedResult['meanConfidence'] = sum(confidenceList) / len(confidenceList)
    parsedResult['recommendList'] = recommendList
    parsedResult['scoreDistribution'] = {'labels': scoreDistributionLabels, 'counts': scoreDistributionCounts}
    parsedResult['recommendDistribution'] = {'labels': recommendDistributionLabels,
                                             'counts': recommendDistributionCounts}

    dict_result = {'infoType': 'review', 'infoData': parsedResult}
    ppdict(dict_result)

    return dict_result, lines


def getSubmissionInfo(inputFile):
    """
    submission.csv
    data format:
    submission ID | track ID | track name | title | authors | submit time | last update time | form fields | keywords | decision | notified | reviews sent | abstract
    File has header
    """
    parsedResult = {}
    lines = parseCSVFile(inputFile)[1:]
    lines = [ele for ele in lines if ele]
    acceptedSubmission = [line for line in lines if str(line[9]) == 'accept']
    rejectedSubmission = [line for line in lines if str(line[9]) == 'reject']

    acceptanceRate = float(len(acceptedSubmission)) / len(lines)

    informedRate = sum([1 for ele in lines if ele[10] == 'yes'])/len(lines)

    submissionTimes = [parseSubmissionTime(str(ele[5])) for ele in lines]
    lastEditTimes = [parseSubmissionTime(str(ele[6])) for ele in lines]
    submissionTimes = Counter(submissionTimes)
    lastEditTimes = Counter(lastEditTimes)
    timeStamps = sorted([k for k in submissionTimes])
    lastEditStamps = sorted([k for k in lastEditTimes])
    submittedNumber = [0 for n in range(len(timeStamps))]
    lastEditNumber = [0 for n in range(len(lastEditStamps))]
    timeSeries = []
    lastEditSeries = []
    for index, timeStamp in enumerate(timeStamps):
        if index == 0:
            submittedNumber[index] = submissionTimes[timeStamp]
        else:
            submittedNumber[index] = submissionTimes[timeStamp] + submittedNumber[index - 1]

        timeSeries.append({'x': timeStamp, 'y': submittedNumber[index]})

    for index, lastEditStamp in enumerate(lastEditStamps):
        if index == 0:
            lastEditNumber[index] = lastEditTimes[lastEditStamp]
        else:
            lastEditNumber[index] = lastEditTimes[lastEditStamp] + lastEditNumber[index - 1]

        lastEditSeries.append({'x': lastEditStamp, 'y': lastEditNumber[index]})

    # timeSeries = {'time': timeStamps, 'number': submittedNumber}
    # lastEditSeries = {'time': lastEditStamps, 'number': lastEditNumber}

    acceptedKeywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in acceptedSubmission]
    acceptedKeywords = [ele for item in acceptedKeywords for ele in item]
    acceptedKeywordMap = {k: v for k, v in Counter(acceptedKeywords).items()}
    acceptedKeywordList = [[ele[0], ele[1]] for ele in Counter(acceptedKeywords).most_common(20)]

    rejectedKeywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in rejectedSubmission]
    rejectedKeywords = [ele for item in rejectedKeywords for ele in item]
    rejectedKeywordMap = {k: v for k, v in Counter(rejectedKeywords).items()}
    rejectedKeywordList = [[ele[0], ele[1]] for ele in Counter(rejectedKeywords).most_common(20)]

    allKeywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in lines]
    allKeywords = [ele for item in allKeywords for ele in item]
    allKeywordMap = {k: v for k, v in Counter(allKeywords).items()}
    allKeywordList = [[ele[0], ele[1]] for ele in Counter(allKeywords).most_common(20)]

    tracks = set([str(ele[2]) for ele in lines])
    paperGroupsByTrack = {track: [line for line in lines if str(line[2]) == track] for track in tracks}
    keywordsGroupByTrack = {}
    acceptanceRateByTrack = {}
    comparableAcceptanceRate = {}
    topAuthorsByTrack = {}

    # Obtained from the JCDL.org website: past conferences
    comparableAcceptanceRate['year'] = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
    comparableAcceptanceRate['Full Papers'] = [0.29, 0.28, 0.27, 0.29, 0.29, 0.30, 0.29, 0.30]
    comparableAcceptanceRate['Short Papers'] = [0.29, 0.37, 0.31, 0.31, 0.32, 0.50, 0.35, 0.32]
    for track, papers in paperGroupsByTrack.items():
        keywords = [str(ele[8]).lower().replace("\r", "").split("\n") for ele in papers]
        keywords = [ele for item in keywords for ele in item]
        # keywordMap = {k : v for k, v in Counter(keywords).iteritems()}
        keywordMap = [[ele[0], ele[1]] for ele in Counter(keywords).most_common(20)]
        keywordsGroupByTrack[track] = keywordMap

        acceptedPapersPerTrack = [ele for ele in papers if str(ele[9]) == 'accept']
        acceptanceRateByTrack[track] = float(len(acceptedPapersPerTrack)) / len(papers)

        acceptedPapersThisTrack = [paper for paper in papers if str(paper[9]) == 'accept']
        acceptedAuthorsThisTrack = [str(ele[4]).replace(" and ", ", ").split(", ") for ele in acceptedPapersThisTrack]
        acceptedAuthorsThisTrack = [ele for item in acceptedAuthorsThisTrack for ele in item]
        topAcceptedAuthorsThisTrack = Counter(acceptedAuthorsThisTrack).most_common(10)
        topAuthorsByTrack[track] = {'names': [ele[0] for ele in topAcceptedAuthorsThisTrack],
                                    'counts': [ele[1] for ele in topAcceptedAuthorsThisTrack]}

        if track == "Full Papers" or track == "Short Papers":
            comparableAcceptanceRate[track].append(float(len(acceptedPapersPerTrack)) / len(papers))

    acceptedAuthors = [str(ele[4]).replace(" and ", ", ").split(", ") for ele in acceptedSubmission]
    acceptedAuthors = [ele for item in acceptedAuthors for ele in item]
    topAcceptedAuthors = Counter(acceptedAuthors).most_common(10)
    topAcceptedAuthorsMap = {'names': [ele[0] for ele in topAcceptedAuthors],
                             'counts': [ele[1] for ele in topAcceptedAuthors]}
    # topAcceptedAuthors = {ele[0] : ele[1] for ele in Counter(acceptedAuthors).most_common(10)}

    parsedResult['informedRate'] = informedRate
    parsedResult['acceptanceRate'] = acceptanceRate
    parsedResult['overallKeywordMap'] = allKeywordMap
    parsedResult['overallKeywordList'] = allKeywordList
    parsedResult['acceptedKeywordMap'] = acceptedKeywordMap
    parsedResult['acceptedKeywordList'] = acceptedKeywordList
    parsedResult['rejectedKeywordMap'] = rejectedKeywordMap
    parsedResult['rejectedKeywordList'] = rejectedKeywordList
    parsedResult['keywordsByTrack'] = keywordsGroupByTrack
    parsedResult['acceptanceRateByTrack'] = acceptanceRateByTrack
    parsedResult['topAcceptedAuthors'] = topAcceptedAuthorsMap
    parsedResult['topAuthorsByTrack'] = topAuthorsByTrack
    parsedResult['timeSeries'] = timeSeries
    parsedResult['lastEditSeries'] = lastEditSeries
    parsedResult['comparableAcceptanceRate'] = comparableAcceptanceRate

    dict_result = {'infoType': 'submission', 'infoData': parsedResult}
    ppdict(dict_result)

    return dict_result, lines


if __name__ == "__main__":
    # parseCSVFile(fileName)
    print("getInsight.main")
