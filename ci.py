#encoding:utf-8

import sys
import requests
from jira import JIRA


ORGAN_NAME = "kentzzhang"
REPO_NAME = "swift-CI-Test"
COMMIT_ID = "d95cc72223f3ecc5a5d926be2ba357404f27bf1e"
GIT_COMMIT_URL = "https://api.github.com/repos/{0}/{1}/git/commits/{2}".format(ORGAN_NAME, REPO_NAME, COMMIT_ID)


JIRA_SERVER = {"server":"https://misfit.jira.com"}
JIRA_AUTH = ("kentz", "1qaz2wsx")


if __name__ == "__main__":
	if not len(sys.argv) == 4:
		print "Usage: python ci.py [username] [repo name] [commit id]"
	else:
		ORGAN_NAME = sys.argv[1]
		REPO_NAME = sys.argv[2]
		COMMIT_ID = sys.argv[3]
		GIT_COMMIT_URL = "https://api.github.com/repos/{0}/{1}/git/commits/{2}".format(ORGAN_NAME, REPO_NAME, COMMIT_ID)
		#print GIT_COMMIT_URL

		#commit_message = requests.get(GIT_COMMIT_URL).json()["message"]
		#print commit_message

		# COMMIT_MESSAGE contains:
		# 1.issueid=****
		# 2.type=CR, values: CR(default value), SCR
		# 3.msg=****
		# -----------------------
		# issue_id=TP-5
		# msg=testcomment is fine. Let's go
		# -----------------------
		issue_id = "TP-8"
		jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
		issue = jira.issue(issue_id)
		# ISSUE STATUS
		print issue.id
		print issue.key
		print issue.fields.status
		print issue.fields.progress
		jira.add_comment(issue_id, "CUSTOM COMMENT !!!!")

		# Transition Opt
		# transitions = jira.transitions(issue)
		# print [(t['id'], t['name']) for t in transitions] 
		# jira.transition_issue(issue, '11')


		# 1. we can change the status of the JIRA before the build.


		# POST-COMMIT
		# 0.upload the build app(.apk or .ipa) file to HockeyApp
		# 1.Execute the BDD cases  
		# --> Travis can do this with test command Or we can do it in this file. But we need to revoke the JIRA API to change the fileds after bdd tests.
		# 2.Execute the Device Tests  
		# --> Test Report Url + Test Result
		# 3.UI Check  
		# --> Test Report Url + Test Result
		# 
		# 




