#encoding:utf-8
import sys
import requests
import argparse
import time
from jira import JIRA

JIRA_SERVER = {"server":"https://misfit.jira.com"}
JIRA_AUTH = ("kentz", "1qaz2wsx")

def load_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--username", type=str, default="kentzzhang")
	parser.add_argument("-r", "--reponame", type=str, default="swift-CI-Test")
	parser.add_argument("-c", "--commitid", type=str)
	parser.add_argument("-m", "--method")
	parser.add_argument("-s", "--action") # method=change_status, then you need to input the status you want to change to.
	return parser.parse_args()


def change_status(issue_id, action):
	print "Change the Issue: {0} status. Action: {1}".format(issue_id, action)
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)
	transitions = jira.transitions(issue)
	t_dict = {t['name']:t['id'] for t in transitions} 
	print "Optional Action: {0}".format(t_dict)
	jira.transition_issue(issue, t_dict[action])


def parse_cmt(cmt):
	# COMMIT_MESSAGE contains:
	# issueid=TP11
	# rtype=CR, values: CR(default value), SCR
	# msg=****
	# -----------------------
	print "The Commit Commnet are: \n{0}".format(cmt)
	lines = cmt.split("\n")
	issue_id = lines[0][lines[0].index("=")+1:]
	rtype = lines[1][lines[1].index("=")+1:]
	msg = lines[2][lines[2].index("=")+1:]
	return issue_id, rtype, msg


def get_current_issue_status(issue_id):
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)
	status = str(issue.fields.status)
	print "Current Status of the JIRA Issue is : {0}".format(status)
	return status


def test(issue_id):
	#jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	#issue = jira.issue(issue_id)
	#issue.update(customfield_12003="http://google.com")
	#issue.update(customfield_12009={"value":"Failed"})
	bdd_test(issue_id)
	ui_check(issue_id)
	device_test(issue_id)


def test_status(testResult):
	if testResult is None:
		testStatus = TestResult.NT
	else:
		if testResult:
			testStatus = TestResult.Pass
		else:
			testStatus = TestResult.Fail
	return testStatus


# **********************************************
# Specified Test
# **********************************************
def bdd_test(issue_id):
	# CI Test Result
	#text: customfield_12103
	#radio: customfield_12007
	testResult = True
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)

	# After Testing, Set the value to the JIRA
	issue.update(customfield_12103="http://ci.misfit.com/{0}".format(time.time()))
	issue.update(customfield_12007={"value":test_status(testResult)})
	return testResult


def ui_check(issue_id):
	# Only Add the test result url to the field
	# UI Check Status
	#text: customfield_12105
	#radio: customfield_12009
	testResult = True
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)

	# After Testing, Set the value to the JIRA
	issue.update(customfield_12105="http://uicheck.misfit.com/{0}".format(time.time()))
	issue.update(customfield_12009={"value":test_status(testResult)})
	return testResult


def coverage_stat(issue_id):
	return True


def unit_test(issue_id):
	return True


def device_test(issue_id):
	# DT Result Status
	#text: customfield_12104
	#radio: customfield_12008
	testResult = True
	jira = JIRA(options = JIRA_SERVER, basic_auth = JIRA_AUTH)
	issue = jira.issue(issue_id)

	# After Testing, Set the value to the JIRA
	issue.update(customfield_12104="http://dt.misfit.com/{0}".format(time.time()))
	issue.update(customfield_12008={"value":test_status(testResult)})
	return testResult


def reset(issue_id):
	pass

# **********************************************
# Workflow Actions
# **********************************************
def commit_cr(issue_id):
	# In Progress => CR Test Completed
	change_status(issue_id, IssueAction.CommitCr)
	# Begin to test after committing
	crTestResult = bdd_test(issue_id) and ui_check(issue_id) and unit_test(issue_id) and device_test(issue_id)
	if not crTestResult:
		# if there is any fail result, go to the issue fixing status
		fix_cr_issue(issue_id)
	# else branch need to change the status manually


def commit_scr(issue_id):
	# In Progress => SCR Test Completed
	change_status(issue_id, IssueAction.CommitScr)
	# Begin to test after committing
	scrTestResult = bdd_test(issue_id) and ui_check(issue_id) and unit_test(issue_id) and device_test(issue_id)
	if not scrTestResult:
		# if there is any fail result, go to the in progress status
		fail_scr_test(issue_id)
	# else branch need to change the status manually


def start_smoke_test(issue_id):
	# SCR Test Completed => Smoke Testing
	change_status(issue_id, IssueAction.StartSmokeTest)


def commit_smoke(issue_id):
	# Smoke Testing => In Progress
	change_status(issue_id, IssueAction.CommitSmoke)


def fail_scr_test(issue_id):
	# SCR Test Completed => In Progress
	change_status(issue_id, IssueAction.FailScrTest)


def fix_cr_issue(issue_id):
	# CR Test Completed => CR Fixing
	change_status(issue_id, IssueAction.FixCrIssue)


def commit_issue(issue_id):
	# CR Fixing => CR Test Completed
	change_status(issue_id, IssueAction.CommitIssue)
	# Begin to test after committing
	crTestResult = bdd_test(issue_id) and ui_check(issue_id) and unit_test(issue_id) and device_test(issue_id)
	if not crTestResult:
		# if there is any fail result, go to the issue fixing status
		fix_cr_issue(issue_id)
	# else branch need to change the status manually


def pass_cr_test(issue_id):
	# CR Test Completed => In Progress
	change_status(issue_id, IssueAction.PassCrTest)


# Enum of the Issue Action
class IssueAction:
	StartStory = "Start Story"
	CommitScr = "Commit SCR"
	CommitCr = "Commit CR"
	FailScrTest = "Fail SCR Test"
	PassCrTest = "Pass CR Test"
	FixCrIssue = "Fix CR Issue"
	CommitIssue = "Commit Issue"
	StartSmokeTest = "Start Smoke Test"
	CommitSmoke = "Commit Smoke"
	PassSmokeTest = "Pass Smoke Test"


# Enum of the Issue Status
class IssueStatus:
	ToDo = "Open"
	InProgress = "In Progress"
	CrTestCompleted = "CR Test Completed"
	ScrTestCompleted = "SCR Test Completed"
	CrFixing = "CR Fixing"
	SmokeTesting = "Smoke Testing"
	Done = "Done"


# Result of the Testing
class TestResult:
	Pass = "Passed"
	Fail = "Failed"
	NT = "Not Test"


if __name__ == "__main__":
	args = load_args()
	GIT_COMMIT_URL = "https://api.github.com/repos/{0}/{1}/git/commits/{2}".format(args.username, 
																				   args.reponame, 
																				   args.commitid)
	#commit_message = requests.get(GIT_COMMIT_URL).json()["message"]
	commit_message = "issueid=TP-19\nrtype=CR\nmsg=update commit"
	issue_id, rtype, msg = parse_cmt(commit_message)

	#test(issue_id)
	# if the current status is TODO, then change to In Progress
	if get_current_issue_status(issue_id) == IssueStatus.ToDo:
		print "Let's start our story!!"
		change_status(issue_id, IssueAction.StartStory)

	# Change the status of the JIRA issue
	if args.method is not None:
		if args.method == "change_status":
			change_status(issue_id, args.action)
		elif args.method == "reset":
			pass
	else:
		# In Progress
		if get_current_issue_status(issue_id) == IssueStatus.InProgress:
			# SCR Commit
			if rtype.upper() == "SCR":
				commit_scr(issue_id)

			# CR Commit
			elif rtype.upper() == "CR":
				commit_cr(issue_id)


		# CR Fixing
		elif get_current_issue_status(issue_id) == IssueStatus.CrFixing:
			commit_issue(issue_id)